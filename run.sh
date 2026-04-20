#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/controlplane/automations"
SCRIPT_DIR="$REPO_DIR/programming_trends"
LOG_FILE="$REPO_DIR/run.log"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE"

cd "$SCRIPT_DIR"
python3 main.py >> "$LOG_FILE" 2>&1

cd "$REPO_DIR"
git add vault/
if git diff --cached --quiet; then
    echo "No new notes to commit." >> "$LOG_FILE"
else
    git commit -m "Daily briefing $(date '+%Y-%m-%d')" >> "$LOG_FILE" 2>&1
fi
if git log origin/main..HEAD --oneline | grep -q .; then
    git push >> "$LOG_FILE" 2>&1
    echo "Pushed to GitHub." >> "$LOG_FILE"
else
    echo "Nothing to push." >> "$LOG_FILE"
fi
