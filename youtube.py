import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import feedparser

def resolve_channel(url: str) -> str | None:
    """
    Получает channel_id по ссылке на канал или @username
    """
    if "/channel/" in url:
        return url.split("/channel/")[1].split("/")[0]
    elif "/@" in url:
        username = url.split("/@")[1].split("/")[0]
        r = requests.get(f"https://www.youtube.com/@{username}")
        match = re.search(r'channelId":"(UC[\w-]+)"', r.text)
        if match:
            return match.group(1)
    return None

def get_channel_info(channel_id: str) -> tuple[str, str]:
    """
    Возвращает (название канала, последний video_id)
    """
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    if not feed.entries:
        return ("Неизвестный канал", "")
    name = feed.feed.title
    last_video_id = feed.entries[0].id.split(":")[-1]
    return name, last_video_id

def get_latest_video(channel_id: str) -> tuple[str, str, datetime] | None:
    """
    Возвращает (video_id, title, publish_datetime) последнего видео
    """
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    if not feed.entries:
        return None
    entry = feed.entries[0]
    video_id = entry.id.split(":")[-1]
    title = entry.title
    pub = datetime(*entry.published_parsed[:6])
    return video_id, title, pub
