"""ECS Fargate infrastructure source-level tests.

Since we cannot run ``pulumi up`` in CI, these tests validate that the
infrastructure source code defines the expected AWS resources using
"myxo" naming throughout.
"""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


# ---------------------------------------------------------------------------
# Module existence
# ---------------------------------------------------------------------------


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
    assert "task_execution_role" in src or "task-execution-role" in src, (
        "ecs.py must define a task execution role"
    )
    assert "task_role" in src or "task-role" in src, (
        "ecs.py must define a task role"
    )


def test_defines_cloudwatch_log_group():
    """ecs.py must define a CloudWatch Log Group."""
    src = _ecs_source()
    assert "cloudwatch.LogGroup(" in src, "ecs.py must define cloudwatch.LogGroup"


# ---------------------------------------------------------------------------
# Naming convention — "myxo" not "pseudopod"
# ---------------------------------------------------------------------------


def test_no_pseudopod_references():
    """All resource names must use 'myxo', not 'pseudopod'."""
    src = _ecs_source()
    assert "pseudopod" not in src.lower(), (
        "ecs.py must not reference 'pseudopod' — use 'myxo' instead"
    )


def test_myxo_naming():
    """Key resources must include 'myxo' in their names."""
    src = _ecs_source()
    assert "myxo-cluster" in src, "ECS cluster must be named 'myxo-cluster'"
    assert "myxo-base" in src, "ECR repository must be named 'myxo-base'"
    assert "/ecs/myxo" in src, "CloudWatch log group must be '/ecs/myxo'"


# ---------------------------------------------------------------------------
# __main__.py imports ECS module
# ---------------------------------------------------------------------------


def test_main_imports_ecs_module():
    """__main__.py must import or reference the ECS module."""
    main_src = (INFRA_DIR / "__main__.py").read_text()
    assert "ecs" in main_src.lower(), (
        "__main__.py must import or reference the ECS module"
    )


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------


def test_exports_key_outputs():
    """ecs.py must export cluster name, ECR URL, and task definition ARN."""
    src = _ecs_source()
    assert "pulumi.export(" in src, "ecs.py must export Pulumi outputs"
    assert "cluster" in src.lower() and "export" in src.lower(), (
        "ecs.py must export cluster-related output"
    )
    assert "ecr" in src.lower() and "url" in src.lower(), (
        "ecs.py must export ECR URL"
    )
    assert "task" in src.lower() and "arn" in src.lower(), (
        "ecs.py must export task definition ARN"
    )
