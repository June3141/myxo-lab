#!/usr/bin/env bash
# Commit gate — validate message format and commit size
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only intercept git commit commands
if ! echo "$COMMAND" | grep -qE '\bgit\s+commit\b'; then
  exit 0
fi

# --- 1. Commit message validation ---
COMMIT_MSG=$(echo "$COMMAND" | grep -oP '(?<=-m\s")[^"]*' || echo "$COMMAND" | grep -oP "(?<=-m\s')[^']*" || true)

# Also handle heredoc format: -m "$(cat <<'EOF' ... EOF )"
if [[ -z "$COMMIT_MSG" ]]; then
  COMMIT_MSG=$(echo "$COMMAND" | sed -n "s/.*<<'EOF'[[:space:]]*//p" | sed '/^EOF/d' | head -1 || true)
fi

if [[ -n "$COMMIT_MSG" ]]; then
  SUBJECT=$(echo "$COMMIT_MSG" | head -1 | sed 's/^[[:space:]]*//')

  # Validate gitmoji + scope format
  GITMOJI_FILE=".claude/hooks/gitmoji-pattern.txt"
  if [[ -f "$GITMOJI_FILE" ]]; then
    EMOJIS=$(cat "$GITMOJI_FILE")
  else
    EMOJIS='✨|🐛|📝|✅|♻️|🔧|🎨|⚡️|🔥|💥|🚀|🚧|🔒|⬆️|🗃️|🎉'
  fi
  TYPES='feat|fix|docs|test|refactor|chore|style|perf'
  GITMOJI_PATTERN="^($TYPES): ($EMOJIS) .+$"
  if ! echo "$SUBJECT" | grep -qP "$GITMOJI_PATTERN"; then
    echo '{"decision":"block","reason":"Commit message must match type: emoji subject format: e.g. feat: ✨ add health check endpoint"}'
    exit 2
  fi

  # Reject Japanese characters in subject
  if echo "$SUBJECT" | grep -qP '[\p{Hiragana}\p{Katakana}\p{Han}]'; then
    echo '{"decision":"block","reason":"Commit message subject must be in English (no Japanese characters)"}'
    exit 2
  fi
fi

# --- 2. Commit size validation ---
EXCLUDE_PATTERN='(\.test\.|_test\.py|tests/|\.lock$)'
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null | grep -v -E "$EXCLUDE_PATTERN" | wc -l | tr -d ' ')
TOTAL_LINES=$(git diff --cached --numstat 2>/dev/null | grep -v -E "$EXCLUDE_PATTERN" | awk '{s+=$1+$2} END {print s+0}')

SIZE_WARN=""
if [[ "$STAGED_FILES" -gt 10 ]]; then
  SIZE_WARN+="Staged files ($STAGED_FILES) exceed limit of 10. "
fi
if [[ "$TOTAL_LINES" -gt 300 ]]; then
  SIZE_WARN+="Changed lines ($TOTAL_LINES) exceed limit of 300. "
fi

if [[ -n "$SIZE_WARN" ]]; then
  echo '{"decision":"block","reason":"Commit too large: '"$SIZE_WARN"'Split into smaller commits."}'
  exit 2
fi

exit 0
