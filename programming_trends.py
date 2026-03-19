import os
import json
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

SEEN_FILE = Path(__file__).parent / ".seen_items.json"

YOUTUBE_CHANNELS = {
    "Fireship":        "UCsBjURrPoezykLs9EqgamOA",
    "ThePrimeagen":    "UCVTlvUkGslCV_h-nSAId8Sw",
    "Matthew Berman":  "UCnUYZLuoy1rq1aVMwx4aTzw",
    "AI Explained":    "UCNJ1Ymd5yFuUPtn21xtRbbw",
    "Andrej Karpathy": "UCXUPKJO5MZQMU11wm2QEyYQ",
}

GITHUB_QUERIES = ["multi-agent AI", "agentic workflow", "MCP server LLM"]

HN_KEYWORDS = [
    "agent", "MCP", "LLM", "Claude", "worktree", "RAG",
    "local model", "copilot", "automation", "sql"
]

ARXIV_QUERIES = [
    "RAG retrieval augmented generation",
    "text to sql",
    "agentic workflow LLM",
]

SCORE_THRESHOLD = 7  # items below this are dropped before summarization

today_str       = datetime.date.today().strftime("%Y-%m-%d")
daily_note_path = OBSIDIAN_VAULT / f"{today_str}-tech-trends.md"

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ------------------------
# SEEN TRACKER
# ------------------------
def load_seen() -> dict:
    if not SEEN_FILE.exists():
        return {}
    with open(SEEN_FILE) as f:
        return json.load(f)

def save_seen(seen: dict):
    # purge entries older than 7 days
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

# ------------------------
# FETCH: GitHub
# ------------------------
def fetch_github(max_per_query=5):
    if not GITHUB_TOKEN:
        print("  [skip] GITHUB_TOKEN not set")
        return []
    gh         = Github(auth=Auth.Token(GITHUB_TOKEN))
    since      = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    items      = []
    for query in GITHUB_QUERIES:
        try:
            full_query = f"{query} created:>{since}"
            results    = gh.search_repositories(full_query, sort="stars", order="desc")
            for repo in results[:max_per_query]:
                items.append({
                    "title":       repo.full_name,
                    "url":         repo.html_url,
                    "description": (repo.description or "") + f" | ⭐ {repo.stargazers_count}",
                    "source":      "GitHub",
                })
        except Exception as e:
            print(f"  [github] error on '{query}': {e}")
    return items

# ------------------------
# FETCH: Hacker News (Algolia API)
# ------------------------
def fetch_hn(max_per_keyword=3):
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

# ------------------------
# FETCH: ArXiv (API, abstracts only)
# ------------------------
def fetch_arxiv(max_per_query=5):
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
# PASS 1: Score relevance with Claude
# ------------------------
def score_items(items: list) -> list:
    numbered = "\n\n".join(
        f"[{i+1}] ({item['source']}) {item['title']}\n{item['description'][:200]}"
        for i, item in enumerate(items)
    )

    prompt = f"""You are filtering a daily tech briefing for a senior engineer focused on:
- Agentic AI / multi-agent workflows
- LLM tooling (MCP, RAG, Claude, local models)
- Developer automation and coding assistants
- Text-to-SQL
- Git workflows and emerging dev paradigms

Rate each item 1–10 for relevance to these topics. Be strict — generic tech news, unrelated ML research, or non-developer content should score 1–4.

Return ONLY a JSON array like:
[{{"index": 1, "score": 8}}, {{"index": 2, "score": 3}}, ...]

Items:
{numbered}
"""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        text   = resp.content[0].text
        start  = text.index("[")
        end    = text.rindex("]") + 1
        scores = json.loads(text[start:end])
        score_map = {s["index"]: s["score"] for s in scores}
        for i, item in enumerate(items):
            item["score"] = score_map.get(i + 1, 0)
        kept = [item for item in items if item["score"] >= SCORE_THRESHOLD]
        print(f"  Scored {len(items)} items → {len(kept)} passed threshold ({SCORE_THRESHOLD}+)")
        return kept
    except Exception as e:
        print(f"  [score] parse error: {e} — passing all items through")
        return items

# ------------------------
# PASS 2: Summarize with Claude
# ------------------------
def summarize_items(items: list) -> str:
    combined = "\n\n".join(
        f"[{i+1}] ({item['source']}) score={item.get('score','?')} {item['title']}\nURL: {item['url']}\n{item['description']}"
        for i, item in enumerate(items)
    )

    prompt = f"""You are a senior engineer writing a daily morning briefing on agentic programming, LLM tooling, and developer trends.

Today: {today_str}

All items below have already been scored ≥{SCORE_THRESHOLD}/10 for relevance — do not re-filter, summarize everything.

Output format (Markdown):

## Daily Tech Trends — {today_str}

### TL;DR
- 3–5 bullets on the most important things happening today

### Top Stories
For each item:
#### [Title](url)
**Source:** ... | **Relevance score:** X/10
**Why it matters:** 1–2 sentences
**Key points:**
- bullet 1
- bullet 2
**Follow-up:** one question worth exploring

### Emerging Patterns
1–2 paragraphs on cross-cutting themes across today's items.

---

Items:
{combined}
"""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text

# ------------------------
# WRITE OBSIDIAN NOTE
# ------------------------
def write_note(content: str):
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
    seen = load_seen()

    all_items = []
    print("  GitHub...")
    all_items += fetch_github()
    print("  Hacker News...")
    all_items += fetch_hn()
    print("  ArXiv...")
    all_items += fetch_arxiv()
    print("  YouTube...")
    all_items += fetch_youtube()

    before = len(all_items)
    all_items = filter_seen(all_items, seen)
    print(f"  {before} items fetched → {len(all_items)} after removing already-seen")

    if not all_items:
        print("  Nothing new today.")
        return

    print(f"  Scoring {len(all_items)} items with Claude (pass 1)...")
    all_items = score_items(all_items)

    if not all_items:
        print("  No items passed the relevance threshold.")
        return

    print(f"  Summarizing {len(all_items)} items with Claude (pass 2)...")
    summary = summarize_items(all_items)

    write_note(summary)

    mark_seen(all_items, seen)
    save_seen(seen)

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
