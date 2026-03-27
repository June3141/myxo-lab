"""ECS Fargate infrastructure source-level tests.

Since we cannot run ``pulumi up`` in CI, these tests validate that the
infrastructure source code defines the expected AWS resources using
"myxo" naming throughout.

After #254 the monolithic ``ecs.py`` was decomposed into a package::

    infra/ecs/
    ├── __init__.py   (public re-exports)
    ├── ecr.py        (ECR repository)
    ├── cluster.py    (ECS Cluster + Capacity Provider)
    ├── efs.py        (EFS file system + access point)
    └── task.py       (Task Definition + Container Definition)
"""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"
ECS_PKG = INFRA_DIR / "ecs"


# ---------------------------------------------------------------------------
# Package structure (#254)
# ---------------------------------------------------------------------------


def test_ecs_is_package():
    """infra/ecs/ must be a Python package (directory with __init__.py)."""
    assert ECS_PKG.is_dir(), "infra/ecs/ must be a directory"
    assert (ECS_PKG / "__init__.py").is_file(), "infra/ecs/__init__.py must exist"


def test_ecs_submodules_exist():
    """All expected submodules must exist."""
    for name in ("ecr.py", "cluster.py", "efs.py", "task.py"):
        assert (ECS_PKG / name).is_file(), f"infra/ecs/{name} must exist"


def test_old_ecs_py_removed():
    """The monolithic infra/ecs.py must no longer exist."""
    assert not (INFRA_DIR / "ecs.py").is_file(), "infra/ecs.py should be removed after decomposition"


# ---------------------------------------------------------------------------
# ecr.py
# ---------------------------------------------------------------------------


def _ecr_source() -> str:
    return (ECS_PKG / "ecr.py").read_text()


def test_ecr_defines_repository():
    """ecr.py must define an ECR Repository resource."""
    src = _ecr_source()
    assert "ecr.Repository(" in src, "ecr.py must define ecr.Repository"


def test_ecr_myxo_naming():
    """ecr.py must use 'myxo-base' naming."""
    src = _ecr_source()
    assert "myxo-base" in src


# ---------------------------------------------------------------------------
# cluster.py
# ---------------------------------------------------------------------------


def _cluster_source() -> str:
    return (ECS_PKG / "cluster.py").read_text()


def test_cluster_defines_ecs_cluster():
    """cluster.py must define an ECS Cluster resource."""
    src = _cluster_source()
    assert "ecs.Cluster(" in src, "cluster.py must define ecs.Cluster"


def test_cluster_defines_capacity_providers():
    """cluster.py must reference ClusterCapacityProviders."""
    src = _cluster_source()
    assert "ClusterCapacityProviders" in src


def test_cluster_contains_fargate_spot():
    """cluster.py must contain FARGATE_SPOT."""
    src = _cluster_source()
    assert "FARGATE_SPOT" in src


def test_cluster_default_capacity_provider_strategy():
    """cluster.py must define a default capacity provider strategy."""
    src = _cluster_source()
    assert "default_capacity_provider_strategies" in src


def test_cluster_myxo_naming():
    """cluster.py must use 'myxo-cluster' naming."""
    src = _cluster_source()
    assert "myxo-cluster" in src


# ---------------------------------------------------------------------------
# efs.py
# ---------------------------------------------------------------------------


def _efs_source() -> str:
    return (ECS_PKG / "efs.py").read_text()


def test_efs_defines_file_system():
    """efs.py must define an EFS FileSystem resource."""
    src = _efs_source()
    assert "aws.efs.FileSystem(" in src, "efs.py must define aws.efs.FileSystem"


def test_efs_defines_access_point():
    """efs.py must define an EFS AccessPoint resource."""
    src = _efs_source()
    assert "aws.efs.AccessPoint(" in src, "efs.py must define aws.efs.AccessPoint"


def test_efs_myxo_naming():
    """EFS resources must use 'myxo-nix-cache' naming."""
    src = _efs_source()
    assert "myxo-nix-cache" in src


