import requests
import re
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def resolve_channel(url: str):
    match = re.search(r"youtube\.com/@([\w\-]+)", url)
    if not match:
        return None
    return match.group(1)


def get_channel_info(handle: str):
    url = f"https://www.youtube.com/@{handle}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return None

    title_match = re.search(r'"title":"([^"]+)"', r.text)
    if not title_match:
        return None

    return {
        "id": handle,
        "title": title_match.group(1),
    }


def get_latest_video(handle: str):
    url = f"https://www.youtube.com/@{handle}/videos"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return None

    match = re.search(r'"videoId":"([^"]+)".+?"title":{"runs":\[{"text":"([^"]+)"}].+?"publishedTimeText":{"simpleText":"([^"]+)"}', r.text)
    if not match:
        return None

    video_id, title, published = match.groups()

    return {
        "id": video_id,
        "title": title,
        "published": datetime.utcnow().isoformat(),
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }
