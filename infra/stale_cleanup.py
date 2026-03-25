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

import pulumi
import pulumi_aws as aws

# --- IAM Role for Lambda ---------------------------------------------------
cleanup_role = aws.iam.Role(
    "myxo-stale-cleanup-role",
    name="myxo-stale-cleanup-role",
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

# Basic Lambda execution (CloudWatch Logs)
aws.iam.RolePolicyAttachment(
    "myxo-stale-cleanup-basic-exec",
    role=cleanup_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)

# Inline policy for ECS + EC2 describe/delete with AutoDelete tag
aws.iam.RolePolicy(
    "myxo-stale-cleanup-policy",
    role=cleanup_role.id,
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

# --- CloudWatch Log Group --------------------------------------------------
cleanup_log_group = aws.cloudwatch.LogGroup(
    "myxo-stale-cleanup-logs",
    name="/aws/lambda/myxo-stale-cleanup",
    retention_in_days=14,
)

# --- Lambda Function -------------------------------------------------------
cleanup_function = aws.lambda_.Function(
    "myxo-stale-cleanup",
    function_name="myxo-stale-cleanup",
    runtime="python3.13",
    handler="handler.handle",
    timeout=300,
    memory_size=128,
    role=cleanup_role.arn,
    code=pulumi.AssetArchive({".": pulumi.FileArchive("../lambda/stale_cleanup")}),
)

# --- EventBridge Schedule Rule ---------------------------------------------
schedule_rule = aws.cloudwatch.EventRule(
    "myxo-stale-cleanup-schedule",
    name="myxo-stale-cleanup-schedule",
    description="Run stale resource cleanup daily at 03:00 UTC",
    schedule_expression="cron(0 3 * * ? *)",
)

# --- EventBridge Target ----------------------------------------------------
aws.cloudwatch.EventTarget(
    "myxo-stale-cleanup-target",
    rule=schedule_rule.name,
    arn=cleanup_function.arn,
)

# --- Lambda Permission for EventBridge ------------------------------------
aws.lambda_.Permission(
    "myxo-stale-cleanup-invoke",
    action="lambda:InvokeFunction",
    function=cleanup_function.name,
    principal="events.amazonaws.com",
    source_arn=schedule_rule.arn,
)

# --- Exports ---------------------------------------------------------------
pulumi.export("stale_cleanup_function_arn", cleanup_function.arn)
pulumi.export("stale_cleanup_schedule_rule", schedule_rule.name)
