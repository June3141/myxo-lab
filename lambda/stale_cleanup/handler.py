"""Stale resource cleanup Lambda handler.

Scans for AWS resources tagged with AutoDelete=true and
AutoDeleteAfter timestamp. If the timestamp is in the past
(resource has exceeded its TTL), the resource is logged for
deletion.

This is a stub — actual deletion logic is a placeholder.
"""

import json
import logging
from datetime import UTC, datetime

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _find_stale_resources() -> list[dict]:
    """Find resources tagged with AutoDelete=true whose TTL has expired."""
    client = boto3.client("resourcegroupstaggingapi")
    paginator = client.get_paginator("get_resources")

    stale: list[dict] = []
    now = datetime.now(tz=UTC)

    for page in paginator.paginate(
        TagFilters=[{"Key": "AutoDelete", "Values": ["true"]}],
    ):
        for resource in page.get("ResourceTagMappingList", []):
            tags = {t["Key"]: t["Value"] for t in resource.get("Tags", [])}
            delete_after = tags.get("AutoDeleteAfter")
            if not delete_after:
                continue

            try:
                expiry = datetime.fromisoformat(delete_after)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=UTC)
            except ValueError:
                logger.warning(
                    "Invalid AutoDeleteAfter value '%s' on %s",
                    delete_after,
                    resource["ResourceARN"],
                )
                continue

            if now > expiry:
                stale.append(
                    {
                        "arn": resource["ResourceARN"],
                        "auto_delete_after": delete_after,
                        "age_hours": round((now - expiry).total_seconds() / 3600, 1),
                    }
                )

    return stale


def handle(event, context):
    """Lambda entry point.

    Returns a summary of stale resources found. Actual deletion
    is a placeholder for future implementation.
    """
    logger.info("Starting stale resource scan")

    stale_resources = _find_stale_resources()

    for res in stale_resources:
        logger.info(
            "STALE: %s (expired %s, %.1f hours ago)",
            res["arn"],
            res["auto_delete_after"],
            res["age_hours"],
        )

    # TODO: Implement actual deletion logic for ECS tasks, EC2 instances
    logger.info("Found %d stale resources", len(stale_resources))

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "stale_count": len(stale_resources),
                "resources": stale_resources,
            }
        ),
    }
