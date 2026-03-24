"""ECS Fargate resources for Myxo execution environment (PoC).

Defines minimal ECS infrastructure:
- ECS Cluster, ECR Repository, CloudWatch Log Group
- IAM roles (task execution + task)
- Fargate Task Definition (0.25 vCPU / 512 MB)
"""

import json

import pulumi
import pulumi_aws as aws

# --- providers ---------------------------------------------------------------
ecs = aws.ecs
ecr = aws.ecr
iam = aws.iam
cloudwatch = aws.cloudwatch

# --- CloudWatch Log Group ----------------------------------------------------
log_group = cloudwatch.LogGroup(
    "myxo-log-group",
    name="/ecs/myxo",
    retention_in_days=14,
)

# --- ECR Repository ----------------------------------------------------------
repo = ecr.Repository(
    "myxo-base-repo",
    name="myxo-base",
    image_tag_mutability="MUTABLE",
    force_delete=True,  # PoC convenience — remove in production
)

# --- ECS Cluster -------------------------------------------------------------
cluster = ecs.Cluster(
    "myxo-cluster",
    name="myxo-cluster",
)

# --- IAM: Task Execution Role -----------------------------------------------
task_execution_role = iam.Role(
    "myxo-task-execution-role",
    name="myxo-task-execution-role",
    assume_role_policy=json.dumps(
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
    ),
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
    assume_role_policy=json.dumps(
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
    container_definitions=pulumi.Output.all(repo.repository_url, log_group.name).apply(
        lambda args: json.dumps(
            [
                {
                    "name": "myxo",
                    "image": f"{args[0]}:latest",
                    "cpu": 256,
                    "memory": 512,
                    "essential": True,
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": args[1],
                            "awslogs-region": aws.get_region().name,
                            "awslogs-stream-prefix": "myxo",
                        },
                    },
                }
            ]
        )
    ),
)

# --- Exports -----------------------------------------------------------------
pulumi.export("cluster_name", cluster.name)
pulumi.export("ecr_url", repo.repository_url)
pulumi.export("task_definition_arn", task_definition.arn)
