from config import client, SCORE_THRESHOLD, today_str


def summarize_items(items: list) -> str:
    combined = "\n\n".join(
        f"[{i+1}] ({item['source']}) score={item.get('score', '?')} {item['title']}\nURL: {item['url']}\n{item['description']}"
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
