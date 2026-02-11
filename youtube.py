import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

def resolve_channel(url: str) -> str | None:
    """Возвращает ID или ссылку канала, если ссылка корректная."""
    if "youtube.com" not in url:
        return None
    if "/@" in url:
        return url.rstrip("/")
    if "/channel/" in url:
        return url.rstrip("/")
    return None

def get_channel_info(channel_url: str) -> dict | None:
    """Получает название и ссылку на канал через og:meta теги."""
    try:
        r = requests.get(channel_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        og_title = soup.find("meta", property="og:title")
        og_url = soup.find("meta", property="og:url")
        if not og_title or not og_url:
            return None
        title = og_title["content"].replace(" - YouTube", "").strip()
        url = og_url["content"]
        return {"title": title, "url": url}
    except Exception:
        return None

def get_latest_video(channel_url: str) -> dict | None:
    """Возвращает последнее видео канала через RSS."""
    try:
        # Поддержка каналов с /channel/ID и /@username
        if "/channel/" in channel_url:
            channel_id = channel_url.split("/channel/")[-1]
        elif "/@" in channel_url:
            channel_id = channel_url.split("/@")[-1]
        else:
            return None

        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}" if "/channel/" in channel_url else None
        if not rss_url:
            # Для @username сначала нужно получить реальный канал
            info = get_channel_info(channel_url)
            if not info:
                return None
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={resolve_channel(info['url']).split('/')[-1]}"

        feed = feedparser.parse(rss_url)
        if not feed.entries:
            return None
        entry = feed.entries[0]
        # Преобразуем published в isoformat для хранения
        try:
            published = datetime(*entry.published_parsed[:6]).isoformat()
        except Exception:
            published = datetime.utcnow().isoformat()
        return {
            "id": entry.link.split("/")[-1],
            "title": entry.title,
            "url": entry.link,
            "published": published
        }
    except Exception:
        return None
