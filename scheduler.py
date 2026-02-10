# scheduler.py
import feedparser
from db import cursor, conn
from datetime import datetime

def check_updates(bot):
    """
    Проверяет новые видео на всех каналах и отправляет уведомления пользователям.
    Работает корректно, даже если меню открыты.
    """
    cursor.execute("SELECT channel_id, last_video_id FROM channels")
    channels = cursor.fetchall()

    for channel_id, last_video_id in channels:
        feed = feedparser.parse(
            f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        )

        if not feed.entries:
            continue

        latest_entry = feed.entries[0]
        latest_video_id = latest_entry.yt_videoid

        # Если есть новое видео
        if latest_video_id != last_video_id:
            # Обновляем last_video_id в базе
            cursor.execute(
                "UPDATE channels SET last_video_id=? WHERE channel_id=?",
                (latest_video_id, channel_id)
            )
            conn.commit()

            # Получаем всех пользователей, подписанных на канал
            cursor.execute(
                "SELECT user_id FROM subscriptions WHERE channel_id=?",
                (channel_id,)
            )
            users = cursor.fetchall()

            # Формируем сообщение
            pub_time = datetime(*latest_entry.published_parsed[:6]).strftime("%d %B %H:%M")
            msg_text = (
                f"🎬 Новое видео!\n\n"
                f"📺 Канал: {feed.feed.title}\n"
                f"🗓 Дата: {pub_time}\n"
                f"🎥 Название: {latest_entry.title}\n"
                f"🔗 Ссылка: {latest_entry.link}"
            )

            # Отправляем уведомление всем подписанным
            for (uid,) in users:
                try:
                    bot.send_message(uid, msg_text)
                except Exception as e:
                    print(f"Ошибка при отправке уведомления пользователю {uid}: {e}")
