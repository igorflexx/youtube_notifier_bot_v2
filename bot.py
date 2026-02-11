import os
import sqlite3
import asyncio
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

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Мои каналы", callback_data="list")],
        [InlineKeyboardButton("🆕 Последние видео", callback_data="last_video")]
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Домой", callback_data="main_menu")]
    ])

def get_user_channels(uid):
    cur.execute("SELECT name, channel_id, last_video FROM channels WHERE user_id=?", (uid,))
    return cur.fetchall()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    states.pop(update.effective_user.id, None)
    await update.message.reply_text(
        "Скидывай ссылку на YouTube канал",
        reply_markup=main_menu()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "main_menu":
        states.pop(uid, None)
        await q.message.edit_text("Скидывай ссылку на YouTube канал", reply_markup=main_menu())

    elif q.data == "list":
        rows = get_user_channels(uid)
        if not rows:
            await q.message.edit_text("📭 Каналов нет", reply_markup=back_menu())
            return
        text = "📺 Твои каналы:\n\n" + "\n".join(
            f"{i+1}. {name}" for i, (name, _, _) in enumerate(rows)
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Удалить канал", callback_data="del")],
            [InlineKeyboardButton("🏠 Домой", callback_data="main_menu")]
        ])
        await q.message.edit_text(text, reply_markup=kb)

    elif q.data == "del":
        states[uid] = "del"
        await q.message.reply_text("Введи номер канала", reply_markup=back_menu())

    elif q.data == "last_video":
        rows = get_user_channels(uid)
        if not rows:
            await q.message.edit_text("📭 Каналов нет", reply_markup=back_menu())
            return

        videos = []
        for name, cid, _ in rows:
            v = get_last_video(cid)
            if not v:
                continue
            pub = datetime(*v.published_parsed[:6])
            videos.append((pub, name, v.title, v.link))

        videos.sort(reverse=True)
        text = "\n\n".join(
            f"📺 {name}\n🎬 {title}\n🗓 {pub:%d.%m %H:%M}\n🔗 {link}"
            for pub, name, title, link in videos
        )
        await q.message.edit_text(text or "Видео не найдены", reply_markup=back_menu())

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if states.get(uid) == "del":
        rows = get_user_channels(uid)
        try:
            idx = int(text) - 1
            name, cid, _ = rows[idx]
            cur.execute(
                "DELETE FROM channels WHERE user_id=? AND channel_id=?",
                (uid, cid)
            )
            db.commit()
            await update.message.reply_text(f"❌ Удалён: {name}", reply_markup=main_menu())
        except:
            await update.message.reply_text("Ошибка", reply_markup=main_menu())
        states.pop(uid, None)
        return

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
        await update.message.reply_text(f"✅ Добавлен: {info['title']}", reply_markup=main_menu())
    except:
        await update.message.reply_text("❌ Неверная ссылка", reply_markup=main_menu())

async def notifier(app: Application):
    while True:
        cur.execute("SELECT rowid, user_id, channel_id, name, last_video FROM channels")
        for rowid, uid, cid, name, last in cur.fetchall():
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
                    f"🆕 Новое видео!\n📺 {name}\n🎬 {v.title}\n🔗 {v.link}"
                )
        await asyncio.sleep(300)

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    asyncio.create_task(notifier(app))

    print("Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
