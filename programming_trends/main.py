import time
import argparse
import datetime
import sys
from pathlib import Path

# allow imports from this package directory
sys.path.insert(0, str(Path(__file__).parent))

from config import today_str
from seen import load_seen, save_seen, filter_seen, mark_seen
from fetchers import fetch_github, fetch_hn, fetch_arxiv, fetch_youtube
from claude import score_items, summarize_items
from writer import write_note


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

    before     = len(all_items)
    all_items  = filter_seen(all_items, seen)
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
