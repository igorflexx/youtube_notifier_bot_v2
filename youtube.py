import requests
from bs4 import BeautifulSoup
from datetime import datetime

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

# 🔹 Пример функции для получения последнего видео
def get_latest_video(channel_url: str) -> dict | None:
    # Здесь можно подключить API YouTube или парсер RSS канала
    # Возвращает словарь: {"id": video_id, "title": title, "published": iso_date, "url": video_url}
    # Для теста можно вернуть заглушку
    return {
        "id": "test_id",
        "title": "Тестовое видео",
        "published": datetime.utcnow().isoformat(),
        "url": f"{channel_url}/video/test_id"
    }
