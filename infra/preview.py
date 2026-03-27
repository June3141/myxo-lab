"""ECS Fargate preview environment for PR-specific deployments (#73).

Creates a lightweight ECS service per pull request, allowing API preview
before merge.  Uses FARGATE_SPOT to keep costs around ~$1/day.
"""

import ecs
import pulumi
import pulumi_aws as aws
from constants import PREVIEW_API_PORT, preview_tags

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config("preview")
pr_number = config.get_int("pr_number") or 0


# ---------------------------------------------------------------------------
# PreviewEnvironment
# ---------------------------------------------------------------------------
class PreviewEnvironment:
    """PR-specific ECS Fargate preview service.

    Parameters
    ----------
    pr_number:
        Pull-request number used to name and tag resources.
    cluster_arn:
        ARN of the existing ECS cluster.
    task_definition_arn:
        ARN of the task definition to run.
    subnet_ids:
        List of subnet IDs for awsvpc networking.
    vpc_id:
        VPC ID for the security group.
    """

    def __init__(
        self,
        pr_number: int,
        *,
        cluster_arn: pulumi.Input[str],
        task_definition_arn: pulumi.Input[str],
        subnet_ids: list[pulumi.Input[str]],
        vpc_id: pulumi.Input[str],
    ) -> None:
        name = f"myxo-preview-pr-{pr_number}"
        _tags = preview_tags(cost_center="preview", pr_number=pr_number)

        # --- Security Group (allow inbound 8080) ----------------------------
        self.security_group = aws.ec2.SecurityGroup(
            f"{name}-sg",
            name_prefix=f"{name}-",
            description=f"Preview environment for PR #{pr_number}",
            vpc_id=vpc_id,
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=PREVIEW_API_PORT,
                    to_port=PREVIEW_API_PORT,
                    cidr_blocks=["0.0.0.0/0"],
                    description="API preview port",
                ),
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    protocol="-1",
                    from_port=0,
                    to_port=0,
                    cidr_blocks=["0.0.0.0/0"],
                ),
            ],
            tags={"Name": name, **_tags},
        )

        # --- ECS Service (Fargate Spot, 1 task) -----------------------------
        self.service = aws.ecs.Service(
            f"{name}-svc",
            name=name,
            cluster=cluster_arn,
            task_definition=task_definition_arn,
            desired_count=1,
            capacity_provider_strategies=[
                aws.ecs.ServiceCapacityProviderStrategyArgs(
                    capacity_provider="FARGATE_SPOT",
                    weight=1,
                ),
            ],
            network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                subnets=subnet_ids,
                security_groups=[self.security_group.id],
                assign_public_ip=True,
            ),
            tags=_tags,
        )

        # --- Export info -------------------------------------------------------
        # Note: actual URL requires ALB/Cloud Map setup (future work).
        # For now, access via task public IP on the preview API port.
        self.service_name = name


# ---------------------------------------------------------------------------
# Instantiate only when a PR number is provided via config
# ---------------------------------------------------------------------------
if pr_number:
    _vpc_id = config.require("vpc_id")
    _subnet_ids = config.require_object("subnet_ids")

    preview = PreviewEnvironment(
        pr_number,
        cluster_arn=ecs.cluster.arn,
        task_definition_arn=ecs.task_definition.arn,
        subnet_ids=_subnet_ids,
        vpc_id=_vpc_id,
    )

    pulumi.export("preview_service_name", preview.service_name)
