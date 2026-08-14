#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PORT="${PORT:-8011}"
OUTPUT_DIR="$ROOT_DIR/docs/screenshots"
PROFILE_DIR="$(mktemp -d)"

mkdir -p "$OUTPUT_DIR"
cd "$ROOT_DIR"
"$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" >"$PROFILE_DIR/server.log" 2>&1 &
SERVER_PID=$!
cleanup(){ kill "$SERVER_PID" 2>/dev/null || true; rm -rf "$PROFILE_DIR"; }
trap cleanup EXIT

for _ in {1..40}; do
  curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null && break
  sleep 0.25
done

"$CHROME_BIN" --headless=new --hide-scrollbars --disable-software-rasterizer \
  --user-data-dir="$PROFILE_DIR/desktop" --window-size=1440,1100 \
  --screenshot="$OUTPUT_DIR/dashboard-desktop.png" "http://127.0.0.1:$PORT/"
"$CHROME_BIN" --headless=new --hide-scrollbars --disable-software-rasterizer \
  --user-data-dir="$PROFILE_DIR/mobile" --window-size=430,930 \
  --screenshot="$OUTPUT_DIR/dashboard-mobile.png" "http://127.0.0.1:$PORT/"

echo "Screenshots written to $OUTPUT_DIR"

