"""ECS Fargate preview environment infrastructure source-level tests.

Validates that the preview environment Pulumi module defines the expected
resources for PR-specific ECS Fargate services (#73).
"""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


def test_preview_module_exists():
    """infra/preview.py must exist."""
    assert (INFRA_DIR / "preview.py").is_file(), "infra/preview.py must exist"


# ---------------------------------------------------------------------------
# Resource definitions in preview.py
# ---------------------------------------------------------------------------


def _preview_source() -> str:
    return (INFRA_DIR / "preview.py").read_text()


def test_preview_imports_pulumi_aws():
    """preview.py must import pulumi_aws."""
    src = _preview_source()
    assert "pulumi_aws" in src, "preview.py must import pulumi_aws"


def test_defines_preview_environment():
    """preview.py must define PreviewEnvironment class or function."""
    src = _preview_source()
    assert "PreviewEnvironment" in src, (
        "preview.py must define PreviewEnvironment"
    )


def test_defines_ecs_service():
    """preview.py must define an ECS Service resource."""
    src = _preview_source()
    assert "ecs.Service(" in src or "aws.ecs.Service(" in src, (
        "preview.py must define an ECS Service"
    )


def test_defines_security_group():
    """preview.py must define a Security Group for inbound traffic."""
    src = _preview_source()
    assert "SecurityGroup(" in src, (
        "preview.py must define a SecurityGroup"
    )


def test_security_group_allows_port_8080():
    """Security group must allow inbound on port 8080."""
    src = _preview_source()
    assert "8080" in src, "Security group must reference port 8080"


def test_uses_fargate_spot():
    """Preview service must use FARGATE_SPOT capacity provider."""
    src = _preview_source()
    assert "FARGATE_SPOT" in src, "Preview service must use FARGATE_SPOT"


def test_desired_count_is_one():
    """Preview service desired_count must be 1."""
    src = _preview_source()
    assert "desired_count=1" in src, "Preview service desired_count must be 1"


def test_parameterized_by_pr_number():
    """PreviewEnvironment must accept a PR number parameter."""
    src = _preview_source()
    assert "pr_number" in src, (
        "PreviewEnvironment must be parameterized by pr_number"
    )


def test_exports_service_url():
    """preview.py must export the service URL."""
    src = _preview_source()
    assert "pulumi.export(" in src, "preview.py must export a value"
    assert "url" in src.lower(), "preview.py must export a URL"


def test_main_imports_preview_module():
    """__main__.py must import the preview module."""
    main_src = (INFRA_DIR / "__main__.py").read_text()
    assert "preview" in main_src.lower(), (
        "__main__.py must import the preview module"
    )
