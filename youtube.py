import feedparser

def resolve_channel(url: str):
    if "channel/" in url:
        return url.split("channel/")[1].split("/")[0]
    raise ValueError("Невозможно определить channel_id")

def get_channel_info(channel_id: str):
    feed = feedparser.parse(
        f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    )
    if not feed.feed:
        return None
    return {
        "title": feed.feed.title,
        "link": feed.feed.link
    }

def get_last_video(channel_id: str):
    feed = feedparser.parse(
        f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    )
    if not feed.entries:
        return None
    return feed.entries[0]
