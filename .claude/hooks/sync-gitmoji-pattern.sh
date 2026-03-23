#!/usr/bin/env bash
# Fetch gitmoji list from upstream and generate a regex pattern file.
# Output: .claude/hooks/gitmoji-pattern.txt (single-line regex alternation)
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

URL="https://raw.githubusercontent.com/carloscuesta/gitmoji/refs/heads/master/packages/gitmojis/src/gitmojis.json"
OUT=".claude/hooks/gitmoji-pattern.txt"

EMOJIS=$(curl -fsSL "$URL" | jq -r '.gitmojis[].emoji' | paste -sd '|' -)

if [[ -z "$EMOJIS" ]]; then
  echo "ERROR: Failed to fetch or parse gitmoji list" >&2
  exit 1
fi

echo "$EMOJIS" > "$OUT"
echo "Updated $OUT ($(echo "$EMOJIS" | tr '|' '\n' | wc -l | tr -d ' ') emojis)"
