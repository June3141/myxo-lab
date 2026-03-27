"""Cleanup Lambda resources for PR close event handling.

Defines infrastructure to automatically clean up preview resources
when a pull request is closed:
- Lambda Function — handles PR close webhook events
- IAM Role — execution permissions (CloudWatch Logs + ECS stop)
- CloudWatch Log Group — Lambda log retention
- EventBridge Rule — triggers Lambda on PR close events
"""

import json

import common
import pulumi
import pulumi_aws as aws
from constants import LOG_RETENTION_DAYS

iam = aws.iam
cloudwatch = aws.cloudwatch

# --- CloudWatch Log Group for Lambda ----------------------------------------
cleanup_log_group = common.create_log_group(
    "myxo-pr-cleanup-logs",
    "/aws/lambda/myxo-pr-cleanup",
    retention_in_days=LOG_RETENTION_DAYS,
)

# --- IAM Role for Lambda execution ------------------------------------------
cleanup_role = common.create_lambda_role("myxo-pr-cleanup")

# CloudWatch Logs permissions
common.attach_basic_execution_role("myxo-pr-cleanup", cleanup_role)

# ECS task stop permissions
iam.RolePolicy(
    "myxo-pr-cleanup-ecs-policy",
    role=cleanup_role.name,
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecs:StopTask",
                        "ecs:ListTasks",
                        "ecs:DescribeTasks",
                    ],
                    "Resource": "arn:aws:ecs:*:*:task/myxo-cluster/*",
                }
            ],
        }
    ),
)

# --- Lambda Function --------------------------------------------------------
cleanup_lambda = aws.lambda_.Function(
    "myxo-pr-cleanup",
    function_name="myxo-pr-cleanup",
    runtime="python3.13",
    handler="handler.handle",
    timeout=60,
    memory_size=128,
    role=cleanup_role.arn,
    description="Clean up preview resources when PR is closed",
    code=pulumi.AssetArchive({"handler.py": pulumi.FileAsset("../lambda/pr_cleanup/handler.py")}),
)

# --- EventBridge Rule -------------------------------------------------------
pr_close_rule = cloudwatch.EventRule(
    "myxo-pr-close-rule",
    name="myxo-pr-close-rule",
    description="Trigger cleanup Lambda on GitHub PR close events",
    event_pattern=json.dumps(
        {
            "source": ["aws.partner/github.com"],
            "detail-type": ["pull_request"],
            "detail": {"action": ["closed"]},
        }
    ),
)

cloudwatch.EventTarget(
    "myxo-pr-close-target",
    rule=pr_close_rule.name,
    arn=cleanup_lambda.arn,
)

# Allow EventBridge to invoke the Lambda
common.create_eventbridge_lambda_permission("myxo-pr-cleanup", cleanup_lambda, pr_close_rule)

# --- Exports ----------------------------------------------------------------
pulumi.export("cleanup_lambda_arn", cleanup_lambda.arn)
pulumi.export("cleanup_rule_arn", pr_close_rule.arn)
