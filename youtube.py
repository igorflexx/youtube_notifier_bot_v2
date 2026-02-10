import feedparser

def resolve_channel(url: str):
    """
    Возвращает channel_id по ссылке канала.
    Поддерживает /channel/ID и /@handle через RSS.
    """
    if "channel/" in url:
        return url.split("channel/")[1].split("/")[0]

    if "/@" in url:
        handle = url.split("/@")[1].split("/")[0]
        # Попробуем получить feed RSS напрямую
        feed_url = f"https://www.youtube.com/feeds/videos.xml?user={handle}"
        feed = feedparser.parse(feed_url)
        if feed.entries:
            return feed.feed.id.split(":")[-1]  # Вытаскиваем channelId из feed.feed.id
        # Если не получилось через user, пробуем через handle (редирект)
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel=@{handle}"
        feed = feedparser.parse(feed_url)
        if feed.entries:
            return feed.feed.id.split(":")[-1]

    return None

def get_channel_info(channel_id: str):
    """
    Возвращает (channel_name, last_video_id)
    """
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    if not feed.entries:
        return None, None

    name = feed.feed.title
    last_video = feed.entries[0].yt_videoid
    return name, last_video
