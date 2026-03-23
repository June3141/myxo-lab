"""Tests for CachedGitHubMCP."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from myxo.cached_github import CachedGitHubMCP

# --- init ---


def test_default_ttl():
    cache = CachedGitHubMCP()
    assert cache.ttl == 300


def test_custom_ttl():
    cache = CachedGitHubMCP(ttl=60)
    assert cache.ttl == 60


def test_ttl_zero_raises_value_error():
    with pytest.raises(ValueError, match="ttl must be positive"):
        CachedGitHubMCP(ttl=0)


def test_ttl_negative_raises_value_error():
    with pytest.raises(ValueError, match="ttl must be positive"):
        CachedGitHubMCP(ttl=-10)


# --- set / get ---


def test_get_returns_none_for_missing_key():
    cache = CachedGitHubMCP()
    assert cache.get("nonexistent") is None


def test_set_and_get_value():
    cache = CachedGitHubMCP()
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_set_and_get_various_types():
    cache = CachedGitHubMCP()
    cache.set("str", "hello")
    cache.set("int", 42)
    cache.set("list", [1, 2, 3])
    cache.set("dict", {"a": 1})
    assert cache.get("str") == "hello"
    assert cache.get("int") == 42
    assert cache.get("list") == [1, 2, 3]
    assert cache.get("dict") == {"a": 1}


def test_set_overwrites_existing_value():
    cache = CachedGitHubMCP()
    cache.set("key", "old")
    cache.set("key", "new")
    assert cache.get("key") == "new"


def test_set_and_get_none_value():
    """None can be stored and retrieved without being confused with 'missing'."""
    cache = CachedGitHubMCP()
    cache.set("key", None)
    assert cache.get("key") is None
    assert cache.is_cached("key") is True


# --- TTL expiration (mocked clock) ---


def test_get_returns_none_after_ttl_expired():
    with patch("myxo.cached_github.time.monotonic") as mock_mono:
        mock_mono.return_value = 1000.0
        cache = CachedGitHubMCP(ttl=10)
        cache.set("key", "value")
        assert cache.get("key") == "value"

        mock_mono.return_value = 1010.1
        assert cache.get("key") is None


def test_is_cached_returns_false_after_ttl_expired():
    with patch("myxo.cached_github.time.monotonic") as mock_mono:
        mock_mono.return_value = 1000.0
        cache = CachedGitHubMCP(ttl=10)
        cache.set("key", "value")
        assert cache.is_cached("key") is True

        mock_mono.return_value = 1010.1
        assert cache.is_cached("key") is False


def test_value_still_valid_just_before_ttl():
    with patch("myxo.cached_github.time.monotonic") as mock_mono:
        mock_mono.return_value = 1000.0
        cache = CachedGitHubMCP(ttl=10)
        cache.set("key", "value")

        mock_mono.return_value = 1009.9
        assert cache.get("key") == "value"


# --- invalidate ---


def test_invalidate_removes_key():
    cache = CachedGitHubMCP()
    cache.set("key", "value")
    cache.invalidate("key")
    assert cache.get("key") is None


def test_invalidate_nonexistent_key_does_not_raise():
    cache = CachedGitHubMCP()
    cache.invalidate("nonexistent")  # should not raise


# --- clear ---


def test_clear_removes_all_keys():
    cache = CachedGitHubMCP()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None
    assert cache.get("c") is None


# --- is_cached ---


def test_is_cached_returns_false_for_missing_key():
    cache = CachedGitHubMCP()
    assert cache.is_cached("nonexistent") is False


def test_is_cached_returns_true_for_existing_key():
    cache = CachedGitHubMCP()
    cache.set("key", "value")
    assert cache.is_cached("key") is True


def test_is_cached_returns_false_after_invalidation():
    cache = CachedGitHubMCP()
    cache.set("key", "value")
    cache.invalidate("key")
    assert cache.is_cached("key") is False


# --- cache hit ---


def test_cache_hit_returns_same_object():
    cache = CachedGitHubMCP()
    data = {"repos": ["a", "b"]}
    cache.set("repos", data)
    assert cache.get("repos") is data
    assert cache.get("repos") is data
