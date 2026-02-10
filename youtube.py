# youtube.py
import requests
import re

def resolve_channel(url: str):
    """Возвращает channel_id по ссылке канала, поддерживает /channel/ID и /@handle"""
    if "channel/" in url:
        return url.split("channel/")[1].split("/")[0]

    if "/@" in url:
        handle = url.split("/@")[1].split("/")[0]
        try:
            html = requests.get(f"https://www.youtube.com/@{handle}").text
            match = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', html)
            if match:
                return match.group(1)
        except:
            return None

    return None

def get_channel_info(channel_id: str):
    """Возвращает (channel_name, last_video_id)"""
    import feedparser
    feed = feedparser.parse(
        f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    )
    if not feed.entries:
        return None, None

    name = feed.feed.title
    last_video = feed.entries[0].yt_videoid
    return name, last_video
