import requests
import feedparser
import re

def resolve_channel(url: str):
    # Прямой channel_id
    if "channel/" in url:
        return url.split("channel/")[1].split("/")[0]

    # Ссылка на handle (@имя)
    if "/@" in url:
        handle = url.split("/@")[1].split("/")[0]
        try:
            html = requests.get(f"https://www.youtube.com/@{handle}").text
            match = re.search(r'"channelId":"([A-Za-z0-9_-]+)"', html)
            if match:
                return match.group(1)
        except Exception:
            return None
    return None

def get_channel_info(channel_id: str):
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    if not feed.entries:
        return None, None
    name = feed.feed.title
    last_video = feed.entries[0].yt_videoid
    return name, last_video
