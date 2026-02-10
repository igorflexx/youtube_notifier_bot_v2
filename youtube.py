import re
import feedparser
import requests


def resolve_channel(url: str):
    """Возвращает channel_id по ссылке канала, поддерживает /channel/ID и /@handle"""
    url = url.strip()

    # прямой channel ID
    if "channel/" in url:
        return url.split("channel/")[1].split("/")[0]

    # handle
    if "/@" in url:
        handle = url.split("/@")[1].split("/")[0]
        try:
            # Пробуем RSS: https://www.youtube.com/feeds/videos.xml?user=HANDLE
            rss_url = f"https://www.youtube.com/feeds/videos.xml?user={handle}"
            feed = feedparser.parse(rss_url)
            if feed.entries:
                # берем channel_id из feed
                return feed.feed.yt_channelid
        except:
            pass

        # fallback: старая проверка через HTML (не всегда работает)
        try:
            html = requests.get(f"https://www.youtube.com/@{handle}").text
            match = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', html)
            if match:
                return match.group(1)
        except:
            pass

    return None


def get_channel_info(channel_id: str):
    """Возвращает (channel_name, last_video_id)"""
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    if not feed.entries:
        return None, None

    name = feed.feed.title
    last_video = feed.entries[0].yt_videoid
    return name, last_video
