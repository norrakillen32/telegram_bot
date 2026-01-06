import os
import logging
import asyncio
from threading import Thread
from queue import Queue
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКА ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("Задайте переменную TELEGRAM_BOT_TOKEN в настройках Vercel!")

# --- ИНИЦИАЛИЗАЦИЯ FLASK И БОТА ---
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
# Создаем асинхронное приложение PTB
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Очередь для обновлений от Telegram
update_queue = Queue()

# --- ЭТАП 1: ЛОКАЛЬНАЯ БАЗА ЗНАНИЙ (JSON) ---
import json
class LocalKnowledgeBase:
    def __init__(self, file_path="knowledge_base.json"):
        self.file_path = file_path
        self.qa_pairs = self._load_data()

    def _load_data(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)  # Ожидается [{"question": "...", "answer": "..."}, ...]
        except FileNotFoundError:
            return []

    def find_answer(self, user_question: str) -> str | None:
        user_q_lower = user_question.lower()
        for qa in self.qa_pairs:
            if qa.get("question", "").lower() in user_q_lower or user_q_lower in qa.get("question", "").lower():
                return qa.get("answer")
        return None

# --- ЭТАП 2: ПОИСК В ДОКУМЕНТАЦИИ 1С (ЗАГЛУШКА) ---
class DocSearch1C:
    async def find_in_docs(self, question: str) -> str:
        """
        ВАШ ВЫБОР: Здесь нужно реализовать один из двух путей:
        Вариант А (RAG): Поиск в векторной БД + запрос к локальной LLM (Ollama).
        Вариант Б (HTTP): Запрос к веб-сервису, опубликованному в 1С.
        """
        # Пока возвращаем заглушку
        return f"🔍 Вот что я нашел в документации 1С по запросу '{question}':\n... (реализуйте поиск в классе DocSearch1C) ..."

# --- ИНИЦИАЛИЗАЦИЯ КОМПОНЕНТОВ ---
knowledge_base = LocalKnowledgeBase()
doc_searcher = DocSearch1C()

# --- ОБРАБОТЧИКИ КОМАНД ТЕЛЕГРАМ-БОТА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-помощник по 1С.\n"
        "Задайте вопрос — я поищу ответ в базе знаний, а затем в документации."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text
    logging.info(f"Пользователь спросил: {user_question}")

    # ЭТАП 1: Поиск в локальной базе
    local_answer = knowledge_base.find_answer(user_question)
    if local_answer:
        await update.message.reply_text(local_answer)
        return

    # ЭТАП 2: Поиск в документации 1С
    search_result = await doc_searcher.find_in_docs(user_question)
    await update.message.reply_text(search_result)

# Регистрируем обработчики в приложении PTB
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- ФОНОВЫЙ ПОТОК ДЛЯ ОБРАБОТКИ ОЧЕРЕДИ ---
def run_bot_worker():
    """Запускает бота в бесконечном цикле, обрабатывая очередь."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def worker():
        while True:
            # Ждем обновление из очереди
            update = update_queue.get()
            await application.process_update(update)
            update_queue.task_done()

    loop.run_until_complete(worker())

# Запускаем поток при старте приложения
bot_thread = Thread(target=run_bot_worker, daemon=True)
bot_thread.start()

# --- FLASK ЭНДПОИНТЫ ДЛЯ VERCEL ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """Главная точка входа для вебхука от Telegram."""
    try:
        # 1. Получаем обновление от Telegram
        update_data = request.get_json()
        if not update_data:
            return jsonify({"status": "error", "message": "Empty update"}), 400

        logging.info(f"Получен вебхук: {update_data}")

        # 2. Создаем объект Update для библиотеки python-telegram-bot
        update = Update.de_json(update_data, bot)

        # 3. ПОМЕЩАЕМ ОБНОВЛЕНИЕ В ОЧЕРЕДЬ для фоновой обработки
        update_queue.put(update)

        # 4. Сразу отвечаем Telegram "OK", чтобы он не ждал
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logging.exception(f"Ошибка в /webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    """Проверка здоровья сервера (то, что вы видите в логах)."""
    logging.info("Health check выполнен")
    return jsonify({"status": "ok", "service": "Telegram 1C Bot"})
