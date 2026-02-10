import requests
import feedparser
import re

def resolve_channel(url: str):
    """
    Определяет channel_id по ссылке на канал.
    Работает с:
    - https://www.youtube.com/channel/UCxxxx
    - https://www.youtube.com/@username
    """
    url = url.strip()

    # Если прямая ссылка на канал
    if "channel/" in url:
        return url.split("channel/")[1].split("/")[0]

    # Если ссылка с @username
    if "/@" in url:
        handle = url.split("/@")[1].split("/")[0]

        # Пробуем через RSS feed (альтернатива HTML, работает стабильнее)
        rss_url = f"https://www.youtube.com/feeds/videos.xml?user={handle}"
        feed = feedparser.parse(rss_url)
        if feed.entries:
            # Если RSS сработал, вытаскиваем channel_id из feed
            return feed.feed.get('yt_channelid', None)

        # Альтернатива через HTML (если RSS не сработал)
        html = requests.get(f"https://www.youtube.com/@{handle}").text
        match = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', html)
        if match:
            return match.group(1)

    return None


def get_channel_info(channel_id: str):
    """
    Возвращает название канала и id последнего видео.
    """
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        return None, None

    name = feed.feed.title
    last_video = feed.entries[0].yt_videoid
    return name, last_video
