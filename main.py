import os
import json
import logging
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# База знаний
def load_knowledge_base():
    try:
        with open('knowledge_base.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# Поиск в базе
def search_local_kb(question, kb):
    q_lower = question.lower()
    for item in kb:
        if q_lower in item.get('question', '').lower():
            return item.get('answer')
    return None

# Заглушка поиска в документации 1С
def search_1c_docs(question):
    # TODO: заменить на реальный поиск
    return f"🔍 По запросу '{question}' в документации 1С ничего не найдено."

# Отправка ответа в Telegram
def send_message(chat_id, text):
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", 
                     json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        return True
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        return False

# Обработчик вебхука
@app.route('/webhook', methods=['POST'])
def webhook_handler():  # Уникальное имя
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"status": "error"}), 400

        message = data['message']
        chat_id = message['chat']['id']
        text = message.get('text', '').strip()

        # Команда /start
        if text == '/start':
            welcome_text = (
                "👋 <b>Привет! Я бот-помощник по 1С</b>\n\n"
                "Задайте вопрос, и я:\n"
                "1️⃣ Сначала поищу в базе знаний\n"
                "2️⃣ Если не найду — поищу в документации 1С\n\n"
                "Примеры вопросов:\n"
                "• Как создать накладную?\n"
                "• Где отчет о прибылях?"
            )
            send_message(chat_id, welcome_text)
            return jsonify({"status": "ok"})

        # Этап 1: Поиск в локальной базе
        kb_data = load_knowledge_base()
        answer = search_local_kb(text, kb_data)

        # Этап 2: Если не нашли - ищем в документации
        if not answer:
            answer = search_1c_docs(text)

        # Отправляем ответ
        send_message(chat_id, answer)
        return jsonify({"status": "ok"})

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return jsonify({"status": "error"}), 500

# Health check
@app.route('/', methods=['GET'])
def health_handler():  # Уникальное имя
    return jsonify({"status": "ok", "service": "1C Bot"})
