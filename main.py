from flask import Flask, request, jsonify
from bot_logic import processor
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Обработчик вебхука от Telegram"""
    try:
        # Получаем данные от Telegram
        update_data = request.get_json()
        
        if not update_data:
            logger.warning("Пустой запрос от Telegram")
            return jsonify({"status": "error", "message": "Empty data"}), 400
        
        logger.info(f"Получен вебхук: {update_data}")
        
        # Обрабатываем обновление
        success = processor.process_update(update_data)
        
        if success:
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"status": "error", "message": "Processing failed"}), 500
            
    except Exception as e:
        logger.error(f"Ошибка в вебхуке: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    """Проверка работоспособности сервера"""
    return jsonify({
        "status": "ok",
        "service": "Telegram 1C Bot",
        "endpoints": {
            "webhook": "POST /webhook",
            "health": "GET /"
        }
    })
