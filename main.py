from flask import Flask, request, jsonify
from bot import application  # Импортируем application из bot.py
import logging

app = Flask(__name__)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Получаем JSON-обновление от Telegram
    update = request.get_json()
    if not update:
        logger.error("Пустое обновление")
        return jsonify({'status': 'error'}), 400

    # Преобразуем JSON в объект Update и передаём в Application
    from telegram import Update
    from telegram.ext import Dispatcher
    update = Update.de_json(update, application.bot)
    application.process_update(update)  # Обрабатываем обновление

    logger.info("Обновление обработано")
    return jsonify({'status': 'ok'}), 200

@app.route('/')
def health():
    return jsonify({'status': 'ok', 'service': 'Telegram 1C Bot'})

if __name__ == '__main__':
    app.run()

