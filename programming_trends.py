import os
import json
import datetime
from pathlib import Path
import requests
import openai
import praw  # Reddit API wrapper
from github import Github  # PyGithub

# ------------------------
# CONFIG
# ------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")
REDDIT_USER_AGENT = "agentic-tech-bot/0.1"

OBSIDIAN_VAULT = Path("/home/you/ObsidianVault")  # Update path
TOPICS = ["agentic AI", "multi-agent workflows", "automation frameworks"]

# Ensure daily folder exists
today_str = datetime.date.today().strftime("%Y-%m-%d")
daily_note_path = OBSIDIAN_VAULT / f"{today_str}-agentic-tech.md"

# ------------------------
# INITIALIZE API CLIENTS
# ------------------------
openai.api_key = OPENAI_API_KEY

# GitHub client
gh = Github(GITHUB_TOKEN)

# Reddit client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

# ------------------------
# 1. FETCH CONTENT
# ------------------------

def fetch_github_trending(query="multi-agent AI", max_items=5):
    results = gh.search_repositories(query, sort="stars", order="desc")
    repos = []
    for repo in results[:max_items]:
        repos.append({
            "title": repo.full_name,
            "url": repo.html_url,
            "description": repo.description or "",
            "source": "GitHub"
        })
    return repos

def fetch_reddit_posts(subreddit="MachineLearning", query="multi-agent", max_items=5):
    posts = []
    for submission in reddit.subreddit(subreddit).search(query, limit=max_items):
        posts.append({
            "title": submission.title,
            "url": submission.url,
            "description": submission.selftext or "",
            "source": f"Reddit/{subreddit}"
        })
    return posts

# Optional: Fetch from Brave Search API / RSS feeds here
# You can add additional fetch functions and merge results

# ------------------------
# 2. SUMMARIZE WITH GPT-4 TURBO
# ------------------------
def summarize_item(item):
    prompt = f"""
Summarize this content into JSON with:
- title
- url
- summary (2-5 bullet points)
- subtopics (2-4)
- follow_up (1-2 research questions)
- novelty (true/false)

Content:
Title: {item['title']}
URL: {item['url']}
Description: {item['description']}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    # Extract JSON output
    try:
        text_output = response.choices[0].message.content
        data = json.loads(text_output)
        return data
    except Exception as e:
        print("Failed to parse GPT output:", e)
        return None

# ------------------------
# 3. WRITE DAILY NOTE IN OBSIDIAN
# ------------------------
def write_markdown(items, path):
    with open(path, "w", encoding="utf-8") as f:
        # YAML front matter
        f.write("---\n")
        f.write(f"date: {today_str}\n")
        f.write(f"topics: {TOPICS}\n")
        f.write(f"source_count: {len(items)}\n")
        f.write("---\n\n")

        # Write each summarized item
        for item in items:
            f.write(f"## {item['title']}\n")
            f.write(f"**URL:** {item['url']}\n")
            f.write(f"**Subtopics:** {', '.join(item.get('subtopics', []))}\n")
            f.write(f"**Summary:** {'; '.join(item.get('summary', []))}\n")
            f.write(f"**Follow-up:** {'; '.join(item.get('follow_up', []))}\n")
            f.write(f"**Novelty:** {item.get('novelty', True)}\n\n")

# ------------------------
# MAIN WORKFLOW
# ------------------------
def main():
    github_items = fetch_github_trending()
    reddit_items = fetch_reddit_posts()

    all_items_raw = github_items + reddit_items
    summarized_items = []

    for item in all_items_raw:
        summary = summarize_item(item)
        if summary:
            summarized_items.append(summary)

    write_markdown(summarized_items, daily_note_path)
    print(f"Daily note written to {daily_note_path}")

if __name__ == "__main__":
    main()
