import json
from config import client, SCORE_THRESHOLD


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

Rate each item 1–10 for relevance. Be strict — generic tech news, unrelated ML research, or non-developer content should score 1–4.

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
        text      = resp.content[0].text
        scores    = json.loads(text[text.index("["):text.rindex("]") + 1])
        score_map = {s["index"]: s["score"] for s in scores}
        for i, item in enumerate(items):
            item["score"] = score_map.get(i + 1, 0)
        kept = [item for item in items if item["score"] >= SCORE_THRESHOLD]
        print(f"  Scored {len(items)} items → {len(kept)} passed threshold ({SCORE_THRESHOLD}+)")
        return kept
    except Exception as e:
        print(f"  [scorer] parse error: {e} — passing all items through")
        return items
