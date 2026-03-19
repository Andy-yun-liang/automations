import os
import time
import argparse
import datetime
import feedparser
import requests
from pathlib import Path
from anthropic import Anthropic
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ------------------------
# CONFIG
# ------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN")

OBSIDIAN_VAULT = Path.home() / "Documents" / "Obsidian" / "TechTrends"
OBSIDIAN_VAULT.mkdir(parents=True, exist_ok=True)

TOPICS = [
    "agentic AI", "multi-agent workflows", "LLM automation",
    "git worktrees", "Claude Code", "AI coding tools",
    "MCP servers", "local LLMs", "RAG pipelines"
]

YOUTUBE_CHANNELS = {
    "Fireship":        "UCsBjURrPoezykLs9EqgamOA",
    "ThePrimeagen":    "UCVTlvUkGslCV_h-nSAId8Sw",
    "Matthew Berman":  "UCnUYZLuoy1rq1aVMwx4aTzw",
    "AI Explained":    "UCNJ1Ymd5yFuUPtn21xtRbbw",
    "Andrej Karpathy": "UCXUPKJO5MZQMU11wm2QEyYQ",
}

GITHUB_QUERIES = ["multi-agent AI", "agentic workflow", "MCP server LLM"]

today_str       = datetime.date.today().strftime("%Y-%m-%d")
daily_note_path = OBSIDIAN_VAULT / f"{today_str}-tech-trends.md"

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ------------------------
# FETCH: GitHub
# ------------------------
def fetch_github(max_per_query=3):
    if not GITHUB_TOKEN:
        print("  [skip] GITHUB_TOKEN not set")
        return []
    gh    = Github(auth=Auth.Token(GITHUB_TOKEN))
    items = []
    for query in GITHUB_QUERIES:
        try:
            results = gh.search_repositories(query, sort="stars", order="desc")
            for repo in results[:max_per_query]:
                items.append({
                    "title":       repo.full_name,
                    "url":         repo.html_url,
                    "description": repo.description or "",
                    "source":      "GitHub",
                })
        except Exception as e:
            print(f"  [github] error on '{query}': {e}")
    return items

# ------------------------
# FETCH: Hacker News (RSS)
# ------------------------
def fetch_hn(max_items=10):
    items = []
    try:
        feed = feedparser.parse("https://hnrss.org/frontpage?points=100")
        for entry in feed.entries[:max_items]:
            items.append({
                "title":       entry.title,
                "url":         entry.link,
                "description": entry.get("summary", "")[:400],
                "source":      "Hacker News",
            })
    except Exception as e:
        print(f"  [hn] error: {e}")
    return items

# ------------------------
# FETCH: ArXiv (RSS)
# ------------------------
def fetch_arxiv(max_items=5):
    items = []
    feeds = [
        "https://rss.arxiv.org/rss/cs.AI",
        "https://rss.arxiv.org/rss/cs.LG",
    ]
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_items]:
                items.append({
                    "title":       entry.title,
                    "url":         entry.link,
                    "description": entry.get("summary", "")[:600],
                    "source":      "ArXiv",
                })
        except Exception as e:
            print(f"  [arxiv] error on {url}: {e}")
    return items

# ------------------------
# FETCH: YouTube (RSS)
# ------------------------
def fetch_youtube(max_per_channel=2):
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

# ------------------------
# SUMMARIZE WITH CLAUDE
# ------------------------
def summarize_all(items):
    combined = "\n\n".join(
        f"[{i+1}] ({item['source']}) {item['title']}\nURL: {item['url']}\n{item['description']}"
        for i, item in enumerate(items)
    )

    prompt = f"""You are a senior engineer who curates a daily briefing on agentic programming, AI tooling, and developer trends.

Today's date: {today_str}

Below are {len(items)} raw items pulled from GitHub, Hacker News, ArXiv, and YouTube.

Your job:
1. Filter out noise — skip anything unrelated to: agentic AI, LLM tooling, developer automation, git workflows, local models, RAG, MCP, coding assistants, or emerging programming paradigms.
2. For the items that pass the filter, write a structured Markdown briefing.

Output format (Markdown):

## Daily Tech Trends — {today_str}

### TL;DR
- 3-5 bullet point summary of the most important things happening today

### Top Stories
For each relevant item:
#### [Title](url)
**Source:** ...
**Why it matters:** 1-2 sentences
**Key points:**
- bullet 1
- bullet 2
**Follow-up:** one question worth exploring

### Emerging Patterns
1-2 paragraphs on any cross-cutting themes you see across today's items.

---

Raw items:
{combined}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text

# ------------------------
# WRITE OBSIDIAN NOTE
# ------------------------
def write_note(content):
    with open(daily_note_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"date: {today_str}\n")
        f.write(f"tags: [tech-trends, agentic-ai, daily-brief]\n")
        f.write(f"sources: [GitHub, HackerNews, ArXiv, YouTube]\n")
        f.write("---\n\n")
        f.write(content)
    print(f"Note written: {daily_note_path}")

# ------------------------
# MAIN
# ------------------------
def main():
    print(f"[{today_str}] Fetching trends...")

    all_items = []
    print("  GitHub...")
    all_items += fetch_github()
    print("  Hacker News...")
    all_items += fetch_hn()
    print("  ArXiv...")
    all_items += fetch_arxiv()
    print("  YouTube...")
    all_items += fetch_youtube()

    print(f"  Fetched {len(all_items)} items total. Summarizing with Claude...")
    summary = summarize_all(all_items)

    write_note(summary)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", metavar="HH:MM", help="Wait until this time before running")
    args = parser.parse_args()

    if args.start:
        target = datetime.datetime.strptime(args.start, "%H:%M").replace(
            year=datetime.date.today().year,
            month=datetime.date.today().month,
            day=datetime.date.today().day,
        )
        wait = (target - datetime.datetime.now()).total_seconds()
        if wait > 0:
            print(f"Waiting until {args.start} ({int(wait)}s)...")
            time.sleep(wait)

    main()
