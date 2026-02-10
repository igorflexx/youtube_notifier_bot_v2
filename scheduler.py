from db import cursor, conn, get_subscribed_users
from youtube import get_latest_video
import asyncio

async def check_updates(bot):
    """
    Проверяет новые видео для всех пользователей и каналов
    """
    cursor.execute("SELECT DISTINCT channel_id FROM subscriptions")
    channels = cursor.fetchall()

    for (channel_id,) in channels:
        latest = get_latest_video(channel_id)
        if not latest:
            continue
        video_id, title, pub = latest

        # Проверяем, было ли видео уже сохранено
        cursor.execute("SELECT last_video FROM channels WHERE channel_id=?", (channel_id,))
        row = cursor.fetchone()
        if row and row[0] == video_id:
            continue  # Уже уведомляли

        # Обновляем последний видео id
        cursor.execute("UPDATE channels SET last_video=? WHERE channel_id=?", (video_id, channel_id))
        conn.commit()

        # Отправляем всем подписанным пользователям
        users = get_subscribed_users(channel_id)
        for uid in users:
            try:
                await bot.send_message(uid, f"📢 Новое видео!\n🎬 {title}\nhttps://youtu.be/{video_id}")
            except Exception as e:
                print(f"Не удалось отправить пользователю {uid}: {e}")
