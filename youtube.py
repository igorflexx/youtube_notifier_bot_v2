import re
import requests
import feedparser


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def resolve_channel(url: str):
    """
    Надёжно определяет channel_id (UC...) для:
    - https://www.youtube.com/@handle
    - https://www.youtube.com/channel/UC...
    - https://www.youtube.com/user/username
    """

    # 1️⃣ Если channel_id уже есть
    match = re.search(r"(UC[a-zA-Z0-9_-]{22})", url)
    if match:
        return match.group(1)

    # 2️⃣ Приводим к /about (самый надёжный способ)
    if "/about" not in url:
        url = url.rstrip("/") + "/about"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None

        html = resp.text

        # YouTube всегда кладёт channelId в JSON
        match = re.search(r'"channelId":"(UC[a-zA-Z0-9_-]{22})"', html)
        if match:
            return match.group(1)

    except Exception:
        return None

    return None


def get_channel_info(channel_id: str):
    feed = feedparser.parse(
        f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    )

    if not feed.entries:
        return None, None

    name = feed.feed.title
    last_video = feed.entries[0].yt_videoid
    return name, last_video
