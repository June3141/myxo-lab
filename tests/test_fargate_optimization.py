"""Fargate cost optimization tests (#137).

Validates that ECS infrastructure includes:
- Cost tags on cluster, task definition, and EFS resources
- ECR image scanning configuration (scan_on_push)
- CloudWatch metric filter for task execution time
- Fargate Spot capacity provider (already implemented)
"""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


def _ecs_source() -> str:
    return (INFRA_DIR / "ecs.py").read_text()


# ---------------------------------------------------------------------------
# Cost tags (#137)
# ---------------------------------------------------------------------------

_COST_TAGS = {
    "Project": "myxo-lab",
    "Environment": "dev",
    "CostCenter": "ai-agent",
}


def test_cluster_has_cost_tags():
    """ECS Cluster must have Project, Environment, CostCenter tags."""
    src = _ecs_source()
    for key, value in _COST_TAGS.items():
        assert f'"{key}"' in src, f"Cluster must have {key} tag"
        assert f'"{value}"' in src, f"Cluster must have {key}={value}"


def test_task_definition_has_cost_tags():
    """Task Definition must have cost tags (inline or via shared variable)."""
    src = _ecs_source()
    td_start = src.index("ecs.TaskDefinition(")
    td_section = src[td_start:]
    # Accept either inline tag literals or a reference to a shared tags dict
    has_inline = all(f'"{k}"' in td_section for k in _COST_TAGS)
    has_ref = "_COST_TAGS" in td_section
    assert has_inline or has_ref, "TaskDefinition must have cost tags"


def test_efs_has_cost_tags():
    """EFS FileSystem must have cost tags in addition to Name tag."""
    src = _ecs_source()
    efs_start = src.index("aws.efs.FileSystem(")
    # Use a generous slice to capture the full resource block
    efs_section = src[efs_start:efs_start + 400]
    has_inline = all(f'"{k}"' in efs_section for k in _COST_TAGS)
    has_ref = "_COST_TAGS" in efs_section
    assert has_inline or has_ref, "EFS must have cost tags"


# ---------------------------------------------------------------------------
# ECR image scanning (#137)
# ---------------------------------------------------------------------------


def test_ecr_scan_on_push_enabled():
    """ECR repository must have image scanning with scan_on_push=True."""
    src = _ecs_source()
    assert "image_scanning_configuration" in src, (
        "ECR must have image_scanning_configuration"
    )
    # Find the scanning config section and verify scan_on_push
    scan_idx = src.index("image_scanning_configuration")
    scan_section = src[scan_idx:scan_idx + 200]
    assert "scan_on_push" in scan_section, "Must set scan_on_push"
    assert "True" in scan_section, "scan_on_push must be True"


# ---------------------------------------------------------------------------
# CloudWatch metric filter for task execution (#137)
# ---------------------------------------------------------------------------


def test_cloudwatch_metric_filter_exists():
    """ecs.py must define a CloudWatch metric filter for task execution."""
    src = _ecs_source()
    assert "MetricFilter(" in src or "metric_filter" in src.lower(), (
        "Must define a CloudWatch metric filter"
    )


def test_metric_filter_references_log_group():
    """Metric filter must reference the ECS log group."""
    src = _ecs_source()
    assert "log_group" in src, "Metric filter must reference log_group"
    # Ensure it's connected to the myxo log group
    assert "myxo" in src


# ---------------------------------------------------------------------------
# Fargate Spot (verify existing, #137)
# ---------------------------------------------------------------------------


def test_fargate_spot_capacity_provider_exists():
    """ecs.py must configure FARGATE_SPOT capacity provider."""
    src = _ecs_source()
    assert "FARGATE_SPOT" in src
    assert "ClusterCapacityProviders" in src
