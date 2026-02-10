import feedparser
from db import cursor, conn

def check_updates(bot):
    cursor.execute("SELECT channel_id, last_notified_video_id FROM channels")
    channels = cursor.fetchall()

    for channel_id, last_notified in channels:
        feed = feedparser.parse(
            f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        )
        if not feed.entries:
            continue

        entry = feed.entries[0]
        video_id = entry.yt_videoid

        # Если новое видео для уведомлений
        if video_id != last_notified:
            # обновляем last_notified_video_id
            cursor.execute(
                "UPDATE channels SET last_notified_video_id=? WHERE channel_id=?",
                (video_id, channel_id)
            )
            conn.commit()

            # уведомляем подписанных пользователей
            cursor.execute(
                "SELECT user_id FROM subscriptions WHERE channel_id=?",
                (channel_id,)
            )
            users = cursor.fetchall()

            for (uid,) in users:
                bot.send_message(
                    uid,
                    f"🎬 Новое видео!\n\n{entry.title}\n{entry.link}"
                )
