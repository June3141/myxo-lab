"""CachedGitHubMCP - TTL-based request caching for GitHub MCP."""

from __future__ import annotations

import time
from typing import Any


class CachedGitHubMCP:
    """TTL-based cache to reduce GitHub API calls.

    Stores values in a dict with timestamps. Expired entries are
    lazily evicted on the next :meth:`get` call and the caller-supplied
    *default* (``None`` when omitted) is returned instead.
    """

    _MISSING = object()

    def __init__(self, ttl: int = 300) -> None:
        """Initialize cache with TTL in seconds."""
        if ttl <= 0:
            raise ValueError(f"ttl must be positive, got {ttl}")
        self.ttl = ttl
        self._cache: dict[str, tuple[float, Any]] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Return cached value if present and not expired.

        If the key is missing or its TTL has expired, return *default*
        (``None`` when the argument is omitted).  Expired entries are
        deleted from the internal store on access.
        """
        if key not in self._cache:
            return default
        timestamp, value = self._cache[key]
        if time.monotonic() - timestamp > self.ttl:
            del self._cache[key]
            return default
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
        sentinel = object()
        return self.get(key, sentinel) is not sentinel
