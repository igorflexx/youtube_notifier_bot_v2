import os
import sqlite3
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from youtube import resolve_channel, get_channel_info, get_last_video

TOKEN = os.getenv("BOT_TOKEN")

# ---------- DB ----------
db = sqlite3.connect("db.sqlite3", check_same_thread=False)
cur = db.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS channels (
    user_id INTEGER,
    channel_id TEXT,
    name TEXT,
    last_video TEXT
)
""")
db.commit()

states = {}

# ---------- Keyboards ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Мои каналы", callback_data="list")],
        [InlineKeyboardButton("🆕 Последние видео", callback_data="last_video")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Домой", callback_data="main_menu")]
    ])

# ---------- Helpers ----------
def get_user_channels(uid):
    cur.execute(
        "SELECT rowid, name, channel_id, last_video FROM channels WHERE user_id=?",
        (uid,)
    )
    return cur.fetchall()

# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    states.pop(update.effective_user.id, None)
    await update.message.reply_text(
        "Скидывай ссылку на YouTube канал",
        reply_markup=main_menu()
    )

# ---------- Buttons ----------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "main_menu":
        states.pop(uid, None)
        await q.message.edit_text(
            "Скидывай ссылку на YouTube канал",
            reply_markup=main_menu()
        )

    elif q.data == "list":
        rows = get_user_channels(uid)
        if not rows:
            await q.message.edit_text("📭 Каналов нет", reply_markup=back_menu())
            return

        text = "📺 Твои каналы:\n\n"
        for i, (_, name, _, _) in enumerate(rows, 1):
            text += f"{i}. {name}\n"

        await q.message.edit_text(text, reply_markup=back_menu())

    elif q.data == "last_video":
        rows = get_user_channels(uid)
        videos = []

        for _, name, cid, _ in rows:
            v = get_last_video(cid)
            if not v:
                continue
            pub = datetime(*v.published_parsed[:6])
            videos.append((pub, name, v.title, v.link))

        videos.sort(reverse=True)

        if not videos:
            await q.message.edit_text("Видео не найдены", reply_markup=back_menu())
            return

        text = ""
        for pub, name, title, link in videos:
            text += (
                f"📺 {name}\n"
                f"🎬 {title}\n"
                f"🗓 {pub:%d.%m %H:%M}\n"
                f"🔗 {link}\n\n"
            )

        await q.message.edit_text(text, reply_markup=back_menu())

# ---------- Text ----------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    try:
        cid = resolve_channel(text)
        info = get_channel_info(cid)
        if not info:
            raise ValueError

        cur.execute(
            "INSERT INTO channels VALUES (?,?,?,?)",
            (uid, cid, info["title"], "")
        )
        db.commit()

        await update.message.reply_text(
            f"✅ Добавлен канал: {info['title']}",
            reply_markup=main_menu()
        )

    except:
        await update.message.reply_text(
            "❌ Не удалось определить канал",
            reply_markup=main_menu()
        )

# ---------- NOTIFIER (JobQueue) ----------
async def notify_job(context: ContextTypes.DEFAULT_TYPE):
    app = context.application

    cur.execute("SELECT rowid, user_id, channel_id, name, last_video FROM channels")
    rows = cur.fetchall()

    for rowid, uid, cid, name, last in rows:
        v = get_last_video(cid)
        if not v:
            continue

        if v.id != last:
            cur.execute(
                "UPDATE channels SET last_video=? WHERE rowid=?",
                (v.id, rowid)
            )
            db.commit()

            await app.bot.send_message(
                uid,
                f"🆕 Новое видео!\n"
                f"📺 {name}\n"
                f"🎬 {v.title}\n"
                f"🔗 {v.link}"
            )

# ---------- MAIN ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # каждые 5 минут
    app.job_queue.run_repeating(notify_job, interval=300, first=10)

    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
