# Automations

This repo started as a curiosity: I was looking at [OpenClaw](https://openclaw.ai/) — an open-source AI assistant that wraps Claude — and wondered how much the orchestration layer would actually cost compared to a lean, purpose-built automation doing the same job.

## The Question

OpenClaw is free and open-source, but you still pay for the underlying Claude API calls. The problem is that orchestration frameworks add significant token overhead on every call: large system prompts, workspace context injection, tool schema definitions, memory handling, etc. For a simple daily automation, that overhead might cost more than the actual work being done.

## The Experiment

`programming_trends/` is the automation I used to benchmark this. It fetches daily AI/programming trends, scores them with Claude, and writes a markdown briefing to an Obsidian vault — exactly **2 API calls per day**.

**Current cost (lean, direct API): ~$0.08/day**

**Estimated cost through OpenClaw:**
- OpenClaw injects ~10,500–60,500 tokens of overhead per call (system prompt + workspace bootstrap files + tool schemas)
- With 2 calls/day, that's ~21,000–121,000 extra input tokens daily
- Estimated total: **~$0.14–$0.44/day** (1.75x–5.5x more expensive)

The dominant variable is workspace context — if you have large `MEMORY.md` / `CLAUDE.md` files, OpenClaw re-injects them on every single call (up to 150,000 chars / ~37,500 tokens).

## Conclusion

For a focused, single-purpose automation, building direct against the API is significantly cheaper than routing through an orchestration layer. OpenClaw makes sense when you need its features (memory, browser control, multi-platform messaging). For a daily cron script, it's overhead you're paying for but not using.

---

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

See [`programming_trends/README.md`](programming_trends/README.md) for full details.
