# scheduler.py
from datetime import datetime
import feedparser
from db import get_user_channels, cursor, conn

async def check_updates(bot):
    """
    Проверяем новые видео для всех пользователей и каналов.
    Если есть новое видео — шлем уведомление.
    """
    # Получаем всех пользователей с их каналами
    users_channels = {}  # {uid: [(channel_name, channel_id)]}
    cursor.execute("SELECT user_id, channel_id FROM subscriptions")
    rows = cursor.fetchall()
    for uid, cid in rows:
        users_channels.setdefault(uid, []).append(cid)

    for uid, cids in users_channels.items():
        for cid in cids:
            # Берем название канала и последнее известное видео из базы
            cursor.execute("SELECT name, last_video_id FROM channels WHERE channel_id=?", (cid,))
            res = cursor.fetchone()
            if not res:
                continue
            name, last_video_id = res

            feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")
            if not feed.entries:
                continue

            entry = feed.entries[0]
            video_id = entry.yt_videoid
            video_title = entry.title
            video_link = entry.link
            published = datetime(*entry.published_parsed[:6])

            # Если видео новое
            if last_video_id != video_id:
                # Сохраняем новый ID видео
                cursor.execute("UPDATE channels SET last_video_id=? WHERE channel_id=?", (video_id, cid))
                conn.commit()

                # Отправляем уведомление пользователю
                try:
                    await bot.send_message(
                        chat_id=uid,
                        text=f"📢 Новое видео на канале {name}!\n🎬 {video_title}\n🗓 {published.strftime('%d %B %H:%M')}\n🔗 {video_link}"
                    )
                except Exception as e:
                    print(f"Ошибка при отправке уведомления {uid}: {e}")
