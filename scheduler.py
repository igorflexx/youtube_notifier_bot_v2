from db import cursor, conn, get_user_channels
from youtube import get_channel_info
from datetime import datetime
import asyncio

async def notify_user(bot, user_id, text):
    from telegram.error import TelegramError
    try:
        await bot.send_message(chat_id=user_id, text=text)
    except TelegramError:
        pass

# Проверка обновлений
async def check_updates(bot):
    cursor.execute("SELECT DISTINCT user_id FROM subscriptions")
    users = [row[0] for row in cursor.fetchall()]

    for uid in users:
        channels = get_user_channels(uid)
        for name, cid in channels:
            channel_name, last_video_time = get_channel_info(cid)
            cursor.execute("SELECT last_video FROM channels WHERE channel_id=?", (cid,))
            old_last = cursor.fetchone()[0]

            if last_video_time and old_last != last_video_time:
                text = f"🎬 Новый ролик на канале {channel_name}!\n🗓 {last_video_time.strftime('%d %B %H:%M')}"
                await notify_user(bot, uid, text)
                cursor.execute("UPDATE channels SET last_video=? WHERE channel_id=?", (last_video_time, cid))
                conn.commit()
