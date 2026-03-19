import datetime
import requests
from config import HN_KEYWORDS


def fetch_hn(max_per_keyword: int = 3) -> list:
    since     = int((datetime.datetime.now() - datetime.timedelta(hours=36)).timestamp())
    seen_urls = set()
    items     = []

    for keyword in HN_KEYWORDS:
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={
                    "query":          keyword,
                    "tags":           "story",
                    "numericFilters": f"created_at_i>{since},points>50",
                    "hitsPerPage":    max_per_keyword,
                },
                timeout=10,
            )
            for hit in resp.json().get("hits", []):
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                items.append({
                    "title":       hit.get("title", ""),
                    "url":         url,
                    "description": f"Points: {hit.get('points', 0)} | Comments: {hit.get('num_comments', 0)}",
                    "source":      "Hacker News",
                })
        except Exception as e:
            print(f"  [hn] error on '{keyword}': {e}")

    return items
