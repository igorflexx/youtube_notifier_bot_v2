import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


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

        return {
            "title": title,
            "url": url
        }

    except Exception:
        return None


# Пример структуры последнего видео для notify_job
def get_latest_video(channel_url: str) -> dict | None:
    try:
        r = requests.get(f"{channel_url}/videos?view=0&sort=p&flow=grid", headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        a_tag = soup.select_one("a#video-title")
        if not a_tag:
            return None

        video_title = a_tag["title"]
        video_url = "https://www.youtube.com" + a_tag["href"]
        published_time = datetime.utcnow().isoformat()

        return {
            "id": video_url.split("v=")[-1],
            "title": video_title,
            "url": video_url,
            "published": published_time
        }

    except Exception:
        return None
