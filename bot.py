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

# Состояния пользователя
states = {}

# Главное меню (только список каналов)
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Мои каналы", callback_data="list")]
    ])

# Стартовое сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Скидывай ссылку на канал в чат",
        reply_markup=menu()
    )

# Обработка нажатий кнопок
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    # Показ списка каналов
    if q.data == "list":
        rows = get_user_channels(uid)
        if not rows:
            await q.message.reply_text("📭 У тебя пока нет каналов")
            return

        text = "📺 Твои каналы:\n\n"
        for i, (name, cid) in enumerate(rows, 1):
            text += f"{i}. {name}\n"

        # Кнопка для удаления по номеру
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Удалить канал", callback_data="del_num")]
        ])
        await q.message.reply_text(text, reply_markup=kb)

    # Начало удаления по номеру
    elif q.data == "del_num":
        states[uid] = "del_num"
        await q.message.reply_text("Введи номер канала, который хочешь удалить")

# Обработка сообщений (ссылки и номера для удаления)
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text.strip()

    # ----------------------
    # Добавление нового канала
    # ----------------------
    if text.startswith("https://") or text.startswith("http://"):
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

        await update.message.reply_text(f"✅ Канал добавлен: {name}", reply_markup=menu())

    # ----------------------
    # Удаление по номеру
    # ----------------------
    elif states.get(uid) == "del_num":
        rows = get_user_channels(uid)
        if not rows:
            await update.message.reply_text("📭 У тебя пока нет каналов")
            states.pop(uid, None)
            return

        try:
            num = int(text)
            if num < 1 or num > len(rows):
                raise ValueError
            cid_to_delete = rows[num - 1][1]
            remove_channel(uid, cid_to_delete)
            states.pop(uid, None)

            # Отправляем обновлённый список после удаления
            updated_rows = get_user_channels(uid)
            if not updated_rows:
                await update.message.reply_text("📭 У тебя пока нет каналов", reply_markup=menu())
                return

            updated_text = "📺 Твои каналы:\n\n"
            for i, (name, cid) in enumerate(updated_rows, 1):
                updated_text += f"{i}. {name}\n"

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Удалить канал", callback_data="del_num")]
            ])
            await update.message.reply_text(updated_text, reply_markup=kb)

        except ValueError:
            await update.message.reply_text("ты долбаеб")

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

app.run_polling()
