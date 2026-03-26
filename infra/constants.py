"""Centralized constants for Myxo Lab infrastructure.

Single source of truth for project-wide values used across infra modules.
Avoids duplication of cost tags, log retention, port numbers, etc.

Ref: #249
"""

import pulumi

__all__ = [
    "COST_TAGS",
    "LOG_RETENTION_DAYS",
    "PREVIEW_API_PORT",
    "PROJECT_NAME",
    "cost_tags",
]

# ---------------------------------------------------------------------------
# Core identifiers
# ---------------------------------------------------------------------------
PROJECT_NAME: str = "myxo-lab"

# ---------------------------------------------------------------------------
# CloudWatch
# ---------------------------------------------------------------------------
LOG_RETENTION_DAYS: int = 14

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------
PREVIEW_API_PORT: int = 8080

# ---------------------------------------------------------------------------
# Cost tags (shared across AWS resources)
# ---------------------------------------------------------------------------
COST_TAGS: dict[str, str] = {
    "Project": PROJECT_NAME,
    "Environment": pulumi.get_stack(),
}


def cost_tags(*, cost_center: str) -> dict[str, str]:
    """Return cost tags with a service-specific CostCenter value.

    Parameters
    ----------
    cost_center:
        Value for the ``CostCenter`` tag (e.g. ``"ai-agent"``).
    """
    return {**COST_TAGS, "CostCenter": cost_center}
