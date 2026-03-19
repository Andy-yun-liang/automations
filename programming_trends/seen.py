import json
import datetime
from config import SEEN_FILE, today_str


def load_seen() -> dict:
    if not SEEN_FILE.exists():
        return {}
    with open(SEEN_FILE) as f:
        return json.load(f)


def save_seen(seen: dict):
    cutoff = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    seen   = {url: date for url, date in seen.items() if date >= cutoff}
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=2)


def filter_seen(items: list, seen: dict) -> list:
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    return [i for i in items if seen.get(i["url"], "") <= yesterday]


def mark_seen(items: list, seen: dict):
    for item in items:
        seen[item["url"]] = today_str
