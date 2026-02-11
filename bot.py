import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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


def keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Мои каналы", callback_data="my_channels")],
        [InlineKeyboardButton("🆕 Последние видео", callback_data="latest_videos")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Скидывай ссылку на YouTube канал",
        reply_markup=keyboard()
    )


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

    channels = context.user_data.setdefault("channels", {})
    channels[info["id"]] = info["title"]

    await update.message.reply_text(
        f"✅ Канал добавлен: {info['title']}",
        reply_markup=keyboard()
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "my_channels":
        channels = context.user_data.get("channels", {})
        if not channels:
            await q.message.reply_text("📭 Каналов нет")
            return

        text = "📺 Твои каналы:\n\n"
        for title in channels.values():
            text += f"• {title}\n"

        await q.message.reply_text(text)

    elif q.data == "latest_videos":
        channels = context.user_data.get("channels", {})
        if not channels:
            await q.message.reply_text("📭 Сначала добавь канал")
            return

        await q.message.reply_text("🆕 Проверка новых видео скоро будет подключена")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
