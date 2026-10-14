#!/usr/bin/env bash
# Start the live dashboard server if not running, then open it in the Windows browser.
PORT="${DASH_PORT:-8765}"
DIR="$(cd "$(dirname "$0")" && pwd)"
if ! curl -s -o /dev/null "localhost:$PORT"; then
  nohup python3 "$DIR/build.py" --serve --port "$PORT" >/dev/null 2>&1 &
  for _ in $(seq 20); do curl -s -o /dev/null "localhost:$PORT" && break; sleep 0.25; done
fi
/mnt/c/Windows/explorer.exe "http://localhost:$PORT" 2>/dev/null || xdg-open "http://localhost:$PORT" 2>/dev/null
echo "http://localhost:$PORT"
