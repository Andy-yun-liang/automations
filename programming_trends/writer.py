from config import daily_note_path, today_str


def write_note(content: str):
    with open(daily_note_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"date: {today_str}\n")
        f.write(f"tags: [tech-trends, agentic-ai, daily-brief]\n")
        f.write(f"sources: [GitHub, HackerNews, ArXiv, YouTube]\n")
        f.write("---\n\n")
        f.write(content)
    print(f"Note written: {daily_note_path}")
