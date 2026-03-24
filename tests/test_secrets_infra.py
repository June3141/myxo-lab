"""GitHub Secrets & Environments infrastructure source-level tests.

Since we cannot run ``pulumi up`` in CI, these tests validate that the
infrastructure source code defines the expected GitHub environments and
Actions secrets structure.
"""

import re
from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"


# ---------------------------------------------------------------------------
# Module existence
# ---------------------------------------------------------------------------


def test_secrets_module_exists():
    """infra/secrets.py must exist."""
    assert (INFRA_DIR / "secrets.py").is_file(), "infra/secrets.py must exist"


# ---------------------------------------------------------------------------
# Environment definitions
# ---------------------------------------------------------------------------


def _secrets_source() -> str:
    return (INFRA_DIR / "secrets.py").read_text()


def test_references_actions_environment():
    """secrets.py must reference GitHub Actions environments."""
    src = _secrets_source()
    assert "ActionsEnvironment" in src or "RepositoryEnvironment" in src or "actions_environment" in src, (
        "secrets.py must reference environment definitions"
    )


def test_defines_development_environment():
    """secrets.py must define a development environment."""
    src = _secrets_source()
    assert "development" in src.lower(), "secrets.py must define development environment"


def test_defines_staging_environment():
    """secrets.py must define a staging environment."""
    src = _secrets_source()
    assert "staging" in src.lower(), "secrets.py must define staging environment"


def test_defines_production_environment():
    """secrets.py must define a production environment."""
    src = _secrets_source()
    assert "production" in src.lower(), "secrets.py must define production environment"


# ---------------------------------------------------------------------------
# Secret definitions
# ---------------------------------------------------------------------------


def test_references_actions_secret():
    """secrets.py must reference GitHub Actions secrets."""
    src = _secrets_source()
    assert "ActionsSecret" in src or "actions_secret" in src, (
        "secrets.py must reference ActionsSecret or secret definitions"
    )


def test_defines_pulumi_access_token_secret():
    """secrets.py must define PULUMI_ACCESS_TOKEN secret."""
    src = _secrets_source()
    assert "PULUMI_ACCESS_TOKEN" in src


def test_defines_aws_access_key_id_secret():
    """secrets.py must define AWS_ACCESS_KEY_ID secret."""
    src = _secrets_source()
    assert "AWS_ACCESS_KEY_ID" in src


def test_defines_aws_secret_access_key_secret():
    """secrets.py must define AWS_SECRET_ACCESS_KEY secret."""
    src = _secrets_source()
    assert "AWS_SECRET_ACCESS_KEY" in src


# ---------------------------------------------------------------------------
# Security: no hardcoded secrets
# ---------------------------------------------------------------------------


def test_no_hardcoded_secret_values():
    """secrets.py must not contain hardcoded secret values (API keys, tokens)."""
    src = _secrets_source()
    # Patterns that look like real secret values (long hex/base64 strings)
    suspicious = re.findall(r'["\'][A-Za-z0-9+/]{32,}["\']', src)
    assert len(suspicious) == 0, f"secrets.py may contain hardcoded secret values: {suspicious}"


def test_uses_pulumi_config_for_secrets():
    """secrets.py must use pulumi.Config to retrieve secret values."""
    src = _secrets_source()
    assert "pulumi.Config" in src or "config.require_secret" in src or "config.get_secret" in src, (
        "secrets.py must use pulumi.Config for encrypted secret values"
    )


# ---------------------------------------------------------------------------
# Integration with __main__.py
# ---------------------------------------------------------------------------


def test_main_imports_secrets_module():
    """__main__.py must import or reference the secrets module."""
    main_src = (INFRA_DIR / "__main__.py").read_text()
    assert "secrets" in main_src, "__main__.py must import secrets module"
