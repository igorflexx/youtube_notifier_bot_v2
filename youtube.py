import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

def resolve_channel(url: str) -> str | None:
    if "youtube.com" not in url:
        return None
    # Полная поддержка разных форматов ссылок
    if "/@" in url or "/channel/" in url or "/c/" in url:
        return url.rstrip("/")
    return None

def get_channel_info(channel_url: str) -> dict | None:
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
    try:
        # Получаем RSS через feedparser
        if "/channel/" in channel_url:
            channel_id = channel_url.split("/channel/")[-1]
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        else:
            # Для @username или /c/ используем HTML парсинг
            feed_url = channel_url + "/videos?flow=grid&view=0&sort=p"
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            return None
        entry = feed.entries[0]
        video_id = entry.link.split("/")[-1]
        return {
            "id": video_id,
            "title": entry.title,
            "url": entry.link,
            "published": entry.published
        }
    except Exception:
        return None
