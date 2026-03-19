# Automations

A collection of personal automation scripts for research, interests, and ideas.

## Projects

### `programming_trends/`

Fetches daily programming and agentic AI trends from across the web, scores them for relevance using Claude, and writes a summarized Markdown briefing to an Obsidian vault.

**Sources:** GitHub (new repos), Hacker News, ArXiv (RAG, text-to-SQL, agentic workflows), YouTube

**Output:** A daily `.md` note in `vault/` — structured with a TL;DR, top stories, and emerging patterns.

**Setup:**
1. Copy `.env.example` to `programming_trends/.env` and fill in your keys
2. Install dependencies: `pip install -r requirements.txt`
3. Add a cron job: `3 7 * * * cd /path/to/repo && python3 programming_trends/main.py >> logs/trends.log 2>&1`

**Required env vars:**
```
ANTHROPIC_API_KEY=
GITHUB_TOKEN=
```
