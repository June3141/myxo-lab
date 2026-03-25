"""PR cleanup Lambda handler.

Handles PR close events from EventBridge and cleans up associated
preview resources (ECS tasks, preview environments).
"""

import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handle(event, context):
    """Handle a PR close event.

    Args:
        event: EventBridge event payload containing PR details.
        context: Lambda execution context (unused).

    Returns:
        dict with statusCode and JSON body.
    """
    detail = event.get("detail", {})
    action = detail.get("action", "unknown")
    pr = detail.get("pull_request", {})
    pr_number = pr.get("number", 0)

    logger.info("PR #%s action=%s — cleanup triggered", pr_number, action)

    # TODO: implement actual cleanup logic
    # - Stop ECS tasks tagged with this PR number
    # - Delete preview environment resources
    # - Clean up associated DNS/routing entries

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "cleanup acknowledged",
                "pr_number": pr_number,
                "action": action,
            }
        ),
    }
