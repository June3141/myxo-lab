"""CachedGitHubMCP - TTL-based request caching for GitHub MCP."""

from __future__ import annotations

import time
from typing import Any


class CachedGitHubMCP:
    """TTL-based cache to reduce GitHub API calls.

    Stores values in a dict with timestamps. Expired entries are
    returned as None (lazy expiration).
    """

    def __init__(self, ttl: int = 300) -> None:
        """Initialize cache with TTL in seconds."""
        self.ttl = ttl
        self._cache: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """Return cached value if present and not expired, else None."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        timestamp, value = entry
        if time.monotonic() - timestamp > self.ttl:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache with the current timestamp."""
        self._cache[key] = (time.monotonic(), value)

    def invalidate(self, key: str) -> None:
        """Remove a specific key from the cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        self._cache.clear()

    def is_cached(self, key: str) -> bool:
        """Return True if the key exists and has not expired."""
        return self.get(key) is not None
