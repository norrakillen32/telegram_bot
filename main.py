from flask import Flask, request, jsonify
from bot import application  # Импортируем Application из bot.py
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Получаем JSON-обновление от Telegram
        update_json = request.get_json()
        if not update_json:
            logger.error("Пустое обновление")
            return jsonify({'status': 'error', 'message': 'Empty update'}), 400

        # Преобразуем JSON в объект Update
        from telegram import Update
        update = Update.de_json(update_json, application.bot)

        # Передаём обновление в Application (без Dispatcher!)
        application.process_update(update)

        logger.info("Обновление обработано успешно")
        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Telegram 1C Bot'})

