from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from nlp_engine import NLPEngine
import logging

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация NLP‑ядра
nlp = NLPEngine()

# ID администратора (ваш Telegram ID, чтобы защитить /learn)
ADMIN_ID = 7918581679  # Замените на свой ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение с клавиатурой."""
    keyboard = [
        [KeyboardButton("Как создать накладную?")],
        [KeyboardButton("Где отчёт о прибыли?")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Здравствуйте! Я бот помощи по 1С.\n"
        "Задайте вопрос или выберите пример ниже.",
        reply_markup=reply_markup
    )

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет новый пример (только для админа)."""
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Эта команда доступна только администратору.")
        return

    text = update.message.text.replace("/learn", "", 1).strip()
    if "|" not in text:
        await update.message.reply_text(
            "Формат: /learn вопрос | ответ\n"
            "Пример: /learn Как обновить 1С? | 1. Сделайте копию базы..."
        )
        return

    question, answer = map(str.strip, text.split("|", 1))
    nlp.add_example(question, answer)
    await update.message.reply_text(f"✅ Пример добавлен:\n\n**Вопрос:** {question}\n**Ответ:** {answer}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения от пользователя."""
    query = update.message.text
    answer = nlp.find_best_answer(query)
    await update.message.reply_text(answer, parse_mode="Markdown")

def main():
    # Укажите токен бота от @BotFather
    TOKEN = "8572890476:AAHVRIrKb_8JuZI_gvjWputPWKNE78AxNvU"


    # Создаём приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("learn", learn))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


if __name__ == '__main__':
    main()
