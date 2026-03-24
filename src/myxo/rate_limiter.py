"""GitHub API rate limiting utilities.

Parse rate-limit headers from GitHub API responses, detect when the
client is rate-limited, and log warnings when remaining requests are low.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

_LOW_REMAINING_THRESHOLD = 10


@dataclass(frozen=True)
class RateLimitInfo:
    """Parsed GitHub API rate-limit information."""

    remaining: int
    limit: int
    reset_at: int  # Unix epoch seconds

    @property
    def is_low(self) -> bool:
        """Return True when remaining requests are below the threshold."""
        return self.remaining < _LOW_REMAINING_THRESHOLD


def parse_rate_limit_headers(response: httpx.Response) -> RateLimitInfo | None:
    """Extract rate-limit info from response headers.

    Returns ``None`` when any required header is missing or unparseable.
    """
    try:
        remaining = int(response.headers["X-RateLimit-Remaining"])
        limit = int(response.headers["X-RateLimit-Limit"])
        reset_at = int(response.headers["X-RateLimit-Reset"])
    except (KeyError, ValueError):
        return None
    return RateLimitInfo(remaining=remaining, limit=limit, reset_at=reset_at)


def is_rate_limited(response: httpx.Response) -> bool:
    """Return True if the response indicates a GitHub rate-limit block."""
    if response.status_code != 403:
        return False
    info = parse_rate_limit_headers(response)
    if info is None:
        return False
    return info.remaining == 0


def check_rate_limit(response: httpx.Response) -> RateLimitInfo | None:
    """Inspect a response and warn if remaining requests are low.

    Returns the parsed :class:`RateLimitInfo` or ``None``.
    """
    info = parse_rate_limit_headers(response)
    if info is not None and info.remaining == 0:
        logger.warning(
            "GitHub API rate limit exhausted: 0/%d remaining (resets at %d)",
            info.limit,
            info.reset_at,
        )
    elif info is not None and info.is_low:
        logger.warning(
            "GitHub API rate limit running low: %d/%d remaining (resets at %d)",
            info.remaining,
            info.limit,
            info.reset_at,
        )
    return info
