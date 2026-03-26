"""Shared infrastructure helpers to reduce duplication across modules.

Provides reusable factory functions for common AWS resource patterns:
- IAM Lambda roles with assume-role policies
- CloudWatch Log Groups with standard retention
- Lambda BasicExecutionRole policy attachments
- EventBridge → Lambda invocation permissions
"""

import json

import pulumi_aws as aws

__all__ = [
    "LAMBDA_ASSUME_ROLE_POLICY",
    "ECS_TASK_ASSUME_ROLE_POLICY",
    "create_lambda_role",
    "create_log_group",
    "attach_basic_execution_role",
    "create_eventbridge_lambda_permission",
]

LAMBDA_ASSUME_ROLE_POLICY = json.dumps(
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
)

ECS_TASK_ASSUME_ROLE_POLICY = json.dumps(
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
)


def create_lambda_role(name: str) -> aws.iam.Role:
    """Create an IAM Role with Lambda assume-role policy."""
    return aws.iam.Role(
        f"{name}-role",
        name=f"{name}-role",
        assume_role_policy=LAMBDA_ASSUME_ROLE_POLICY,
    )


def create_log_group(
    name: str,
    path: str,
    retention_in_days: int = 14,
    **kwargs: object,
) -> aws.cloudwatch.LogGroup:
    """Create a CloudWatch Log Group with standard retention."""
    return aws.cloudwatch.LogGroup(
        name,
        name=path,
        retention_in_days=retention_in_days,
        **kwargs,
    )


def attach_basic_execution_role(name: str, role: aws.iam.Role) -> aws.iam.RolePolicyAttachment:
    """Attach AWSLambdaBasicExecutionRole policy to a role."""
    return aws.iam.RolePolicyAttachment(
        f"{name}-basic-exec",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )


def create_eventbridge_lambda_permission(
    name: str,
    function: aws.lambda_.Function,
    rule: aws.cloudwatch.EventRule,
) -> aws.lambda_.Permission:
    """Allow EventBridge to invoke a Lambda function."""
    return aws.lambda_.Permission(
        f"{name}-eventbridge-permission",
        action="lambda:InvokeFunction",
        function=function.name,
        principal="events.amazonaws.com",
        source_arn=rule.arn,
    )
