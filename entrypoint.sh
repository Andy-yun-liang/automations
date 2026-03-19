#!/bin/sh
set -e

echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="

cd /app/programming_trends
python3 main.py

