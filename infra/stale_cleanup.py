"""Stale resource cleanup infrastructure for Myxo Lab.

Defines a Lambda-based cleanup system that scans for AWS resources
tagged with AutoDelete=true and removes them after their expiry time.

Resources:
- Lambda Function (myxo-stale-cleanup)
- IAM Role with permissions for ECS/EC2 describe+delete
- CloudWatch Log Group for Lambda logs
- EventBridge Schedule Rule (daily at 03:00 UTC)
- EventBridge Target connecting rule to Lambda
"""

import json

import common
import pulumi
import pulumi_aws as aws
from constants import LOG_RETENTION_DAYS, cost_tags


# ---------------------------------------------------------------------------
# StaleCleanupEnvironment
# ---------------------------------------------------------------------------
class StaleCleanupEnvironment:
    """Lambda-based stale resource cleanup on a daily schedule.

    Creates an IAM role, CloudWatch log group, Lambda function,
    and EventBridge schedule rule+target to scan for and remove
    AWS resources tagged with AutoDelete=true past their expiry.
    """

    def __init__(self) -> None:
        _cost_tags = cost_tags(cost_center="cleanup")

        # --- IAM Role for Lambda -------------------------------------------
        self.role = common.create_lambda_role("myxo-stale-cleanup")

        # Basic Lambda execution (CloudWatch Logs)
        common.attach_basic_execution_role("myxo-stale-cleanup", self.role)

        # Inline policy for ECS + EC2 describe/delete with AutoDelete tag
        aws.iam.RolePolicy(
            "myxo-stale-cleanup-policy",
            role=self.role.id,
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "ecs:DescribeTasks",
                                "ecs:ListTasks",
                                "ec2:DescribeInstances",
                                "tag:GetResources",
                            ],
                            "Sid": "ReadOnlyStaleResources",
                            "Resource": "*",
                            "Condition": {
                                "StringEquals": {
                                    "aws:ResourceTag/AutoDelete": "true",
                                }
                            },
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "tag:GetResources",
                                "ecs:ListTasks",
                                "ecs:ListClusters",
                            ],
                            "Resource": "*",
                        },
                    ],
                }
            ),
        )

        # --- CloudWatch Log Group ------------------------------------------
        self.log_group = common.create_log_group(
            "myxo-stale-cleanup-logs",
            "/aws/lambda/myxo-stale-cleanup",
            retention_in_days=LOG_RETENTION_DAYS,
            tags=_cost_tags,
        )

        # --- Lambda Function -----------------------------------------------
        self.cleanup_function = aws.lambda_.Function(
            "myxo-stale-cleanup",
            function_name="myxo-stale-cleanup",
            runtime="python3.13",
            handler="handler.handle",
            timeout=300,
            memory_size=128,
            role=self.role.arn,
            code=pulumi.AssetArchive({".": pulumi.FileArchive("../lambda/stale_cleanup")}),
            tags=_cost_tags,
        )

        # --- EventBridge Schedule Rule -------------------------------------
        self.schedule_rule = aws.cloudwatch.EventRule(
            "myxo-stale-cleanup-schedule",
            name="myxo-stale-cleanup-schedule",
            description="Run stale resource cleanup daily at 03:00 UTC",
            schedule_expression="cron(0 3 * * ? *)",
        )

        # --- EventBridge Target --------------------------------------------
        aws.cloudwatch.EventTarget(
            "myxo-stale-cleanup-target",
            rule=self.schedule_rule.name,
            arn=self.cleanup_function.arn,
        )

        # --- Lambda Permission for EventBridge ----------------------------
        common.create_eventbridge_lambda_permission("myxo-stale-cleanup", self.cleanup_function, self.schedule_rule)


# ---------------------------------------------------------------------------
# Instantiate at module level so Pulumi registers resources on import
# ---------------------------------------------------------------------------
stale_cleanup = StaleCleanupEnvironment()

# --- Exports ---------------------------------------------------------------
pulumi.export("stale_cleanup_function_arn", stale_cleanup.cleanup_function.arn)
pulumi.export("stale_cleanup_schedule_rule", stale_cleanup.schedule_rule.name)
