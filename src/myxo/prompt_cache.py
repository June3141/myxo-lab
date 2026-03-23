"""Claude prompt caching manager.

Adds cache_control markers to immutable content (e.g. Ship's Log, Skills)
so that the Anthropic API can cache prompt prefixes and reduce costs by ~90%.
"""

from __future__ import annotations

import copy
import hashlib
from typing import Any


class PromptCacheManager:
    """Manages prompt caching by injecting cache_control into messages.

    Args:
        cacheable_prefixes: List of content prefixes that identify immutable,
            cacheable content (e.g. ["Ship's Log", "Skills"]).
        max_history: Maximum number of content hashes to track. When exceeded,
            the set is cleared to prevent unbounded memory growth.
    """

    def __init__(
        self,
        cacheable_prefixes: list[str],
        max_history: int = 10000,
    ) -> None:
        self.cacheable_prefixes = tuple(cacheable_prefixes)
        self._seen_hashes: set[str] = set()
        self._max_history = max_history
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_requests = 0

    def is_cacheable(self, content: str) -> bool:
        """Determine whether content is cacheable based on prefix matching."""
        if not content:
            return False
        return any(content.startswith(prefix) for prefix in self.cacheable_prefixes)

    def prepare_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return a copy of messages with cache_control added to cacheable content.

        String content that is cacheable is converted to the block format:
            [{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}]

        Block content (list of dicts) has cache_control added to each cacheable block.

        Non-cacheable content is left unchanged.
        """
        result = copy.deepcopy(messages)

        for msg in result:
            content = msg.get("content")
            if content is None:
                continue

            if isinstance(content, str):
                if self.is_cacheable(content):
                    self._track(content)
                    msg["content"] = [
                        {
                            "type": "text",
                            "text": content,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ]
            elif isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "text" and self.is_cacheable(block.get("text", "")):
                        self._track(block["text"])
                        block["cache_control"] = {"type": "ephemeral"}

        return result

    def get_cache_stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_requests": self._total_requests,
            "hit_rate": (self._cache_hits / self._total_requests if self._total_requests > 0 else 0.0),
        }

    def _track(self, content: str) -> None:
        """Track cache hit/miss based on content hash."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        self._total_requests += 1
        if content_hash in self._seen_hashes:
            self._cache_hits += 1
        else:
            self._cache_misses += 1
            if len(self._seen_hashes) >= self._max_history:
                self._seen_hashes.clear()
            self._seen_hashes.add(content_hash)
