import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("8383810656:AAFkeiHcpMPAuKN2d7zHY0iub5InEgOCjIc")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # для webhook на сервере, если нужен

# Хранение данных пользователей
user_data = {}

# Список привычек и баллы
habits = [
    ("💧 Вода утром", 10),
    ("🌬 Глубокое дыхание", 10),
    ("🧘 Лоуэн", 10),
    ("✍️ Утренние страницы", 20),
    ("🏋️ Приседания", 20),
    ("📖 Книга", 20),
    ("🚫 Не есть после 21", 20),
    ("🌬 Стрельникова", 10),
    ("🧘 Чакровое дыхание", 10)
]

# Главное меню
main_menu = ReplyKeyboardMarkup([["📋 Привычки", "📊 Результат"]], resize_keyboard=True)

def get_habits_keyboard():
    keyboard = [[habit + " ✅", habit + " ❌"] for habit, _ in habits]
    keyboard.append(["🔙 Назад"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {"habits": {}, "history": [], "streak": 0, "last_date": None}
    await update.message.reply_text("🚀 Главное меню", reply_markup=main_menu)

# --- Обработка кнопок ---
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    data = user_data.setdefault(chat_id, {"habits": {}, "history": [], "streak": 0, "last_date": None})

    if text == "📋 Привычки":
        await update.message.reply_text("Выбери привычку:", reply_markup=get_habits_keyboard())
        return
    if text == "🔙 Назад":
        await update.message.reply_text("Главное меню", reply_markup=main_menu)
        return
    if text == "📊 Результат":
        result, progress, streak = get_progress(data)
        history_str = "\n".join([f"{d['date']}: {d['score']} баллов — {d['level']}" for d in data["history"][-7:]])
        await update.message.reply_text(
            f"{result}\n\n📈 Прогресс сегодня:\n{progress}\n🔥 Серия дней подряд: {streak}\n\n📅 Последние дни:\n{history_str if history_str else 'Нет данных'}",
            reply_markup=main_menu
        )
        return
    for habit, _ in habits:
        if habit in text:
            if "✅" in text:
                data["habits"][habit] = True
            elif "❌" in text:
                data["habits"][habit] = False
            await update.message.reply_text(f"{habit}: сохранено ✅")
            return

# --- Подсчёт баллов ---
def calculate(habits_data):
    total = sum(score for habit, score in habits if habits_data.get(habit))
    penalties = sum(
        30 for habit in ["🚫 Не есть после 21", "🏋️ Приседания", "📖 Книга"]
        if habits_data.get(habit) == False
    )
    total -= penalties
    if total >= 100:
        level = "🔥 Идеально"
    elif total >= 70:
        level = "💪 Сильный день"
    elif total >= 40:
        level = "👍 Средний день"
    elif total >= 0:
        level = "⚠️ Слабый день"
    else:
        level = "🚨 Срыв"
    return total, level

# --- Прогресс-бар и streak ---
def get_progress(data):
    total, level = calculate(data["habits"])
    max_score = sum([score for _, score in habits])
    filled = int(total / max_score * 10)
    bar = "█" * filled + "░" * (10 - filled)

    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if data["last_date"] == yesterday and total >= 70:
        data["streak"] += 1
    elif total >= 70:
        data["streak"] = 1
    else:
        data["streak"] = 0

    data["last_date"] = today
    data["history"].append({"date": today, "score": total, "level": level})

    return f"📊 {level}", f"{bar} {total}/{max_score} баллов", data["streak"]

# --- Создание и запуск бота ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

# --- Запуск через polling для GitHub или локально ---
if __name__ == "__main__":
    app.run_polling()
