# scheduler.py
import feedparser
from db import cursor, conn
from datetime import datetime

CHECK_INTERVAL = 60  # 1 минута

def check_updates(bot):
    """Проверка новых видео для всех каналов"""
    cursor.execute("SELECT channel_id, last_video_id FROM channels")
    channels = cursor.fetchall()

    for channel_id, last_video in channels:
        feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
        if not feed.entries:
            continue

        entry = feed.entries[0]
        video_id = entry.yt_videoid

        if video_id != last_video:
            cursor.execute("UPDATE channels SET last_video_id=? WHERE channel_id=?", (video_id, channel_id))
            conn.commit()

            cursor.execute("SELECT user_id FROM subscriptions WHERE channel_id=?", (channel_id,))
            users = cursor.fetchall()

            for (uid,) in users:
                pub_time = datetime(*entry.published_parsed[:6])
                bot.send_message(
                    uid,
                    f"🎬 Новое видео!\n\n"
                    f"📺 Канал: {entry.author}\n"
                    f"🎬 Название: {entry.title}\n"
                    f"🗓 Дата: {pub_time.strftime('%d %B %H:%M')}\n"
                    f"🔗 Ссылка: {entry.link}"
                )
