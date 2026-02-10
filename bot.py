# bot.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import feedparser
import sqlite3
from db import cursor, conn, get_user_channels, remove_channel
from youtube import resolve_channel, get_channel_info
from scheduler import check_updates

DB_PATH = "/data/database.db"  # Railway volume

TOKEN = os.getenv("BOT_TOKEN")
app = ApplicationBuilder().token(TOKEN).build()

# Планировщик проверяет новые видео каждые 1 минуту
scheduler = BackgroundScheduler()
scheduler.add_job(check_updates, "interval", minutes=1, args=[app.bot])
scheduler.start()

states = {}
last_message = {}  # {user_id: message_id} для редактирования списка

# --- Меню ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Мои каналы", callback_data="list")],
        [InlineKeyboardButton("🎬 Последние видео", callback_data="last_video")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ])

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(
        "Скидывай ссылку на канал в чат",
        reply_markup=main_menu()
    )
    last_message[update.message.from_user.id] = msg.message_id

# --- Кнопки ---
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    last_message[uid] = q.message.message_id

    if q.data == "main_menu":
        await q.message.edit_text(
            "Скидывай ссылку на канал в чат",
            reply_markup=main_menu()
        )
        states.pop(uid, None)
        return

    elif q.data == "list":
        rows = get_user_channels(uid)
        if not rows:
            await q.message.edit_text("📭 У тебя пока нет каналов", reply_markup=back_menu())
            return
        text = "📺 Твои каналы:\n\n" + "\n".join(f"{i+1}. {name}" for i, (name, _) in enumerate(rows))
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Удалить канал", callback_data="del_num")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ])
        await q.message.edit_text(text, reply_markup=kb)

    elif q.data == "del_num":
        states[uid] = "del_num"
        await q.message.reply_text("Введи номер канала, который хочешь удалить", reply_markup=back_menu())

    elif q.data == "last_video":
        rows = get_user_channels(uid)
        if not rows:
            await q.message.edit_text("📭 У тебя пока нет каналов", reply_markup=back_menu())
            return

        video_list = []
        for name, cid in rows:
            try:
                feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")
                if not feed.entries:
                    continue
                entry = feed.entries[0]
                pub_time = datetime(*entry.published_parsed[:6])
                video_list.append({
                    "channel": name,
                    "title": entry.title,
                    "link": entry.link,
                    "pub": pub_time
                })
            except Exception as e:
                print(f"Ошибка при получении видео для {name}: {e}")

        if not video_list:
            await q.message.edit_text("📭 Не удалось получить последние видео", reply_markup=back_menu())
            return

        video_list.sort(key=lambda x: x["pub"], reverse=True)
        msg_text = "\n\n".join([
            f"📺 {v['channel']}\n🎬 {v['title']}\n🗓 {v['pub'].strftime('%d %B %H:%M')}\n🔗 {v['link']}"
            for v in video_list
        ])
        await q.message.edit_text(msg_text, reply_markup=back_menu())

# --- Сообщения ---
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text.strip()

    # Добавление нового канала по ссылке
    if text.startswith("http://") or text.startswith("https://"):
        cid = resolve_channel(text)
        if not cid:
            await update.message.reply_text("❌ Не удалось определить канал")
            return

        name, last = get_channel_info(cid)
        if not name:
            await update.message.reply_text("❌ Не удалось получить информацию о канале")
            return

        cursor.execute("INSERT OR IGNORE INTO channels VALUES (?, ?, ?)", (cid, name, last))
        cursor.execute("INSERT OR IGNORE INTO subscriptions VALUES (?, ?)", (uid, cid))
        conn.commit()
        await update.message.reply_text(f"✅ Канал добавлен: {name}", reply_markup=back_menu())

    # Удаление по номеру
    elif states.get(uid) == "del_num":
        rows = get_user_channels(uid)
        if not rows:
            await update.message.reply_text("📭 У тебя пока нет каналов", reply_markup=back_menu())
            states.pop(uid, None)
            return

        try:
            num = int(text)
            if num < 1 or num > len(rows):
                raise ValueError
            cid_to_delete = rows[num - 1][1]
            remove_channel(uid, cid_to_delete)
            states.pop(uid, None)

            # Обновляем список
            updated_rows = get_user_channels(uid)
            if not updated_rows:
                await update.message.reply_text("📭 У тебя пока нет каналов", reply_markup=back_menu())
                return
            updated_text = "📺 Твои каналы:\n\n" + "\n".join(f"{i+1}. {name}" for i, (name, _) in enumerate(updated_rows))
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Удалить канал", callback_data="del_num")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
            ])
            message_id = last_message.get(uid)
            if message_id:
                await context.bot.edit_message_text(chat_id=uid, message_id=message_id, text=updated_text, reply_markup=kb)
        except ValueError:
            await update.message.reply_text("ты долбаеб", reply_markup=back_menu())

# --- Обработчики ---
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

app.run_polling()
