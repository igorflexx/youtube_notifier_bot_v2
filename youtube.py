import re
import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime

YOUTUBE_CHANNEL_RE = r"(?:https?://)?(?:www\.)?youtube\.com/(?:channel/|@)?([A-Za-z0-9_-]+)"

def resolve_channel(url):
    match = re.search(YOUTUBE_CHANNEL_RE, url)
    if not match:
        return None
    return match.group(1)

def get_channel_info(cid):
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")
    if not feed.entries:
        return (cid, None)
    name = feed.feed.title
    last_video = feed.entries[0].published
    last_dt = datetime(*feed.entries[0].published_parsed[:6])
    return (name, last_dt)