# ---------------------------------------------------------------------------
# task.py
# ---------------------------------------------------------------------------


def _task_source() -> str:
    return (ECS_PKG / "task.py").read_text()


def test_task_defines_task_definition():
    """task.py must define an ECS Task Definition resource."""
    src = _task_source()
    assert "ecs.TaskDefinition(" in src, "task.py must define ecs.TaskDefinition"


def test_task_defines_iam_roles():
    """task.py must define IAM roles for task execution and task."""
    src = _task_source()
    assert "iam.Role(" in src, "task.py must define iam.Role"
    assert "task_execution_role" in src or "task-execution-role" in src
    assert "task_role" in src or "task-role" in src


def test_task_defines_cloudwatch_log_group():
    """task.py must define a CloudWatch Log Group."""
    src = _task_source()
    assert "common.create_log_group(" in src, "task.py must use common.create_log_group"


def test_task_has_volume():
    """Task definition must include a volume configuration for EFS."""
    src = _task_source()
    assert "nix-cache" in src, "Task definition must reference nix-cache volume"
    assert "efs_volume_configuration" in src or "EfsVolumeConfiguration" in src


def test_task_defines_cloudwatch_metric_filter():
    """task.py must define a CloudWatch metric filter."""
    src = _task_source()
    assert "LogMetricFilter(" in src


# ---------------------------------------------------------------------------
# __init__.py re-exports
# ---------------------------------------------------------------------------


def _init_source() -> str:
    return (ECS_PKG / "__init__.py").read_text()


def test_init_reexports_cluster():
    """__init__.py must re-export 'cluster'."""
    src = _init_source()
    assert "cluster" in src


def test_init_reexports_task_execution_role():
    """__init__.py must re-export 'task_execution_role'."""
    src = _init_source()
    assert "task_execution_role" in src


def test_init_reexports_task_role():
    """__init__.py must re-export 'task_role'."""
    src = _init_source()
    assert "task_role" in src


def test_init_reexports_task_definition():
    """__init__.py must re-export 'task_definition'."""
    src = _init_source()
    assert "task_definition" in src


def test_init_reexports_repo():
    """__init__.py must re-export 'repo'."""
    src = _init_source()
    assert "repo" in src


def test_init_reexports_nix_cache_fs():
    """__init__.py must re-export 'nix_cache_fs'."""
    src = _init_source()
    assert "nix_cache_fs" in src


def test_init_has_dunder_all():
    """__init__.py must define __all__ for ruff F401 suppression."""
    src = _init_source()
    assert "__all__" in src


def test_init_exports_key_outputs():
    """__init__.py or submodules must export cluster name, ECR URL, and task definition ARN via pulumi.export."""
    pkg_source = ""
    for f in ECS_PKG.glob("*.py"):
        pkg_source += f.read_text()
    assert "pulumi.export(" in pkg_source
    assert "cluster" in pkg_source.lower() and "export" in pkg_source.lower()
    assert "ecr" in pkg_source.lower() and "url" in pkg_source.lower()
    assert "task" in pkg_source.lower() and "arn" in pkg_source.lower()


# ---------------------------------------------------------------------------
# No legacy references
# ---------------------------------------------------------------------------


def test_no_pseudopod_references():
    """All resource names must use 'myxo', not 'pseudopod'."""
    for f in ECS_PKG.glob("*.py"):
        src = f.read_text()
        assert "pseudopod" not in src.lower(), f"{f.name} must not reference 'pseudopod'"


def test_myxo_naming():
    """Key resources must include 'myxo' in their names across the package."""
    pkg_source = ""
    for f in ECS_PKG.glob("*.py"):
        pkg_source += f.read_text()
    assert "myxo-cluster" in pkg_source
    assert "myxo-base" in pkg_source
    assert "/ecs/myxo" in pkg_source


def test_main_imports_ecs_module():
    """__main__.py must import or reference the ECS module."""
    main_src = (INFRA_DIR / "__main__.py").read_text()
    assert "ecs" in main_src.lower()
