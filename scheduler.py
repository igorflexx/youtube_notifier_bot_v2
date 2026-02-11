from db import cursor, conn, get_user_channels
from datetime import datetime
import feedparser

async def check_updates(bot):
    cursor.execute("SELECT DISTINCT user_id FROM subscriptions")
    users = cursor.fetchall()
    for (uid,) in users:
        channels = get_user_channels(uid)
        for name, cid in channels:
            feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")
            if not feed.entries:
                continue
            entry = feed.entries[0]
            pub_time = datetime(*entry.published_parsed[:6])
            cursor.execute("SELECT last_video FROM channels WHERE channel_id=?", (cid,))
            last_row = cursor.fetchone()
            if last_row is None:
                continue
            last_saved = last_row[0]
            if last_saved is None or pub_time > datetime.fromisoformat(last_saved):
                msg = f"📺 {name}\n🎬 {entry.title}\n🗓 {pub_time.strftime('%d %B %H:%M')}\n🔗 {entry.link}"
                await bot.send_message(chat_id=uid, text=msg)
                cursor.execute("UPDATE channels SET last_video=? WHERE channel_id=?", (pub_time.isoformat(), cid))
    conn.commit()
