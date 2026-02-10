import re
import requests
import feedparser


def resolve_channel(url: str):
    """
    Принимает любую ссылку на YouTube-канал и возвращает channel_id (UC...)
    Поддерживает:
    - https://www.youtube.com/@handle
    - https://www.youtube.com/channel/UC...
    - https://www.youtube.com/user/username
    """

    # 1️⃣ Если channel_id уже есть в ссылке
    match = re.search(r"(UC[a-zA-Z0-9_-]{22})", url)
    if match:
        return match.group(1)

    # 2️⃣ Пробуем через oEmbed (работает для @handle и /user/)
    try:
        response = requests.get(
            "https://www.youtube.com/oembed",
            params={
                "url": url,
                "format": "json"
            },
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()
        author_url = data.get("author_url", "")

        match = re.search(r"(UC[a-zA-Z0-9_-]{22})", author_url)
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
