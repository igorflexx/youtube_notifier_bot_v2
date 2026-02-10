import feedparser
from datetime import datetime
import re

# --- Определяем channel_id ---
def resolve_channel(url_or_username):
    if "channel/" in url_or_username:
        return url_or_username.split("channel/")[1].split("/")[0]
    elif "/@" in url_or_username:
        username = url_or_username.split("/@")[1].split("/")[0]
        feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?user={username}")
        if feed.entries:
            return feed.entries[0].yt_channelid
    return None

# --- Получаем инфо о канале ---
def get_channel_info(channel_id):
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    if not feed.entries:
        return ("Неизвестный канал", None)
    entry = feed.entries[0]
    pub_time = datetime(*entry.published_parsed[:6])
    return (feed.feed.title, entry.id)

# --- Последнее видео ---
def get_latest_video(channel_id):
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    if not feed.entries:
        return None
    entry = feed.entries[0]
    pub_time = datetime(*entry.published_parsed[:6])
    return {
        "title": entry.title,
        "link": entry.link,
        "pub": pub_time
    }
