#!/usr/bin/env bash
# install_watcher.sh — one-time setup for the Mac launchd watcher.
# Run this once from the apple_health_analyzer directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.healthanalyzer.watcher.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.healthanalyzer.watcher.plist"
WATCH_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/HealthExports"
DAYS="${1:-1}"

echo "=== Apple Health Analyzer — watcher setup ==="
echo

# 1. Create the iCloud watch folder
mkdir -p "$WATCH_DIR"
echo "[ok] Watch folder: $WATCH_DIR"

# 2. Stamp the real paths into the plist
sed \
    -e "s|/PLACEHOLDER/path/to/apple_health_analyzer|$SCRIPT_DIR|g" \
    -e "s|/PLACEHOLDER/Users/YOUR_USERNAME|$HOME|g" \
    -e "s|<string>1</string>  <!-- days argument -->|<string>$DAYS</string>|" \
    "$PLIST_SRC" > "$PLIST_DST"
echo "[ok] Plist written to: $PLIST_DST"

# 3. Make run.sh executable
chmod +x "$SCRIPT_DIR/run.sh"
echo "[ok] run.sh is executable"

# 4. Load the agent
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
echo "[ok] launchd agent loaded"

echo
echo "Setup complete!"
echo
echo "Next steps:"
echo "  1. Follow the iOS Shortcut guide in README.md to set up the iPhone export."
echo "  2. Each time a new export.zip lands in iCloud, run.sh fires automatically."
echo "  3. Reports are saved to: $HOME/HealthData/YYYY-MM-DD.txt"
echo "  4. Live log: tail -f /tmp/healthanalyzer.log"
