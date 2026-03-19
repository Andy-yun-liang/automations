import os
import datetime
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN")

OBSIDIAN_VAULT = Path.home() / "Documents" / "Obsidian" / "TechTrends"
OBSIDIAN_VAULT.mkdir(parents=True, exist_ok=True)

SEEN_FILE = Path(__file__).parent / ".seen_items.json"

SCORE_THRESHOLD = 7

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
    "local model", "copilot", "automation", "sql",
]

ARXIV_QUERIES = [
    "RAG retrieval augmented generation",
    "text to sql",
    "agentic workflow LLM",
]

today_str       = datetime.date.today().strftime("%Y-%m-%d")
daily_note_path = OBSIDIAN_VAULT / f"{today_str}-tech-trends.md"

client = Anthropic(api_key=ANTHROPIC_API_KEY)
