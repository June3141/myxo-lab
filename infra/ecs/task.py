"""ECS Task Definition, IAM roles, CloudWatch log group and metric filter."""

import json

import common
import pulumi
import pulumi_aws as aws
from constants import LOG_RETENTION_DAYS, cost_tags

from .ecr import repo
from .efs import nix_cache_ap, nix_cache_fs

config = pulumi.Config("aws")
_region = config.require("region")

_COST_TAGS = cost_tags(cost_center="ai-agent")

ecs = aws.ecs
iam = aws.iam
cloudwatch = aws.cloudwatch

# --- CloudWatch Log Group ----------------------------------------------------
log_group = common.create_log_group("myxo-log-group", "/ecs/myxo", retention_in_days=LOG_RETENTION_DAYS)

# --- IAM: Task Execution Role -----------------------------------------------
task_execution_role = iam.Role(
    "myxo-task-execution-role",
    name="myxo-task-execution-role",
    assume_role_policy=common.ECS_TASK_ASSUME_ROLE_POLICY,
)

iam.RolePolicyAttachment(
    "myxo-exec-policy",
    role=task_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

# --- IAM: Task Role (placeholder for Secrets Manager / S3) -------------------
task_role = iam.Role(
    "myxo-task-role",
    name="myxo-task-role",
    assume_role_policy=common.ECS_TASK_ASSUME_ROLE_POLICY,
)

# EFS client permissions for task role
iam.RolePolicy(
    "myxo-task-efs-policy",
    role=task_role.name,
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "elasticfilesystem:ClientMount",
                        "elasticfilesystem:ClientWrite",
                        "elasticfilesystem:DescribeMountTargets",
                    ],
                    "Resource": "*",
                }
            ],
        }
    ),
)

# --- ECS Task Definition -----------------------------------------------------
task_definition = ecs.TaskDefinition(
    "myxo-task",
    family="myxo-task",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_execution_role.arn,
    task_role_arn=task_role.arn,
    volumes=[
        ecs.TaskDefinitionVolumeArgs(
            name="nix-cache",
            efs_volume_configuration=ecs.TaskDefinitionVolumeEfsVolumeConfigurationArgs(
                file_system_id=nix_cache_fs.id,
                transit_encryption="ENABLED",
                authorization_config=ecs.TaskDefinitionVolumeEfsVolumeConfigurationAuthorizationConfigArgs(
                    access_point_id=nix_cache_ap.id,
                    iam="ENABLED",
                ),
            ),
        ),
    ],
    tags=_COST_TAGS,
    container_definitions=pulumi.Output.all(repo.repository_url, log_group.name).apply(
        lambda args: json.dumps(
            [
                {
                    "name": "myxo",
                    "image": f"{args[0]}:latest",
                    "cpu": 256,
                    "memory": 512,
                    "essential": True,
                    "mountPoints": [
                        {
                            "sourceVolume": "nix-cache",
                            "containerPath": "/nix",
                            "readOnly": False,
                        }
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": args[1],
                            "awslogs-region": _region,
                            "awslogs-stream-prefix": "myxo",
                        },
                    },
                }
            ]
        )
    ),
)

# --- CloudWatch Metric Filter for task execution (#137) ---------------------
task_execution_metric_filter = cloudwatch.LogMetricFilter(
    "myxo-task-execution-metric",
    name="myxo-task-execution-time",
    log_group_name=log_group.name,
    pattern="TASK_COMPLETE",
    metric_transformation=cloudwatch.LogMetricFilterMetricTransformationArgs(
        name="TaskCompletionCount",
        namespace="Myxo/ECS",
        value="1",
        default_value="0",
    ),
)

# --- Exports -----------------------------------------------------------------
pulumi.export("ecr_url", repo.repository_url)
pulumi.export("task_definition_arn", task_definition.arn)
pulumi.export("efs_file_system_id", nix_cache_fs.id)
