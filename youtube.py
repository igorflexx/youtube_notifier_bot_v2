# youtube.py
import re
import requests
import feedparser
from datetime import datetime

YOUTUBE_CHANNEL_REGEX = re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/(?:channel/|@)?([a-zA-Z0-9_-]+)")

def resolve_channel(url_or_name):
    """
    Определяет channel_id по ссылке или @username.
    Возвращает channel_id или None, если не удалось.
    """
    match = YOUTUBE_CHANNEL_REGEX.match(url_or_name)
    if match:
        ident = match.group(1)
        # Если это username, нужно получить channel_id через YouTube API или альтернативно
        if ident.startswith("@"):
            # Через RSS можно попробовать найти ID
            rss_url = f"https://www.youtube.com/feeds/videos.xml?user={ident[1:]}"
            feed = feedparser.parse(rss_url)
            if feed.entries:
                return feed.entries[0].yt_channelid
            return None
        else:
            return ident
    return None

def get_channel_info(channel_id):
    """
    Возвращает название канала и дату публикации последнего видео.
    Формат: (name, last_video_date)
    """
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        return ("Неизвестный канал", None)
    name = feed.feed.title
    last_pub = datetime(*feed.entries[0].published_parsed[:6])
    return (name, last_pub)

def get_latest_video(channel_id):
    """
    Возвращает информацию о последнем видео канала.
    Формат: {"title": ..., "link": ..., "pub": datetime_object}
    """
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        return None
    entry = feed.entries[0]
    pub_time = datetime(*entry.published_parsed[:6])
    return {
        "title": entry.title,
        "link": entry.link,
        "pub": pub_time
    }
