"""Tests for Claude prompt caching manager."""

import pytest

from myxo.prompt_cache import PromptCacheManager


class TestPromptCacheManagerInit:
    """Test PromptCacheManager initialization."""

    def test_init_with_cacheable_prefixes(self):
        manager = PromptCacheManager(cacheable_prefixes=["Ship's Log", "Skills"])
        assert manager.cacheable_prefixes == ["Ship's Log", "Skills"]

    def test_init_with_empty_prefixes(self):
        manager = PromptCacheManager(cacheable_prefixes=[])
        assert manager.cacheable_prefixes == []

    def test_init_default_stats(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        stats = manager.get_cache_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["total_requests"] == 0


class TestIsCacheable:
    """Test cache eligibility detection."""

    def test_content_matching_prefix_is_cacheable(self):
        manager = PromptCacheManager(cacheable_prefixes=["Ship's Log", "Skills"])
        assert manager.is_cacheable("Ship's Log: Entry 42") is True

    def test_content_matching_second_prefix_is_cacheable(self):
        manager = PromptCacheManager(cacheable_prefixes=["Ship's Log", "Skills"])
        assert manager.is_cacheable("Skills: Python, Rust") is True

    def test_content_not_matching_any_prefix(self):
        manager = PromptCacheManager(cacheable_prefixes=["Ship's Log", "Skills"])
        assert manager.is_cacheable("User asked a question") is False

    def test_empty_content_is_not_cacheable(self):
        manager = PromptCacheManager(cacheable_prefixes=["Ship's Log"])
        assert manager.is_cacheable("") is False

    def test_no_prefixes_means_nothing_cacheable(self):
        manager = PromptCacheManager(cacheable_prefixes=[])
        assert manager.is_cacheable("Ship's Log: Entry 1") is False


class TestPrepareMessages:
    """Test message preparation with cache_control injection."""

    def test_adds_cache_control_to_cacheable_string_content(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        messages = [
            {"role": "user", "content": "System prompt content"},
        ]
        result = manager.prepare_messages(messages)
        assert result[0]["content"] == [
            {
                "type": "text",
                "text": "System prompt content",
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def test_adds_cache_control_to_cacheable_block_content(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "System instructions here"},
                    {"type": "text", "text": "User question"},
                ],
            },
        ]
        result = manager.prepare_messages(messages)
        assert result[0]["content"][1] == {"type": "text", "text": "User question"}

    def test_does_not_modify_non_cacheable_content(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
        ]
        result = manager.prepare_messages(messages)
        assert result[0]["content"] == "Hello, how are you?"

    def test_preserves_message_role(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        messages = [
            {"role": "system", "content": "System: be helpful"},
        ]
        result = manager.prepare_messages(messages)
        assert result[0]["role"] == "system"

    def test_handles_multiple_messages(self):
        manager = PromptCacheManager(cacheable_prefixes=["System", "Skills"])
        messages = [
            {"role": "system", "content": "System: be helpful"},
            {"role": "user", "content": "Skills: Python"},
            {"role": "user", "content": "What is 2+2?"},
        ]
        result = manager.prepare_messages(messages)
        # First message should have cache_control
        assert result[0]["content"][0]["cache_control"] == {"type": "ephemeral"}
        # Second message should have cache_control
        assert result[1]["content"][0]["cache_control"] == {"type": "ephemeral"}
        # Third message should NOT have cache_control
        assert result[2]["content"] == "What is 2+2?"

    def test_does_not_mutate_original_messages(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        messages = [
            {"role": "user", "content": "System prompt content"},
        ]
        original_content = messages[0]["content"]
        manager.prepare_messages(messages)
        assert messages[0]["content"] == original_content

    def test_empty_messages_returns_empty(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        result = manager.prepare_messages([])
        assert result == []


class TestCacheHashDetection:
    """Test content hash-based cache hit/miss detection."""

    def test_same_content_is_cache_hit(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        messages = [{"role": "system", "content": "System: be helpful"}]
        manager.prepare_messages(messages)
        manager.prepare_messages(messages)
        stats = manager.get_cache_stats()
        assert stats["cache_hits"] == 1

    def test_different_content_is_cache_miss(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        messages1 = [{"role": "system", "content": "System: be helpful"}]
        messages2 = [{"role": "system", "content": "System: be concise"}]
        manager.prepare_messages(messages1)
        manager.prepare_messages(messages2)
        stats = manager.get_cache_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 2

    def test_non_cacheable_content_not_tracked(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        messages = [{"role": "user", "content": "Hello"}]
        manager.prepare_messages(messages)
        manager.prepare_messages(messages)
        stats = manager.get_cache_stats()
        assert stats["total_requests"] == 0


class TestGetCacheStats:
    """Test cache statistics reporting."""

    def test_hit_rate_calculation(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        messages = [{"role": "system", "content": "System: be helpful"}]
        manager.prepare_messages(messages)
        manager.prepare_messages(messages)
        manager.prepare_messages(messages)
        stats = manager.get_cache_stats()
        assert stats["total_requests"] == 3
        assert stats["cache_hits"] == 2
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == pytest.approx(2 / 3)

    def test_hit_rate_zero_when_no_requests(self):
        manager = PromptCacheManager(cacheable_prefixes=["System"])
        stats = manager.get_cache_stats()
        assert stats["hit_rate"] == 0.0
