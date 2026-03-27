"""ECS Fargate resources for Myxo execution environment (PoC).

Defines minimal ECS infrastructure:
- ECS Cluster, ECR Repository, CloudWatch Log Group
- IAM roles (task execution + task)
- Fargate Task Definition (0.25 vCPU / 512 MB)
- EFS file system for Nix store cache
- Cost tags, ECR image scanning, CloudWatch metric filter
"""

import json

import common
import pulumi
import pulumi_aws as aws

config = pulumi.Config("aws")
_region = config.require("region")

# --- Cost tags (#137) --------------------------------------------------------
_COST_TAGS = {
    "Project": "myxo-lab",
    "Environment": pulumi.get_stack(),
    "CostCenter": "ai-agent",
}

# --- providers ---------------------------------------------------------------
ecs = aws.ecs
ecr = aws.ecr
iam = aws.iam
cloudwatch = aws.cloudwatch

# --- CloudWatch Log Group ----------------------------------------------------
log_group = common.create_log_group("myxo-log-group", "/ecs/myxo")

# --- ECR Repository ----------------------------------------------------------
repo = ecr.Repository(
    "myxo-base-repo",
    name="myxo-base",
    image_tag_mutability="MUTABLE",
    force_delete=False,
    image_scanning_configuration=ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
    tags=_COST_TAGS,
)

# --- ECS Cluster -------------------------------------------------------------
cluster = ecs.Cluster(
    "myxo-cluster",
    name="myxo-cluster",
    tags=_COST_TAGS,
)

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

# --- Fargate Spot Capacity Providers ----------------------------------------
ecs.ClusterCapacityProviders(
    "myxo-cluster-capacity-providers",
    cluster_name=cluster.name,
    capacity_providers=["FARGATE", "FARGATE_SPOT"],
    default_capacity_provider_strategies=[
        ecs.ClusterCapacityProvidersDefaultCapacityProviderStrategyArgs(
            capacity_provider="FARGATE_SPOT",
            weight=3,
            base=0,
        ),
        ecs.ClusterCapacityProvidersDefaultCapacityProviderStrategyArgs(
            capacity_provider="FARGATE",
            weight=1,
            base=1,
        ),
    ],
)

# --- EFS: Nix store cache ----------------------------------------------------
nix_cache_fs = aws.efs.FileSystem(
    "myxo-nix-cache",
    encrypted=True,
    performance_mode="generalPurpose",
    tags={"Name": "myxo-nix-cache", **_COST_TAGS},
)

nix_cache_ap = aws.efs.AccessPoint(
    "myxo-nix-cache-ap",
    file_system_id=nix_cache_fs.id,
    posix_user=aws.efs.AccessPointPosixUserArgs(uid=1000, gid=1000),
    root_directory=aws.efs.AccessPointRootDirectoryArgs(
        path="/nix-store",
        creation_info=aws.efs.AccessPointRootDirectoryCreationInfoArgs(
            owner_uid=1000,
            owner_gid=1000,
            permissions="755",
        ),
    ),
    tags={"Name": "myxo-nix-cache-ap"},
)

# TODO(#137): Add EFS Mount Target once VPC/subnet resources are available.
# aws.efs.MountTarget("myxo-nix-cache-mt", ...)

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
pulumi.export("cluster_name", cluster.name)
pulumi.export("ecr_url", repo.repository_url)
pulumi.export("task_definition_arn", task_definition.arn)
pulumi.export("efs_file_system_id", nix_cache_fs.id)
