from flask import Flask, request, jsonify
from telegram import Update

# Импортируем ГЛОБАЛЬНЫЙ объект application из bot.py
from bot import application

app = Flask(__name__)

@app.route(f"/{application.bot.token}", methods=["POST"])
def webhook():
    """Обрабатывает вебхуки от Telegram."""
    json_string = request.get_data().decode("utf-8")
    update = Update.de_json(json_string, application.bot)
    application.process_update(update)
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Telegram 1C Bot"})

