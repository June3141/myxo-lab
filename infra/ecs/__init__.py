"""ECS Fargate resources for Myxo execution environment.

Public interface re-exported from submodules so that existing imports
like ``import ecs as ecs_infra; ecs_infra.cluster`` continue to work.
"""

from .cluster import cluster
from .ecr import repo
from .efs import nix_cache_ap, nix_cache_fs
from .task import (
    log_group,
    task_definition,
    task_execution_metric_filter,
    task_execution_role,
    task_role,
)

__all__ = [
    "cluster",
    "log_group",
    "nix_cache_ap",
    "nix_cache_fs",
    "repo",
    "task_definition",
    "task_execution_metric_filter",
    "task_execution_role",
    "task_role",
]

# Cluster name export lives here to avoid circular imports
import pulumi  # noqa: E402

pulumi.export("cluster_name", cluster.name)
