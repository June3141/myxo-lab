"""ECS Fargate infrastructure source-level tests.

Since we cannot run ``pulumi up`` in CI, these tests validate that the
infrastructure source code defines the expected AWS resources using
"myxo" naming throughout.
"""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


def test_ecs_module_exists():
    """infra/ecs.py must exist."""
    assert (INFRA_DIR / "ecs.py").is_file(), "infra/ecs.py must exist"


# ---------------------------------------------------------------------------
# Resource definitions in ecs.py
# ---------------------------------------------------------------------------


def _ecs_source() -> str:
    return (INFRA_DIR / "ecs.py").read_text()


def test_defines_ecs_cluster():
    """ecs.py must define an ECS Cluster resource."""
    src = _ecs_source()
    assert "ecs.Cluster(" in src, "ecs.py must define ecs.Cluster"


def test_defines_ecr_repository():
    """ecs.py must define an ECR Repository resource."""
    src = _ecs_source()
    assert "ecr.Repository(" in src, "ecs.py must define ecr.Repository"


def test_defines_task_definition():
    """ecs.py must define an ECS Task Definition resource."""
    src = _ecs_source()
    assert "ecs.TaskDefinition(" in src, "ecs.py must define ecs.TaskDefinition"


def test_defines_iam_roles():
    """ecs.py must define IAM roles for task execution and task."""
    src = _ecs_source()
    assert "iam.Role(" in src, "ecs.py must define iam.Role"
    assert "task_execution_role" in src or "task-execution-role" in src
    assert "task_role" in src or "task-role" in src


def test_defines_cloudwatch_log_group():
    """ecs.py must define a CloudWatch Log Group."""
    src = _ecs_source()
    assert "cloudwatch.LogGroup(" in src, "ecs.py must define cloudwatch.LogGroup"


def test_no_pseudopod_references():
    """All resource names must use 'myxo', not 'pseudopod'."""
    src = _ecs_source()
    assert "pseudopod" not in src.lower()


def test_myxo_naming():
    """Key resources must include 'myxo' in their names."""
    src = _ecs_source()
    assert "myxo-cluster" in src
    assert "myxo-base" in src
    assert "/ecs/myxo" in src


def test_main_imports_ecs_module():
    """__main__.py must import or reference the ECS module."""
    main_src = (INFRA_DIR / "__main__.py").read_text()
    assert "ecs" in main_src.lower()


def test_exports_key_outputs():
    """ecs.py must export cluster name, ECR URL, and task definition ARN."""
    src = _ecs_source()
    assert "pulumi.export(" in src
    assert "cluster" in src.lower() and "export" in src.lower()
    assert "ecr" in src.lower() and "url" in src.lower()
    assert "task" in src.lower() and "arn" in src.lower()


# ---------------------------------------------------------------------------
# Fargate Spot capacity provider (#137)
# ---------------------------------------------------------------------------


def test_defines_cluster_capacity_providers():
    """ecs.py must reference ClusterCapacityProviders."""
    src = _ecs_source()
    assert "ClusterCapacityProviders" in src


def test_contains_fargate_spot():
    """ecs.py must contain FARGATE_SPOT."""
    src = _ecs_source()
    assert "FARGATE_SPOT" in src


def test_default_capacity_provider_strategy():
    """ecs.py must define a default capacity provider strategy."""
    src = _ecs_source()
    assert "default_capacity_provider_strategies" in src


# ---------------------------------------------------------------------------
# EFS Nix cache (#137)
# ---------------------------------------------------------------------------


def test_defines_efs_file_system():
    """ecs.py must define an EFS FileSystem resource."""
    src = _ecs_source()
    assert "aws.efs.FileSystem(" in src, "ecs.py must define aws.efs.FileSystem"


def test_defines_efs_access_point():
    """ecs.py must define an EFS AccessPoint resource."""
    src = _ecs_source()
    assert "aws.efs.AccessPoint(" in src, "ecs.py must define aws.efs.AccessPoint"


def test_task_definition_has_volume():
    """Task definition must include a volume configuration for EFS."""
    src = _ecs_source()
    assert "nix-cache" in src, "Task definition must reference nix-cache volume"
    assert "efs_volume_configuration" in src or "EfsVolumeConfiguration" in src


def test_efs_resources_use_myxo_naming():
    """EFS resources must use 'myxo' in their names."""
    src = _ecs_source()
    assert "myxo-nix-cache" in src, "EFS file system must be named myxo-nix-cache"


def test_exports_efs_file_system_id():
    """ecs.py must export the EFS file system ID."""
    src = _ecs_source()
    assert "efs_file_system_id" in src, "Must export efs_file_system_id"
