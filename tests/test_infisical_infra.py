"""Tests for Infisical server infrastructure module.

Validates that infra/infisical.py defines an ECS Fargate service
for self-hosted Infisical with the expected resource definitions.
"""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"
INFISICAL_MODULE = INFRA_DIR / "infisical.py"
MAIN_MODULE = INFRA_DIR / "__main__.py"


def _infisical_source() -> str:
    return INFISICAL_MODULE.read_text()


# ---------------------------------------------------------------------------
# Module existence
# ---------------------------------------------------------------------------


def test_infisical_module_exists():
    """infra/infisical.py must exist."""
    assert INFISICAL_MODULE.is_file(), "infra/infisical.py must exist"


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------


def test_infisical_imports_pulumi_aws():
    """infisical.py must import pulumi_aws."""
    src = _infisical_source()
    assert "import pulumi_aws" in src, "infisical.py must import pulumi_aws"


# ---------------------------------------------------------------------------
# ECS resources
# ---------------------------------------------------------------------------


def test_defines_ecs_service_or_task_definition():
    """infisical.py must define an ECS Service or TaskDefinition for Infisical."""
    src = _infisical_source()
    has_service = "ecs.Service(" in src
    has_task_def = "ecs.TaskDefinition(" in src
    assert has_service or has_task_def, "infisical.py must define ecs.Service or ecs.TaskDefinition"


def test_defines_task_definition():
    """infisical.py must define an ECS TaskDefinition."""
    src = _infisical_source()
    assert "ecs.TaskDefinition(" in src, "infisical.py must define ecs.TaskDefinition for Infisical"


def test_defines_ecs_service():
    """infisical.py must define an ECS Service."""
    src = _infisical_source()
    assert "ecs.Service(" in src, "infisical.py must define ecs.Service for Infisical"


# ---------------------------------------------------------------------------
# Security group
# ---------------------------------------------------------------------------


def test_defines_security_group():
    """infisical.py must define a Security Group allowing inbound 443."""
    src = _infisical_source()
    assert "SecurityGroup(" in src, "infisical.py must define a SecurityGroup"
    assert "443" in src, "Security group must allow inbound port 443"


# ---------------------------------------------------------------------------
# Infisical naming
# ---------------------------------------------------------------------------


def test_infisical_naming():
    """Key resources must include 'infisical' in their names."""
    src = _infisical_source()
    assert "infisical" in src.lower(), "Resources must reference infisical"


# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------


def test_contains_mongo_url_env_var():
    """Container definition must reference MONGO_URL environment variable."""
    src = _infisical_source()
    assert "MONGO_URL" in src, "Container definition must include MONGO_URL environment variable"


# ---------------------------------------------------------------------------
# __main__.py integration
# ---------------------------------------------------------------------------


def test_main_imports_infisical():
    """__main__.py must import the infisical module."""
    content = MAIN_MODULE.read_text()
    assert "import infisical" in content, "__main__.py must import infisical module"
