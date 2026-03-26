"""Tests for Infisical client configuration module.

Validates that infra/infisical_client.py defines the configuration layer
for dynamic secret retrieval via the Infisical SDK, replacing hardcoded
GitHub Actions secrets.

Ref: #87
"""

import re
from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"
CLIENT_MODULE = INFRA_DIR / "infisical_client.py"
MAIN_MODULE = INFRA_DIR / "__main__.py"


def _client_source() -> str:
    return CLIENT_MODULE.read_text()


# ---------------------------------------------------------------------------
# Module existence
# ---------------------------------------------------------------------------


def test_infisical_client_module_exists():
    """infra/infisical_client.py must exist."""
    assert CLIENT_MODULE.is_file(), "infra/infisical_client.py must exist"


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------


def test_imports_pulumi():
    """infisical_client.py must import pulumi for config/exports."""
    src = _client_source()
    assert "import pulumi" in src, "infisical_client.py must import pulumi"


# ---------------------------------------------------------------------------
# Secret mapping / migration config
# ---------------------------------------------------------------------------


def test_defines_secret_mapping():
    """infisical_client.py must define a mapping of secrets for migration."""
    src = _client_source()
    has_mapping = "INFISICAL_SECRETS" in src or "SECRET_MAPPING" in src
    assert has_mapping, "infisical_client.py must define INFISICAL_SECRETS or SECRET_MAPPING"


def test_secret_mapping_includes_anthropic_keys():
    """Secret mapping must include Anthropic API keys for dynamic retrieval."""
    src = _client_source()
    assert "ANTHROPIC_API_KEY_MYXO" in src, "Secret mapping must include ANTHROPIC_API_KEY_MYXO"
    assert "ANTHROPIC_API_KEY_SCHEDULED" in src, "Secret mapping must include ANTHROPIC_API_KEY_SCHEDULED"


def test_secret_mapping_categorizes_sources():
    """Secret mapping must indicate source (infisical vs github_secrets)."""
    src = _client_source()
    has_source = "infisical" in src.lower() and (
        "github_secrets" in src or "github-secrets" in src or "GITHUB_SECRETS" in src
    )
    assert has_source, "Secret mapping must categorize secrets by source (infisical vs github_secrets)"


# ---------------------------------------------------------------------------
# Infisical project / environment references
# ---------------------------------------------------------------------------


def test_references_infisical_project():
    """infisical_client.py must use Pulumi config for project ID."""
    src = _client_source()
    assert 'get_secret("PROJECT_ID")' in src, "Must use config.get_secret for PROJECT_ID"


def test_references_infisical_environment():
    """infisical_client.py must use ENVIRONMENT_MAP for stack-to-env mapping."""
    src = _client_source()
    assert "ENVIRONMENT_MAP" in src, "Must define ENVIRONMENT_MAP"
    assert "pulumi.get_stack()" in src, "Must use pulumi.get_stack() for environment selection"


def test_environment_values():
    """infisical_client.py must define dev/staging/prod environments."""
    src = _client_source()
    for env in ("dev", "staging", "prod"):
        assert env in src.lower(), f"infisical_client.py must reference '{env}' environment"


# ---------------------------------------------------------------------------
# Security: no hardcoded secrets
# ---------------------------------------------------------------------------


def test_no_hardcoded_secret_values():
    """infisical_client.py must not contain hardcoded secret values."""
    src = _client_source()
    suspicious = re.findall(r'["\'][A-Za-z0-9+/]{32,}["\']', src)
    assert len(suspicious) == 0, f"infisical_client.py may contain hardcoded secret values: {suspicious}"


# ---------------------------------------------------------------------------
# Pulumi config for Infisical client credentials
# ---------------------------------------------------------------------------


def test_uses_pulumi_config():
    """infisical_client.py must use pulumi.Config for client credentials."""
    src = _client_source()
    assert "pulumi.Config" in src, "infisical_client.py must use pulumi.Config for credentials"


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------


def test_exports_configuration():
    """infisical_client.py must export configuration via pulumi.export."""
    src = _client_source()
    assert "pulumi.export" in src, "infisical_client.py must export configuration"


# ---------------------------------------------------------------------------
# __main__.py integration
# ---------------------------------------------------------------------------


def test_main_imports_infisical_client():
    """__main__.py must import the infisical_client module."""
    content = MAIN_MODULE.read_text()
    assert "infisical_client" in content, "__main__.py must import infisical_client module"
