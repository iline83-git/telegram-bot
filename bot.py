import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

# Храним ответы пользователя
user_data = {}

questions = [
    "Вода утром? (+/-)",
    "Глубокое дыхание 5 мин? (+/-)",
    "Упражнения Лоуэна? (+/-)",
    "Утренние страницы? (+/-)",
    "30 приседаний? (+/-)",
    "1 глава книги с рефлексией? (+/-)",
    "Не ел после 21:00? (+/-)",
    "Стрельникова? (+/-)",
    "Чакровое дыхание? (+/-)"
]

scores = [10,10,10,20,20,20,20,10,10]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id] = {
        "step": 0,
        "answers": []
    }
    await update.message.reply_text("Начинаем чек-ап 👇")
    await update.message.reply_text(questions[0])

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if chat_id not in user_data:
        await update.message.reply_text("Напиши /start")
        return

    data = user_data[chat_id]

    # сохраняем ответ
    data["answers"].append(text)

    data["step"] += 1

    if data["step"] < len(questions):
        await update.message.reply_text(questions[data["step"]])
    else:
        result = calculate(data["answers"])
        await update.message.reply_text(result)
        del user_data[chat_id]

def calculate(answers):
    total = 0

    # плюсы
    for i, ans in enumerate(answers):
        if ans == "+":
            total += scores[i]

    penalties = 0

    # штрафы
    if answers[6] == "-":  # ел после 21
        penalties += 30

    if answers[4] == "-":  # приседания
        penalties += 30

    if answers[5] == "-":  # книга
        penalties += 30

    total -= penalties

    # уровень
    if total >= 100:
        level = "🔥 Идеально"
    elif total >= 70:
        level = "💪 Сильный день"
    elif total >= 40:
        level = "👍 Средний"
    elif total >= 0:
        level = "⚠️ Слабый"
    else:
        level = "🚨 Срыв"

    return f"Баллы: {total}\nУровень: {level}"

app = ApplicationBuilder().token("8383810656:AAFkeiHcpMPAuKN2d7zHY0iub5InEgOCjIc").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))

app.run_polling()
