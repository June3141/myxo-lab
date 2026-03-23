#!/usr/bin/env python3
"""Validate PR title matches the gitmoji commit format.

Usage: pr-title-lint.py "<title>"
Exit 0 on valid, 1 on invalid.
"""

import re
import sys
from pathlib import Path

TYPES = {"feat", "fix", "docs", "test", "refactor", "chore", "style", "perf"}

# Load gitmoji pattern from the hook file
_pattern_file = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "gitmoji-pattern.txt"
if _pattern_file.exists():
    _emojis = _pattern_file.read_text().strip().split("|")
else:
    # Fallback: common gitmoji set
    _emojis = ["✨", "🐛", "📝", "✅", "♻️", "🔧", "🎨", "⚡️", "🔥", "💥", "🚀", "🚧", "🔒", "⬆️", "🗃️", "🎉"]

_emoji_pattern = "|".join(re.escape(e) for e in _emojis)

# Pattern: <type>: <emoji> <lowercase subject, no trailing period>
TITLE_RE = re.compile(
    rf"^(?:{'|'.join(TYPES)}): (?:{_emoji_pattern}) [a-z].*[^.]$"
)

MAX_LENGTH = 70


def validate(title: str) -> str | None:
    """Return error message or None if valid."""
    if not title:
        return "Title is empty"
    if len(title) > MAX_LENGTH:
        return f"Title exceeds {MAX_LENGTH} characters ({len(title)})"
    if not TITLE_RE.match(title):
        return f"Title does not match format: <type>: <emoji> <subject>"
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <title>", file=sys.stderr)
        return 2

    title = sys.argv[1]
    error = validate(title)
    if error:
        print(f"❌ {error}", file=sys.stderr)
        print(f"   Got: {title!r}", file=sys.stderr)
        print(f"   Expected: <type>: <emoji> <subject>", file=sys.stderr)
        return 1

    print(f"✅ Title OK: {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
