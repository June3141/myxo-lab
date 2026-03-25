"""Cleanup Lambda resources for PR close event handling.

Defines infrastructure to automatically clean up preview resources
when a pull request is closed:
- Lambda Function — handles PR close webhook events
- IAM Role — execution permissions (CloudWatch Logs + ECS stop)
- CloudWatch Log Group — Lambda log retention
- EventBridge Rule — triggers Lambda on PR close events
"""

import json

import pulumi
import pulumi_aws as aws

iam = aws.iam
cloudwatch = aws.cloudwatch

# --- CloudWatch Log Group for Lambda ----------------------------------------
cleanup_log_group = cloudwatch.LogGroup(
    "myxo-pr-cleanup-logs",
    name="/aws/lambda/myxo-pr-cleanup",
    retention_in_days=14,
)

# --- IAM Role for Lambda execution ------------------------------------------
cleanup_role = iam.Role(
    "myxo-pr-cleanup-role",
    name="myxo-pr-cleanup-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    ),
)

# CloudWatch Logs permissions
iam.RolePolicyAttachment(
    "myxo-pr-cleanup-logs-policy",
    role=cleanup_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)

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
aws.lambda_.Permission(
    "myxo-pr-cleanup-eventbridge-permission",
    action="lambda:InvokeFunction",
    function=cleanup_lambda.name,
    principal="events.amazonaws.com",
    source_arn=pr_close_rule.arn,
)

# --- Exports ----------------------------------------------------------------
pulumi.export("cleanup_lambda_arn", cleanup_lambda.arn)
pulumi.export("cleanup_rule_arn", pr_close_rule.arn)
