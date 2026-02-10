import re
import feedparser
from datetime import datetime

# Преобразование ссылки на канал в ID
def resolve_channel(url: str):
    if "/channel/" in url:
        return url.split("/channel/")[1].split("/")[0]
    elif "/@" in url:
        # username -> channel ID через RSS
        username = url.split("/@")[1].split("/")[0]
        feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?user={username}")
        if feed.entries:
            return feed.entries[0].yt_channelid
    return None

# Получение имени канала и последнего видео
def get_channel_info(cid: str):
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")
    if feed.entries:
        last_video_time = datetime(*feed.entries[0].published_parsed[:6])
        return feed.feed.title, last_video_time
    return "Неизвестный канал", None
