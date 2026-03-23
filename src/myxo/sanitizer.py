"""ContextSanitizer — detect and redact secrets before sending to LLM."""

from __future__ import annotations

import re
from typing import ClassVar


class ContextSanitizer:
    """Scans text for common secret patterns and replaces them with redaction markers."""

    _PATTERNS: ClassVar[list[tuple[str, re.Pattern[str]]]] = [
        (
            "aws-access-key",
            re.compile(r"AKIA[0-9A-Z]{16}"),
        ),
        (
            "aws-secret-key",
            re.compile(
                r"(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)"
                r"\s*[=:]\s*"
                r"([A-Za-z0-9/+=]{40})"
            ),
        ),
        (
            "private-key",
            re.compile(r"-----BEGIN\s[\w\s]*PRIVATE\sKEY-----"),
        ),
        (
            "jwt",
            re.compile(
                r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"
            ),
        ),
        (
            "github-token",
            re.compile(r"gh[ps]_[A-Za-z0-9_]{36,}"),
        ),
        (
            "password",
            re.compile(r"password\s*=\s*['\"][^'\"]+['\"]"),
        ),
    ]

    def sanitize(self, text: str) -> str:
        """Replace detected secrets with ``[REDACTED:<type>]`` markers."""
        result = text
        for label, pattern in self._PATTERNS:
            result = pattern.sub(f"[REDACTED:{label}]", result)
        return result

    def has_secrets(self, text: str) -> bool:
        """Return ``True`` if *text* contains any recognised secret pattern."""
        return any(pattern.search(text) for _, pattern in self._PATTERNS)
