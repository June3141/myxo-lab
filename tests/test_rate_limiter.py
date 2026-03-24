"""Rate limiter tests for GitHub API rate limiting countermeasures."""

from __future__ import annotations

import logging

import httpx

from myxo.rate_limiter import (
    RateLimitInfo,
    check_rate_limit,
    is_rate_limited,
    parse_rate_limit_headers,
)


class TestRateLimitInfo:
    """Tests for the RateLimitInfo dataclass."""

    def test_dataclass_fields(self):
        info = RateLimitInfo(remaining=42, limit=60, reset_at=1700000000)
        assert info.remaining == 42
        assert info.limit == 60
        assert info.reset_at == 1700000000

    def test_is_low_remaining_true(self):
        info = RateLimitInfo(remaining=5, limit=60, reset_at=1700000000)
        assert info.is_low is True

    def test_is_low_remaining_false(self):
        info = RateLimitInfo(remaining=50, limit=60, reset_at=1700000000)
        assert info.is_low is False

    def test_is_low_boundary(self):
        """Remaining == 10 should NOT be considered low (< 10 is low)."""
        info = RateLimitInfo(remaining=10, limit=60, reset_at=1700000000)
        assert info.is_low is False

    def test_is_low_at_nine(self):
        info = RateLimitInfo(remaining=9, limit=60, reset_at=1700000000)
        assert info.is_low is True


class TestParseRateLimitHeaders:
    """Tests for parsing rate limit headers from httpx Response."""

    def _make_response(
        self,
        remaining: str | None = None,
        limit: str | None = None,
        reset: str | None = None,
        status_code: int = 200,
    ) -> httpx.Response:
        headers = {}
        if remaining is not None:
            headers["X-RateLimit-Remaining"] = remaining
        if limit is not None:
            headers["X-RateLimit-Limit"] = limit
        if reset is not None:
            headers["X-RateLimit-Reset"] = reset
        return httpx.Response(status_code=status_code, headers=headers)

    def test_parse_all_headers(self):
        resp = self._make_response(remaining="42", limit="60", reset="1700000000")
        info = parse_rate_limit_headers(resp)
        assert info is not None
        assert info.remaining == 42
        assert info.limit == 60
        assert info.reset_at == 1700000000

    def test_missing_headers_returns_none(self):
        resp = self._make_response()
        info = parse_rate_limit_headers(resp)
        assert info is None

    def test_partial_headers_returns_none(self):
        resp = self._make_response(remaining="42")
        info = parse_rate_limit_headers(resp)
        assert info is None

    def test_partial_headers_missing_reset_returns_none(self):
        resp = self._make_response(remaining="42", limit="60")
        info = parse_rate_limit_headers(resp)
        assert info is None

    def test_invalid_header_values_returns_none(self):
        resp = self._make_response(remaining="abc", limit="60", reset="1700000000")
        info = parse_rate_limit_headers(resp)
        assert info is None


class TestRateLimitDetection:
    """Tests for detecting rate-limited state (403 + rate limit headers)."""

    def test_is_rate_limited_403_with_zero_remaining(self):
        headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Reset": "1700000000",
        }
        resp = httpx.Response(status_code=403, headers=headers)
        assert is_rate_limited(resp) is True

    def test_is_not_rate_limited_200(self):
        headers = {
            "X-RateLimit-Remaining": "50",
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Reset": "1700000000",
        }
        resp = httpx.Response(status_code=200, headers=headers)
        assert is_rate_limited(resp) is False

    def test_is_not_rate_limited_403_without_headers(self):
        resp = httpx.Response(status_code=403)
        assert is_rate_limited(resp) is False

    def test_is_not_rate_limited_403_with_remaining(self):
        """403 but still has remaining requests — not a rate limit."""
        headers = {
            "X-RateLimit-Remaining": "10",
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Reset": "1700000000",
        }
        resp = httpx.Response(status_code=403, headers=headers)
        assert is_rate_limited(resp) is False


class TestLowRemainingWarning:
    """Tests for logging a warning when remaining requests are low."""

    def test_warns_on_low_remaining(self, caplog):
        headers = {
            "X-RateLimit-Remaining": "5",
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Reset": "1700000000",
        }
        resp = httpx.Response(status_code=200, headers=headers)

        with caplog.at_level(logging.WARNING):
            check_rate_limit(resp)

        assert any("rate limit" in msg.lower() for msg in caplog.messages)

    def test_no_warning_when_sufficient(self, caplog):
        headers = {
            "X-RateLimit-Remaining": "50",
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Reset": "1700000000",
        }
        resp = httpx.Response(status_code=200, headers=headers)

        with caplog.at_level(logging.WARNING):
            check_rate_limit(resp)

        assert not any("rate limit" in msg.lower() for msg in caplog.messages)

    def test_no_warning_when_no_headers(self, caplog):
        resp = httpx.Response(status_code=200)

        with caplog.at_level(logging.WARNING):
            check_rate_limit(resp)

        assert not any("rate limit" in msg.lower() for msg in caplog.messages)
