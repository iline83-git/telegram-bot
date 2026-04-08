from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

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
main_menu = ReplyKeyboardMarkup([
    ["📋 Привычки", "📊 Результат"]
], resize_keyboard=True)

# Клавиатура для привычек
def get_habits_keyboard():
    keyboard = []
    for habit, _ in habits:
        keyboard.append([habit + " ✅", habit + " ❌"])
    keyboard.append(["🔙 Назад"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {"habits": {}, "history": [], "streak": 0, "last_date": None}
    await update.message.reply_text("🚀 Главное меню", reply_markup=main_menu)

# Обработка кнопок
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

    # отметка привычки
    for habit, _ in habits:
        if habit in text:
            if "✅" in text:
                data["habits"][habit] = True
            elif "❌" in text:
                data["habits"][habit] = False
            await update.message.reply_text(f"{habit}: сохранено ✅")
            return

# Подсчёт баллов
def calculate(habits_data):
    total = 0
    for habit, score in habits:
        if habits_data.get(habit):
            total += score

    penalties = 0
    if habits_data.get("🚫 Не есть после 21") == False:
        penalties += 30
    if habits_data.get("🏋️ Приседания") == False:
        penalties += 30
    if habits_data.get("📖 Книга") == False:
        penalties += 30

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

# Прогресс-бар и streak
def get_progress(data):
    total, level = calculate(data["habits"])
    max_score = sum([score for _, score in habits])
    filled = int(total / max_score * 10)
    bar = "█" * filled + "░" * (10 - filled)

    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # обновление streak
    if data["last_date"] == yesterday and total >= 70:
        data["streak"] += 1
    elif total >= 70:
        data["streak"] = 1
    else:
        data["streak"] = 0

    data["last_date"] = today

    # сохраняем историю
    data["history"].append({
        "date": today,
        "score": total,
        "level": level
    })

    progress_str = f"{bar} {total}/{max_score} баллов"
    return f"📊 {level}", progress_str, data["streak"]

# Создание и запуск бота
app = ApplicationBuilder().token("8383810656:AAFkeiHcpMPAuKN2d7zHY0iub5InEgOCjIc").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))
app.run_polling()
