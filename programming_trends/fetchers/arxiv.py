import feedparser
import requests
from config import ARXIV_QUERIES


def fetch_arxiv(max_per_query: int = 5) -> list:
    items = []

    for query in ARXIV_QUERIES:
        try:
            resp = requests.get(
                "https://export.arxiv.org/api/query",
                params={
                    "search_query": f"abs:{query}",
                    "sortBy":       "submittedDate",
                    "sortOrder":    "descending",
                    "max_results":  max_per_query,
                },
                timeout=15,
            )
            feed = feedparser.parse(resp.text)
            for entry in feed.entries:
                items.append({
                    "title":       entry.title.replace("\n", " "),
                    "url":         entry.link,
                    "description": entry.get("summary", "")[:600],
                    "source":      "ArXiv",
                })
        except Exception as e:
            print(f"  [arxiv] error on '{query}': {e}")

    return items
