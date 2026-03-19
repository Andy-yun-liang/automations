# programming_trends

A daily briefing pipeline focused on agentic AI, LLM tooling, and developer automation. Pulls content from four sources, uses Claude to filter and summarize, then writes a structured Markdown note to an Obsidian vault.

## Pipeline

```
┌─────────────────────────────────────────────────┐
│                     FETCH                        │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────┐  ┌─────┐ │
│  │  GitHub  │  │    HN    │  │ ArXiv │  │ YT  │ │
│  │ (repos)  │  │(stories) │  │(papers│  │(RSS)│ │
│  └────┬─────┘  └────┬─────┘  └──┬────┘  └──┬──┘ │
└───────┼─────────────┼───────────┼───────────┼───┘
        └─────────────┴───────────┴───────────┘
                              │
                              ▼
                   ┌──────────────────┐
                   │   DEDUPLICATE    │
                   │  (.seen_items)   │
                   │  drop if seen    │
                   │  in last 7 days  │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │  SCORE (pass 1)  │
                   │    Claude API    │
                   │   rates 1–10     │
                   │  drops score <7  │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │SUMMARIZE (pass 2)│
                   │    Claude API    │
                   │  writes briefing │
                   │  in MD format    │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │   WRITE NOTE     │
                   │  vault/YYYY-MM-  │
                   │  DD-tech-trends  │
                   │      .md         │
                   └──────────────────┘
```

## How it works

**1. Fetch** — four sources run each day:

| Source | What it fetches | Config |
|---|---|---|
| GitHub | Top new repos by stars (last 30 days) | `GITHUB_QUERIES` in `config.py` |
| Hacker News | Stories >50 points from the last 36 hours | `HN_KEYWORDS` in `config.py` |
| ArXiv | Latest papers matching topic queries | `ARXIV_QUERIES` in `config.py` |
| YouTube | Most recent videos from tracked channels | `YOUTUBE_CHANNELS` in `config.py` |

**2. Deduplicate** — URLs seen in the last 7 days are skipped (tracked in `.seen_items.json`).

**3. Score (pass 1)** — Claude rates each item 1–10 for relevance to the configured focus areas (agentic AI, RAG, MCP, text-to-SQL, dev automation). Items scoring below 7 (`SCORE_THRESHOLD`) are dropped.

**4. Summarize (pass 2)** — Claude writes a morning briefing from the surviving items:
- **TL;DR** — 3–5 top-level bullets
- **Top Stories** — per-item breakdown with why it matters, key points, and a follow-up prompt
- **Emerging Patterns** — cross-cutting themes across today's items
- **What to Watch** — the single most important thing this week with a concrete action

**5. Write** — the note is saved to `vault/YYYY-MM-DD-tech-trends.md` with YAML frontmatter (`date`, `tags`, `sources`).

## Project structure

```
programming_trends/
├── main.py              # Orchestrates the pipeline
├── config.py            # All tunable settings (queries, channels, threshold, paths)
├── seen.py              # Deduplication — tracks seen URLs with 7-day expiry
├── writer.py            # Writes the final Markdown note with frontmatter
├── fetchers/
│   ├── github.py        # GitHub Search API via PyGithub
│   ├── hn.py            # HN Algolia search API
│   ├── arxiv.py         # ArXiv Atom feed
│   └── youtube.py       # YouTube RSS feeds (no API key needed)
└── claude/
    ├── scorer.py        # Pass 1: relevance scoring
    └── summarizer.py    # Pass 2: briefing generation
```

## Setup

1. Copy `.env.example` to `.env` and fill in your keys:
   ```
   ANTHROPIC_API_KEY=
   GITHUB_TOKEN=
   OUTPUT_DIR=/path/to/your/obsidian/vault  # optional, defaults to ~/Documents/Obsidian/TechTrends
   ```
2. Install dependencies: `pip install -r ../requirements.txt`
3. Run manually: `python3 main.py`
4. Or schedule with cron: `3 7 * * * cd /path/to/repo && python3 programming_trends/main.py >> logs/trends.log 2>&1`

## Customising

- **Add/remove topics** — edit `GITHUB_QUERIES`, `HN_KEYWORDS`, `ARXIV_QUERIES` in `config.py`
- **Add/remove YouTube channels** — edit `YOUTUBE_CHANNELS` (channel ID, not handle)
- **Raise/lower the bar** — change `SCORE_THRESHOLD` (default: 7/10)
- **Change the Claude model** — update the `model=` argument in `scorer.py` and `summarizer.py`
