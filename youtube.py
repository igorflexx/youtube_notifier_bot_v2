import feedparser

def resolve_channel(url: str):
    if "channel/" in url:
        return url.split("channel/")[1].split("/")[0]
    return None  # Только прямые ссылки channel/UC...

def get_channel_info(channel_id: str):
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    if not feed.entries:
        return None, None
    name = feed.feed.title
    last_video = feed.entries[0].yt_videoid
    return name, last_video
