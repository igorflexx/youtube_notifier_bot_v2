import re
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def resolve_channel(url: str) -> str | None:
    url = url.strip()

    # @username
    m = re.search(r"youtube\.com/@([A-Za-z0-9._-]+)", url)
    if m:
        return f"@{m.group(1)}"

    # /channel/UCxxxx
    m = re.search(r"youtube\.com/channel/(UC[a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)

    # /c/xxxx
    m = re.search(r"youtube\.com/c/([A-Za-z0-9_-]+)", url)
    if m:
        return m.group(1)

    return None


def get_channel_info(channel: str) -> dict | None:
    if channel.startswith("@"):
        url = f"https://www.youtube.com/{channel}"
    elif channel.startswith("UC"):
        url = f"https://www.youtube.com/channel/{channel}"
    else:
        url = f"https://www.youtube.com/c/{channel}"

    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code != 200:
        return None

    # тупо, но стабильно
    m = re.search(r"<title>(.*?) - YouTube</title>", r.text)
    if not m:
        return None

    return {
        "id": channel,
        "title": m.group(1)
    }
