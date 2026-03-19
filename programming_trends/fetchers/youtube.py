import feedparser
from config import YOUTUBE_CHANNELS


def fetch_youtube(max_per_channel: int = 2) -> list:
    items = []

    for name, channel_id in YOUTUBE_CHANNELS.items():
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_channel]:
                items.append({
                    "title":       entry.title,
                    "url":         entry.link,
                    "description": entry.get("summary", "")[:400],
                    "source":      f"YouTube/{name}",
                })
        except Exception as e:
            print(f"  [youtube] error on {name}: {e}")

    return items
