from flask import Flask, request, jsonify
import os
import requests
import logging
from knowledge_base import KNOWLEDGE_BASE
from nlp_engine import SemanticEngine

app = Flask(__name__)
# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация семантического движка
semantic_engine = SemanticEngine(KNOWLEDGE_BASE)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    logger.info("Получено обновление: %s", update)

    if 'message' in update and 'text' in update['message']:
        chat_id = update['message']['chat']['id']
        user_text = update['message']['text']

        # Поиск ответа через семантический поиск
        answer = semanticengine.find_best_match(user_text)
        if answer:
            send_message(chat_id, answer)
        else:
            send_message(chat_id, "Извините, я не нашёл ответа на ваш вопрос. Попробуйте уточнить.")
    else:
        logger.info("Не текстовое сообщение: %s", update)

    return jsonify({'status': 'ok'}), 200

def send_message(chat_id: int, text: str):
    """Отправка сообщения через Telegram API"""
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN не задан!")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        headers = {"Content-Type": "application/json; charset=utf-8"}

        response = requests.post(url, json=payload, headers=headers, timeout=5)


        if response.status_code == 200:
            logger.info("Сообщение отправлено успешно: %s", response.json())
        else:
            logger.error("Ошибка API: %d %s", response.status_code, response.text)
    except Exception as e:
        logger.exception("Ошибка отправки сообщения: %s", e)
