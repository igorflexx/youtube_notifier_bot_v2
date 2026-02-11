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

# ====== КНОПКИ ======
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Мои каналы", callback_data="my_channels")],
        [InlineKeyboardButton("🆕 Последние видео", callback_data="latest_videos")],
    ])

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Скидывай ссылку на YouTube канал",
        reply_markup=main_keyboard()
    )

# ====== ОБРАБОТКА ССЫЛКИ ======
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    channel_id = resolve_channel(text)
    if not channel_id:
        await update.message.reply_text("❌ Не удалось определить канал")
        return  # ⛔ ВАЖНО: дальше код НЕ идёт

    info = get_channel_info(channel_id)
    if not info:
        await update.message.reply_text("❌ Не удалось получить информацию о канале")
        return

    # сохраняем канал
    user_channels = context.user_data.setdefault("channels", {})
    user_channels[channel_id] = info["title"]

    await update.message.reply_text(
        f"✅ Канал добавлен: {info['title']}",
        reply_markup=main_keyboard()
    )

# ====== КНОПКИ ======
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "my_channels":
        channels = context.user_data.get("channels", {})
        if not channels:
            await query.message.reply_text("📭 У тебя нет добавленных каналов")
            return

        text = "📺 Твои каналы:\n\n"
        for title in channels.values():
            text += f"• {title}\n"

        await query.message.reply_text(text)

    elif query.data == "latest_videos":
        channels = context.user_data.get("channels", {})
        if not channels:
            await query.message.reply_text("📭 Сначала добавь канал")
            return

        await query.message.reply_text("🆕 Проверка новых видео...")

# ====== MAIN ======
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
