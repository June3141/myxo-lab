"""ContextSanitizer — detect and redact secrets before sending to LLM."""

from __future__ import annotations

import re
from typing import ClassVar


class ContextSanitizer:
    """Scans text for common secret patterns and replaces them with redaction markers."""

    # Patterns that use a simple full-match replacement.
    _PATTERNS: ClassVar[list[tuple[str, re.Pattern[str]]]] = [
        (
            "aws-access-key",
            re.compile(r"AKIA[0-9A-Z]{16}"),
        ),
        (
            "private-key",
            re.compile(
                r"-----BEGIN\s[\w\s]*PRIVATE\sKEY-----"
                r"[\s\S]*?"
                r"-----END\s[\w\s]*PRIVATE\sKEY-----"
            ),
        ),
        (
            "jwt",
            re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
        ),
        (
            "github-token",
            re.compile(
                r"(?:github_pat_[A-Za-z0-9_]{22,}"
                r"|gh[psourx]_[A-Za-z0-9_]{36,})"
            ),
        ),
    ]

    # Patterns where only the *value* should be redacted (key name is preserved).
    # Each tuple: (label, compiled pattern with a ``value`` named group).
    _KEY_VALUE_PATTERNS: ClassVar[list[tuple[str, re.Pattern[str]]]] = [
        (
            "aws-secret-key",
            re.compile(
                r"(?P<key>(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)"
                r"\s*[=:]\s*)"
                r"(?P<value>[A-Za-z0-9/+=]{40})"
            ),
        ),
        (
            "password",
            re.compile(
                r"(?P<key>\bpassword\b\s*=\s*)"
                r"(?P<value>['\"][^'\"]+['\"])"
            ),
        ),
        (
            "api-key",
            re.compile(
                r"(?P<key>\bapi[_-]?(?:key|secret)\b\s*[=:]\s*)"
                r"(?P<value>['\"][^'\"]+['\"]|[^\s,;'\"]+)",
                re.IGNORECASE,
            ),
        ),
    ]

    def sanitize(self, text: str) -> str:
        """Replace detected secrets with ``[REDACTED:<type>]`` markers."""
        result = text
        for label, pattern in self._PATTERNS:
            result = pattern.sub(f"[REDACTED:{label}]", result)
        for label, pattern in self._KEY_VALUE_PATTERNS:
            result = pattern.sub(
                rf"\g<key>[REDACTED:{label}]",
                result,
            )
        return result

    def has_secrets(self, text: str) -> bool:
        """Return ``True`` if *text* contains any recognised secret pattern."""
        return any(pattern.search(text) for _, pattern in self._PATTERNS) or any(
            pattern.search(text) for _, pattern in self._KEY_VALUE_PATTERNS
        )
