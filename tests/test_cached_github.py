"""Tests for CachedGitHubMCP."""

import time

import pytest

from myxo.cached_github import CachedGitHubMCP


class TestCachedGitHubMCPInit:
    """Test initialization."""

    def test_default_ttl(self):
        cache = CachedGitHubMCP()
        assert cache.ttl == 300

    def test_custom_ttl(self):
        cache = CachedGitHubMCP(ttl=60)
        assert cache.ttl == 60


class TestCachedGitHubMCPSetAndGet:
    """Test set and get operations."""

    def test_get_returns_none_for_missing_key(self):
        cache = CachedGitHubMCP()
        assert cache.get("nonexistent") is None

    def test_set_and_get_value(self):
        cache = CachedGitHubMCP()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_set_and_get_various_types(self):
        cache = CachedGitHubMCP()
        cache.set("str", "hello")
        cache.set("int", 42)
        cache.set("list", [1, 2, 3])
        cache.set("dict", {"a": 1})
        assert cache.get("str") == "hello"
        assert cache.get("int") == 42
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"a": 1}

    def test_set_overwrites_existing_value(self):
        cache = CachedGitHubMCP()
        cache.set("key", "old")
        cache.set("key", "new")
        assert cache.get("key") == "new"


class TestCachedGitHubMCPTTL:
    """Test TTL expiration."""

    def test_get_returns_none_after_ttl_expired(self):
        cache = CachedGitHubMCP(ttl=1)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(1.1)
        assert cache.get("key") is None

    def test_is_cached_returns_false_after_ttl_expired(self):
        cache = CachedGitHubMCP(ttl=1)
        cache.set("key", "value")
        assert cache.is_cached("key") is True
        time.sleep(1.1)
        assert cache.is_cached("key") is False


class TestCachedGitHubMCPInvalidate:
    """Test invalidation."""

    def test_invalidate_removes_key(self):
        cache = CachedGitHubMCP()
        cache.set("key", "value")
        cache.invalidate("key")
        assert cache.get("key") is None

    def test_invalidate_nonexistent_key_does_not_raise(self):
        cache = CachedGitHubMCP()
        cache.invalidate("nonexistent")  # should not raise


class TestCachedGitHubMCPClear:
    """Test clear operation."""

    def test_clear_removes_all_keys(self):
        cache = CachedGitHubMCP()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None
        assert cache.get("c") is None


class TestCachedGitHubMCPIsCached:
    """Test is_cached method."""

    def test_is_cached_returns_false_for_missing_key(self):
        cache = CachedGitHubMCP()
        assert cache.is_cached("nonexistent") is False

    def test_is_cached_returns_true_for_existing_key(self):
        cache = CachedGitHubMCP()
        cache.set("key", "value")
        assert cache.is_cached("key") is True

    def test_is_cached_returns_false_after_invalidation(self):
        cache = CachedGitHubMCP()
        cache.set("key", "value")
        cache.invalidate("key")
        assert cache.is_cached("key") is False


class TestCachedGitHubMCPCacheHit:
    """Test that cache hit avoids redundant calls."""

    def test_cache_hit_returns_same_object(self):
        cache = CachedGitHubMCP()
        data = {"repos": ["a", "b"]}
        cache.set("repos", data)
        # Multiple gets should return the cached value
        assert cache.get("repos") is data
        assert cache.get("repos") is data
