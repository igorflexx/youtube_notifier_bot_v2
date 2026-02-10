import feedparser
from db import cursor, conn
from datetime import datetime

def check_updates(bot):
    """Проверяет новые видео и уведомляет пользователей"""
    cursor.execute("SELECT channel_id, last_video_id FROM channels")
    channels = cursor.fetchall()

    for channel_id, last_video in channels:
        feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
        if not feed.entries:
            continue

        entry = feed.entries[0]
        video_id = entry.yt_videoid

        if video_id != last_video:
            # обновляем последний просмотренный видео ID
            cursor.execute("UPDATE channels SET last_video_id=? WHERE channel_id=?", (video_id, channel_id))
            conn.commit()

            # уведомляем всех подписанных пользователей
            cursor.execute("SELECT user_id FROM subscriptions WHERE channel_id=?", (channel_id,))
            users = cursor.fetchall()

            pub_time = datetime(*entry.published_parsed[:6]).strftime('%d %B %H:%M')

            for (uid,) in users:
                try:
                    bot.send_message(
                        uid,
                        f"🎬 Новое видео!\n\n"
                        f"📺 Канал: {entry.author}\n"
                        f"🎥 Название: {entry.title}\n"
                        f"🗓 Дата: {pub_time}\n"
                        f"🔗 Ссылка: {entry.link}"
                    )
                except Exception as e:
                    print(f"Не удалось отправить сообщение {uid}: {e}")
