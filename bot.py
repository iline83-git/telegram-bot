import os
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("8383810656:AAFkeiHcpMPAuKN2d7zHY0iub5InEgOCjIc")

# 📦 База данных
conn = sqlite3.connect("habit_bot.db", check_same_thread=False)
cursor = conn.cursor()

# создаём таблицы
cursor.execute("""
CREATE TABLE IF NOT EXISTS habits (
    chat_id INTEGER,
    habit TEXT,
    value INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    chat_id INTEGER,
    date TEXT,
    score INTEGER,
    level TEXT
)
""")

conn.commit()

# привычки
habits_list = [
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

main_menu = ReplyKeyboardMarkup([
    ["📋 Привычки", "📊 Результат"]
], resize_keyboard=True)

def get_keyboard():
    keyboard = []
    for habit, _ in habits_list:
        keyboard.append([habit + " ✅", habit + " ❌"])
    keyboard.append(["🔙 Назад"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# сохранить привычку
def save_habit(chat_id, habit, value):
    cursor.execute("DELETE FROM habits WHERE chat_id=? AND habit=?", (chat_id, habit))
    cursor.execute("INSERT INTO habits VALUES (?, ?, ?)", (chat_id, habit, value))
    conn.commit()

# получить привычки
def get_habits(chat_id):
    cursor.execute("SELECT habit, value FROM habits WHERE chat_id=?", (chat_id,))
    return dict(cursor.fetchall())

# сохранить историю
def save_history(chat_id, score, level):
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO history VALUES (?, ?, ?, ?)", (chat_id, date, score, level))
    conn.commit()

# получить историю
def get_history(chat_id):
    cursor.execute("SELECT date, score, level FROM history WHERE chat_id=? ORDER BY date DESC LIMIT 7", (chat_id,))
    return cursor.fetchall()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Главное меню", reply_markup=main_menu)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if text == "📋 Привычки":
        await update.message.reply_text("Выбери:", reply_markup=get_keyboard())
        return

    if text == "🔙 Назад":
        await update.message.reply_text("Меню", reply_markup=main_menu)
        return

    if text == "📊 Результат":
        habits = get_habits(chat_id)
        total, level = calculate(habits)

        save_history(chat_id, total, level)

        history = get_history(chat_id)
        history_str = "\n".join([f"{d} — {s} ({l})" for d, s, l in history])

        await update.message.reply_text(f"📊 {total} баллов\n{level}\n\n📅 История:\n{history_str}")
        return

    # обработка привычек
    for habit, _ in habits_list:
        if habit in text:
            if "✅" in text:
                save_habit(chat_id, habit, 1)
            elif "❌" in text:
                save_habit(chat_id, habit, 0)

            await update.message.reply_text(f"{habit} сохранено")
            return

def calculate(habits):
    total = 0

    for habit, score in habits_list:
        if habits.get(habit) == 1:
            total += score

    penalties = 0
    if habits.get("🚫 Не есть после 21") == 0:
        penalties += 30
    if habits.get("🏋️ Приседания") == 0:
        penalties += 30
    if habits.get("📖 Книга") == 0:
        penalties += 30

    total -= penalties

    if total >= 100:
        level = "🔥 Идеально"
    elif total >= 70:
        level = "💪 Сильный"
    elif total >= 40:
        level = "👍 Средний"
    elif total >= 0:
        level = "⚠️ Слабый"
    else:
        level = "🚨 Срыв"

    return total, level

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))

app.run_polling()