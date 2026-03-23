#!/bin/sh
set -e

cd /app

echo "Watching /app/vault for new markdown files..."

inotifywait -m /app/vault -e close_write,moved_to |
while read -r dir events file; do
    case "$file" in
        *.md)
            echo "=== $(date '+%Y-%m-%d %H:%M:%S') New file: $file ==="
            git add vault/"$file"
            if git diff --cached --quiet; then
                echo "No changes to commit."
            else
                git commit -m "Daily briefing $(date '+%Y-%m-%d')"
                git push
                echo "Pushed $file to GitHub."
            fi
            ;;
    esac
done
