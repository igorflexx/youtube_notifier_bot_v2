from db import cursor, conn, get_user_channels
from youtube import get_latest_video
from datetime import datetime
import asyncio

# --- Проверка обновлений ---
async def check_updates(bot):
    cursor.execute("SELECT channel_id, last_video_id FROM channels")
    channels = cursor.fetchall()

    for channel_id, last_video_id in channels:
        latest = get_latest_video(channel_id)
        if not latest:
            continue

        # Если видео новое
        if latest["link"] != last_video_id:
            # Обновляем в базе
            cursor.execute("UPDATE channels SET last_video_id=? WHERE channel_id=?", (latest["link"], channel_id))
            conn.commit()

            # Отправляем уведомления всем подписанным
            cursor.execute("SELECT user_id FROM subscriptions WHERE channel_id=?", (channel_id,))
            subscribers = cursor.fetchall()
            text = f"📢 Новый ролик!\n🎬 {latest['title']}\n🗓 {latest['pub'].strftime('%d %B %H:%M')}\n🔗 {latest['link']}"
            for (user_id,) in subscribers:
                try:
                    await bot.send_message(chat_id=user_id, text=text)
                except Exception as e:
                    print(f"Не удалось отправить пользователю {user_id}: {e}")
