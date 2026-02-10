import os
import requests

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyA-XsN9O9dQa3ZgnoIReE9buTov4mEvqsY")

def resolve_channel(url: str):
    """Возвращает channel_id по ссылке канала, поддерживает /channel/ID, /@handle и /c/"""
    # Прямой ID
    if "channel/" in url:
        return url.split("channel/")[1].split("/")[0]

    # @handle или кастомный URL
    handle = None
    if "/@" in url:
        handle = url.split("/@")[1].split("/")[0]
    elif "/c/" in url:
        handle = url.split("/c/")[1].split("/")[0]

    if handle:
        # Запрос к API: поиск по username/handle
        params = {
            "part": "id",
            "forUsername": handle,
            "key": YOUTUBE_API_KEY
        }
        # сначала пробуем как forUsername
        r = requests.get("https://www.googleapis.com/youtube/v3/channels", params=params).json()
        if "items" in r and r["items"]:
            return r["items"][0]["id"]

        # иначе ищем через search
        params_search = {
            "part": "snippet",
            "q": handle,
            "type": "channel",
            "key": YOUTUBE_API_KEY
        }
        r2 = requests.get("https://www.googleapis.com/youtube/v3/search", params=params_search).json()
        if "items" in r2 and r2["items"]:
            return r2["items"][0]["snippet"]["channelId"]

    return None

def get_channel_info(channel_id: str):
    """Возвращает (channel_name, last_video_id)"""
    params = {
        "part": "snippet,contentDetails",
        "id": channel_id,
        "key": YOUTUBE_API_KEY
    }
    r = requests.get("https://www.googleapis.com/youtube/v3/channels", params=params).json()
    if "items" not in r or not r["items"]:
        return None, None

    name = r["items"][0]["snippet"]["title"]
    uploads_playlist = r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Получаем последнее видео через playlistItems
    params_videos = {
        "part": "snippet",
        "playlistId": uploads_playlist,
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    }
    r2 = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params=params_videos).json()
    if "items" not in r2 or not r2["items"]:
        return name, None

    last_video_id = r2["items"][0]["snippet"]["resourceId"]["videoId"]
    return name, last_video_id
