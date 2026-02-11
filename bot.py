import os
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from youtube import (
    resolve_channel,
    get_channel_info,
    get_latest_video,
)

TOKEN = os.getenv("BOT_TOKEN")

# --------- КЛАВИАТУРА ---------

def home_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Мои каналы", callback_data="my_channels")],
        [InlineKeyboardButton("🆕 Последние видео", callback_data="latest_videos")],
    ])


def back_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Домой", callback_data="home")]
    ])


def delete_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Удалить канал", callback_data="delete_channel")],
        [InlineKeyboardButton("🏠 Домой", callback_data="home")],
    ])


# --------- /start ---------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("channels", [])
    await update.message.reply_text(
        "Скидывай ссылку на YouTube канал",
        reply_markup=home_kb()
    )


# --------- ДОБАВЛЕНИЕ КАНАЛА ---------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("await_delete"):
        await handle_delete_number(update, context)
        return

    url = update.message.text.strip()
    channel_id = resolve_channel(url)

    if not channel_id:
        await update.message.reply_text("❌ Не удалось определить канал")
        return

    info = get_channel_info(channel_id)
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
        reply_markup=home_kb()
    )


# --------- КНОПКИ ---------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "home":
        await q.message.edit_text(
            "Скидывай ссылку на YouTube канал",
            reply_markup=home_kb()
        )

    elif q.data == "my_channels":
        await show_channels(q, context)

    elif q.data == "delete_channel":
        context.user_data["await_delete"] = True
        await q.message.reply_text("Введите номер канала для удаления")

    elif q.data == "latest_videos":
        await show_latest_videos(q, context)


# --------- МОИ КАНАЛЫ ---------

async def show_channels(q, context):
    channels = context.user_data.get("channels", [])

    if not channels:
        await q.message.reply_text("📭 Каналов нет", reply_markup=back_kb())
        return

    text = "📺 Мои каналы:\n\n"
    for i, ch in enumerate(channels, 1):
        text += f"{i}. {ch['title']}\n"

    await q.message.reply_text(text, reply_markup=delete_kb())


# --------- УДАЛЕНИЕ ПО НОМЕРУ ---------

async def handle_delete_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["await_delete"] = False
    channels = context.user_data.get("channels", [])

    try:
        idx = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("ты долбаеб?")
        return

    if idx < 1 or idx > len(channels):
        await update.message.reply_text("ты долбаеб?")
        return

    removed = channels.pop(idx - 1)
    await update.message.reply_text(
        f"🗑 Канал удалён: {removed['title']}",
        reply_markup=home_kb()
    )


# --------- ПОСЛЕДНИЕ ВИДЕО ---------

async def show_latest_videos(q, context):
    channels = context.user_data.get("channels", [])

    if not channels:
        await q.message.reply_text("📭 Сначала добавь канал", reply_markup=back_kb())
        return

    text = "🆕 Последние видео:\n\n"

    for ch in channels:
        video = get_latest_video(ch["id"])
        if not video:
            continue

        dt = datetime.fromisoformat(video["published"])
        date = dt.strftime("%d %B %H:%M")

        text += (
            f"📺 {ch['title']}\n"
            f"🎬 {video['title']}\n"
            f"🕒 {date}\n"
            f"{video['url']}\n\n"
        )

    await q.message.reply_text(text.strip(), reply_markup=back_kb())


# --------- УВЕДОМЛЕНИЯ ---------

async def notify_job(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, data in context.application.user_data.items():
        channels = data.get("channels", [])
        last_ids = data.setdefault("last_videos", {})

        for ch in channels:
            video = get_latest_video(ch["id"])
            if not video:
                continue

            if last_ids.get(ch["id"]) == video["id"]:
                continue

            last_ids[ch["id"]] = video["id"]

            dt = datetime.fromisoformat(video["published"])
            date = dt.strftime("%d %B %H:%M")

            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"🆕 Новое видео!\n\n"
                    f"📺 {ch['title']}\n"
                    f"🎬 {video['title']}\n"
                    f"🕒 {date}\n"
                    f"{video['url']}"
                )
            )


# --------- ЗАПУСК ---------

def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.job_queue.run_repeating(notify_job, interval=300, first=10)

    print("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
