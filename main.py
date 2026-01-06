import os
import logging
import json
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКА ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")

app = Flask(__name__)

# Глобальное приложение, которое будет инициализировано при первом запросе
application = None

# --- ЭТАП 1: ЛОКАЛЬНАЯ БАЗА ЗНАНИЙ ---
class LocalKnowledgeBase:
    def __init__(self, file_path="knowledge_base.json"):
        self.qa_pairs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.qa_pairs = json.load(f)
        except FileNotFoundError:
            pass

    def find_answer(self, user_question: str) -> str | None:
        user_q = user_question.lower()
        for qa in self.qa_pairs:
            db_q = qa.get("question", "").lower()
            if db_q in user_q or user_q in db_q:
                return qa.get("answer")
        return None

knowledge_base = LocalKnowledgeBase()

# --- ЭТАП 2: ЗАГЛУШКА ПОИСКА В ДОКУМЕНТАЦИИ ---
def search_in_1c_docs(question: str) -> str:
    return f"📘 По документации 1С:\nПо запросу '{question}' я пока ничего не нашел. Нужно настроить поиск."

# --- ОБРАБОТЧИКИ ДЛЯ ТЕЛЕГРАМ-БОТА ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-помощник по 1С. Задайте вопрос — я поищу ответ в базе знаний, а затем в документации.\n\n"
        "Попробуйте спросить: 'Как создать накладную?' или 'Где отчет о прибылях?'"
    )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logging.info(f"Обрабатываем сообщение: {user_text}")

    answer = knowledge_base.find_answer(user_text)
    
    if not answer:
        answer = search_in_1c_docs(user_text)
    
    await update.message.reply_text(answer)

def get_application():
    """Создает, настраивает и возвращает инициализированное приложение."""
    global application
    if application is None:
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
        # Инициализируем
        application.initialize()
    return application

# --- FLASK ЭНДПОИНТЫ ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Точка входа для вебхука от Telegram"""
    try:
        update_data = request.get_json()
        if not update_data:
            return jsonify({"status": "error", "message": "Нет данных"}), 400

        logging.info(f"Получен вебхук: {update_data}")

        # Получаем инициализированное приложение
        app_inst = get_application()
        update = Update.de_json(update_data, app_inst.bot)

        async def process_update_async():
            await app_inst.process_update(update)
        
        asyncio.run(process_update_async())

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logging.error(f"Ошибка в /webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "Telegram 1C Bot"})
