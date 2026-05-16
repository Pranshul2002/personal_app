#!/usr/bin/env bash
# run.sh — called automatically by the Mac watcher (or run manually).
#
# Usage:
#   ./run.sh [days]          # days defaults to 1
#
# Expects export.zip to be at:
#   ~/Library/Mobile Documents/com~apple~CloudDocs/HealthExports/export.zip
# (the folder your iOS Shortcut saves to)
#
# Saves a dated report to ~/HealthData/YYYY-MM-DD.txt

set -euo pipefail

DAYS="${1:-1}"
EXPORT_FILE="$HOME/Library/Mobile Documents/com~apple~CloudDocs/HealthExports/export.zip"
OUTPUT_DIR="$HOME/HealthData"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$EXPORT_FILE" ]; then
    echo "[health-analyzer] No export found at: $EXPORT_FILE" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
OUTPUT_FILE="$OUTPUT_DIR/$(date +%Y-%m-%d).txt"

echo "[health-analyzer] Running analysis (last $DAYS day(s))..."
python3 "$SCRIPT_DIR/analyze.py" "$EXPORT_FILE" "$DAYS" -o "$OUTPUT_FILE"
echo "[health-analyzer] Done — report at $OUTPUT_FILE"
