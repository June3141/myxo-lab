"""Infisical server infrastructure (self-hosted on ECS Fargate).

Defines an ECS Fargate service running the Infisical secrets manager.
Uses the existing ECS cluster from ecs.py.  Actual secret values
(MONGO_URL, ENCRYPTION_KEY, etc.) come from Pulumi config, never hardcoded.
Secrets are stored in SSM Parameter Store and injected via the ECS secrets field.

Ref: https://infisical.com/docs/self-hosting/deployments/aws
"""

import json

import common
import ecs as ecs_infra
import pulumi
import pulumi_aws as aws
from constants import LOG_RETENTION_DAYS, cost_tags

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config("infisical")
vpc_config = pulumi.Config("vpc")

# Sensitive values from Pulumi encrypted config
mongo_url = config.require_secret("MONGO_URL")
encryption_key = config.require_secret("ENCRYPTION_KEY")
auth_secret = config.require_secret("AUTH_SECRET")
site_url = config.get("SITE_URL") or "https://infisical.internal"

# Network configuration from Pulumi config
vpc_id = vpc_config.require("id")
subnet_ids: list[str] = vpc_config.require_object("private_subnet_ids")
ingress_cidr_blocks: list[str] = config.get_object("ingress_cidr_blocks") or [
    vpc_config.require("cidr_block"),
]


# ---------------------------------------------------------------------------
# InfisicalServer
# ---------------------------------------------------------------------------
class InfisicalServer:
    """Self-hosted Infisical secrets manager on ECS Fargate.

    Parameters
    ----------
    vpc_id:
        VPC ID for the security group.
    subnet_ids:
        List of private subnet IDs for awsvpc networking.
    ingress_cidr_blocks:
        CIDR blocks allowed for inbound HTTPS traffic.
    mongo_url:
        MongoDB connection URL (Pulumi secret).
    encryption_key:
        Infisical encryption key (Pulumi secret).
    auth_secret:
        Infisical auth secret (Pulumi secret).
    site_url:
        Public URL for the Infisical instance.
    """

    def __init__(
        self,
        *,
        vpc_id: pulumi.Input[str],
        subnet_ids: list[str],
        ingress_cidr_blocks: list[str],
        mongo_url: pulumi.Input[str],
        encryption_key: pulumi.Input[str],
        auth_secret: pulumi.Input[str],
        site_url: str,
    ) -> None:
        _cost_tags = cost_tags(cost_center="secrets-management")

        # --- SSM Parameter Store — secrets for ECS container ----------------
        self.ssm_mongo_url = aws.ssm.Parameter(
            "infisical-ssm-mongo-url",
            name=f"/infisical/{pulumi.get_stack()}/MONGO_URL",
            type="SecureString",
            value=mongo_url,
            tags=_cost_tags,
        )

        self.ssm_encryption_key = aws.ssm.Parameter(
            "infisical-ssm-encryption-key",
            name=f"/infisical/{pulumi.get_stack()}/ENCRYPTION_KEY",
            type="SecureString",
            value=encryption_key,
            tags=_cost_tags,
        )

        self.ssm_auth_secret = aws.ssm.Parameter(
            "infisical-ssm-auth-secret",
            name=f"/infisical/{pulumi.get_stack()}/AUTH_SECRET",
            type="SecureString",
            value=auth_secret,
            tags=_cost_tags,
        )

        # --- CloudWatch Log Group -------------------------------------------
        self.log_group = common.create_log_group(
            "infisical-log-group",
            "/ecs/infisical",
            retention_in_days=LOG_RETENTION_DAYS,
            tags=_cost_tags,
        )

        # --- Security Group — allow inbound 443 (HTTPS) --------------------
        self.security_group = aws.ec2.SecurityGroup(
            "infisical-sg",
            name="infisical-sg",
            description="Allow inbound HTTPS traffic to Infisical",
            vpc_id=vpc_id,
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=443,
                    to_port=443,
                    cidr_blocks=ingress_cidr_blocks,
                    description="HTTPS inbound from configured CIDR",
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
            tags={"Name": "infisical-sg", **_cost_tags},
        )

        # --- ECS Task Definition --------------------------------------------
        aws_config = pulumi.Config("aws")
        _region = aws_config.require("region")

        container_definitions = pulumi.Output.all(
            self.log_group.name,
            self.ssm_mongo_url.arn,
            self.ssm_encryption_key.arn,
            self.ssm_auth_secret.arn,
        ).apply(
            lambda args: json.dumps(
                [
                    {
                        "name": "infisical",
                        "image": "infisical/infisical:v0.91.0",
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
                            {"name": "SITE_URL", "value": site_url},
                            {"name": "NODE_ENV", "value": "production"},
                        ],
                        "secrets": [
                            {"name": "MONGO_URL", "valueFrom": args[1]},
                            {"name": "ENCRYPTION_KEY", "valueFrom": args[2]},
                            {"name": "AUTH_SECRET", "valueFrom": args[3]},
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

        self.task_definition = aws.ecs.TaskDefinition(
            "infisical-task",
            family="infisical-task",
            cpu="512",
            memory="1024",
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            execution_role_arn=ecs_infra.task_execution_role.arn,
            task_role_arn=ecs_infra.task_role.arn,
            container_definitions=container_definitions,
            tags=_cost_tags,
        )

        # --- ECS Service ----------------------------------------------------
        self.service = aws.ecs.Service(
            "infisical-service",
            name="infisical-service",
            cluster=ecs_infra.cluster.arn,
            task_definition=self.task_definition.arn,
            desired_count=1,
            launch_type="FARGATE",
            network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                assign_public_ip=False,
                security_groups=[self.security_group.id],
                subnets=subnet_ids,
            ),
            tags=_cost_tags,
        )


# ---------------------------------------------------------------------------
# Instantiate at module level so Pulumi registers resources on import
# ---------------------------------------------------------------------------
infisical = InfisicalServer(
    vpc_id=vpc_id,
    subnet_ids=subnet_ids,
    ingress_cidr_blocks=ingress_cidr_blocks,
    mongo_url=mongo_url,
    encryption_key=encryption_key,
    auth_secret=auth_secret,
    site_url=site_url,
)

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
pulumi.export("infisical_service_name", infisical.service.name)
pulumi.export("infisical_task_definition_arn", infisical.task_definition.arn)
