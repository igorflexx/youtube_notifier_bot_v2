import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

def resolve_channel(url: str) -> str | None:
    if "youtube.com" not in url:
        return None
    if "/@" in url:
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
    # Берём настоящий RSS канал
    if channel_url.startswith("https://www.youtube.com/@"):
        username = channel_url.split("/@")[-1]
        rss_url = f"https://www.youtube.com/feeds/videos.xml?user={username}"
    else:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_url.split('/')[-1]}"

    feed = feedparser.parse(rss_url)
    if not feed.entries:
        return None

    entry = feed.entries[0]
    return {
        "id": entry.id,
        "title": entry.title,
        "url": entry.link,
        "published": entry.published
    }
