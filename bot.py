import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from apscheduler.schedulers.background import BackgroundScheduler

from db import cursor, conn, remove_channel, get_user_channels
from youtube import resolve_channel, get_channel_info
from scheduler import check_updates

TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()
scheduler = BackgroundScheduler()
scheduler.add_job(check_updates, "interval", minutes=5, args=[app.bot])
scheduler.start()

states = {}

# Главное меню
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить канал", callback_data="add")],
        [InlineKeyboardButton("📋 Мои каналы", callback_data="list")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бля ну ты же разберешься с двумя кнопка в боте",
        reply_markup=menu()
    )

# Обработка нажатий на кнопки
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "add":
        states[uid] = "add"
        await q.message.reply_text("Пришли ссылку на YouTube-канал")

    elif q.data == "list":
        rows = get_user_channels(uid)
        if not rows:
            await q.message.reply_text("📭 У тебя пока нет каналов")
            return

        text = "📺 Твои каналы:\n\n"
        for i, (name, cid) in enumerate(rows, 1):
            text += f"{i}️⃣ {name}\n"

        await q.message.reply_text(text)

    elif q.data.startswith("del:"):
        cid = q.data.split(":")[1]
        remove_channel(uid, cid)
        await q.message.reply_text("❌ Канал удалён")

# Обработка сообщений
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    if states.get(uid) == "add":
        cid = resolve_channel(text)
        if not cid:
            await update.message.reply_text("❌ Не удалось определить канал")
            return

        name, last = get_channel_info(cid)
        cursor.execute(
            "INSERT OR IGNORE INTO channels VALUES (?, ?, ?)",
            (cid, name, last)
        )
        cursor.execute(
            "INSERT OR IGNORE INTO subscriptions VALUES (?, ?)",
            (uid, cid)
        )
        conn.commit()

        states.pop(uid)

        # inline-кнопки после добавления
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить ещё канал", callback_data="add")],
            [InlineKeyboardButton("❌ Удалить этот канал", callback_data=f"del:{cid}")]
        ])
        await update.message.reply_text(
            f"✅ Канал добавлен: {name}",
            reply_markup=kb
        )

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

app.run_polling()
