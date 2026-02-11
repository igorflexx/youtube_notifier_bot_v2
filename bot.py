import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from youtube import resolve_channel, get_channel_info

TOKEN = os.getenv("BOT_TOKEN")


# ---------- КЛАВИАТУРА ----------

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Мои каналы", callback_data="my_channels")],
        [InlineKeyboardButton("🆕 Последние видео", callback_data="latest_videos")],
    ])


# ---------- /start ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Скидывай ссылку на YouTube канал",
        reply_markup=main_keyboard()
    )


# ---------- ДОБАВЛЕНИЕ КАНАЛА ----------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    channel = resolve_channel(text)
    if not channel:
        await update.message.reply_text("❌ Не удалось определить канал")
        return

    info = get_channel_info(channel)
    if not info:
        await update.message.reply_text("❌ Канал не найден")
        return

    channels = context.user_data.setdefault("channels", [])

    if any(c["id"] == info["id"] for c in channels):
        await update.message.reply_text("⚠️ Канал уже добавлен")
        return

    channels.append(info)

    await update.message.reply_text(
        f"✅ Канал добавлен: {info['title']}",
        reply_markup=main_keyboard()
    )


# ---------- КНОПКИ ----------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data

    if data == "my_channels":
        await show_channels(q, context)

    elif data == "latest_videos":
        await show_latest_videos(q, context)

    elif data.startswith("del_"):
        await delete_channel(q, context, data)


# ---------- МОИ КАНАЛЫ ----------

async def show_channels(q, context):
    channels = context.user_data.get("channels", [])

    if not channels:
        await q.message.reply_text("📭 Каналов нет")
        return

    for ch in channels:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Удалить", callback_data=f"del_{ch['id']}")]
        ])

        await q.message.reply_text(
            f"📺 {ch['title']}",
            reply_markup=kb
        )


# ---------- УДАЛЕНИЕ ----------

async def delete_channel(q, context, data):
    channel_id = data.replace("del_", "")
    channels = context.user_data.get("channels", [])

    for ch in channels:
        if ch["id"] == channel_id:
            channels.remove(ch)
            await q.message.reply_text(f"🗑 Канал удалён: {ch['title']}")
            return

    await q.message.reply_text("❌ Канал не найден")


# ---------- ПОСЛЕДНИЕ ВИДЕО ----------

async def show_latest_videos(q, context):
    channels = context.user_data.get("channels", [])

    if not channels:
        await q.message.reply_text("📭 Сначала добавь канал")
        return

    text = "🆕 Последние видео:\n\n"
    for ch in channels:
        text += f"• {ch['title']}\n"

    await q.message.reply_text(text)


# ---------- ЗАПУСК ----------

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
