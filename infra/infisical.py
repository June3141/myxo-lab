"""Infisical server infrastructure (self-hosted on ECS Fargate).

Defines an ECS Fargate service running the Infisical secrets manager.
Uses the existing ECS cluster from ecs.py.  Actual secret values
(MONGO_URL, ENCRYPTION_KEY, etc.) come from Pulumi config, never hardcoded.

Ref: https://infisical.com/docs/self-hosting/deployments/aws
"""

import json

import ecs as ecs_infra
import pulumi
import pulumi_aws as aws

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config("infisical")

# Sensitive values from Pulumi encrypted config
mongo_url = config.require_secret("MONGO_URL")
encryption_key = config.require_secret("ENCRYPTION_KEY")
auth_secret = config.require_secret("AUTH_SECRET")
site_url = config.get("SITE_URL") or "https://infisical.internal"

_COST_TAGS = {
    "Project": "myxo-lab",
    "Environment": pulumi.get_stack(),
    "CostCenter": "secrets-management",
}

# ---------------------------------------------------------------------------
# CloudWatch Log Group
# ---------------------------------------------------------------------------
log_group = aws.cloudwatch.LogGroup(
    "infisical-log-group",
    name="/ecs/infisical",
    retention_in_days=14,
    tags=_COST_TAGS,
)

# ---------------------------------------------------------------------------
# Security Group — allow inbound 443 (HTTPS)
# ---------------------------------------------------------------------------
infisical_sg = aws.ec2.SecurityGroup(
    "infisical-sg",
    name="infisical-sg",
    description="Allow inbound HTTPS traffic to Infisical",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
            description="HTTPS inbound",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound",
        ),
    ],
    tags={"Name": "infisical-sg", **_COST_TAGS},
)

# ---------------------------------------------------------------------------
# ECS Task Definition
# ---------------------------------------------------------------------------
aws_config = pulumi.Config("aws")
_region = aws_config.require("region")

container_definitions = pulumi.Output.all(
    log_group.name,
    mongo_url,
    encryption_key,
    auth_secret,
).apply(
    lambda args: json.dumps(
        [
            {
                "name": "infisical",
                "image": "infisical/infisical:latest",
                "cpu": 512,
                "memory": 1024,
                "essential": True,
                "portMappings": [
                    {
                        "containerPort": 443,
                        "protocol": "tcp",
                    }
                ],
                "environment": [
                    {"name": "MONGO_URL", "value": args[1]},
                    {"name": "ENCRYPTION_KEY", "value": args[2]},
                    {"name": "AUTH_SECRET", "value": args[3]},
                    {"name": "SITE_URL", "value": site_url},
                    {"name": "NODE_ENV", "value": "production"},
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": args[0],
                        "awslogs-region": _region,
                        "awslogs-stream-prefix": "infisical",
                    },
                },
            }
        ]
    )
)

task_definition = aws.ecs.TaskDefinition(
    "infisical-task",
    family="infisical-task",
    cpu="512",
    memory="1024",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=ecs_infra.task_execution_role.arn,
    task_role_arn=ecs_infra.task_role.arn,
    container_definitions=container_definitions,
    tags=_COST_TAGS,
)

# ---------------------------------------------------------------------------
# ECS Service
# ---------------------------------------------------------------------------
infisical_service = aws.ecs.Service(
    "infisical-service",
    name="infisical-service",
    cluster=ecs_infra.cluster.arn,
    task_definition=task_definition.arn,
    desired_count=1,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        security_groups=[infisical_sg.id],
        # TODO(#86): Add subnet IDs once VPC resources are available
        subnets=[],
    ),
    tags=_COST_TAGS,
)

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
pulumi.export("infisical_service_name", infisical_service.name)
pulumi.export("infisical_task_definition_arn", task_definition.arn)
