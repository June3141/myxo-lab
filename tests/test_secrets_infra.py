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
# Purpose-specific API key secrets (#28)
# ---------------------------------------------------------------------------


def test_defines_anthropic_api_key_myxo_secret():
    """secrets.py must define ANTHROPIC_API_KEY_MYXO for worker agent execution."""
    src = _secrets_source()
    assert "ANTHROPIC_API_KEY_MYXO" in src


def test_defines_anthropic_api_key_scheduled_secret():
    """secrets.py must define ANTHROPIC_API_KEY_SCHEDULED for cron tasks."""
    src = _secrets_source()
    assert "ANTHROPIC_API_KEY_SCHEDULED" in src


def test_defines_github_app_private_key_secret():
    """secrets.py must define GITHUB_APP_PRIVATE_KEY for GitHub App token generation."""
    src = _secrets_source()
    assert "GITHUB_APP_PRIVATE_KEY" in src


def test_all_new_secrets_use_require_secret():
    """All purpose-specific secrets must use require_secret (no plaintext)."""
    src = _secrets_source()
    new_secret_names = [
        "ANTHROPIC_API_KEY_MYXO",
        "ANTHROPIC_API_KEY_SCHEDULED",
        "GITHUB_APP_PRIVATE_KEY",
    ]
    for name in new_secret_names:
        pattern = rf'require_secret\(\s*"{name}"\s*\)'
        assert re.search(pattern, src), (
            f"{name} must be loaded via require_secret(), not plaintext"
        )


def test_purpose_based_naming_pattern():
    """SECRET_DEFS must contain keys matching purpose-based naming (MYXO, SCHEDULED, APP)."""
    src = _secrets_source()
    # Extract keys from SECRET_DEFS dict
    secret_def_keys = re.findall(r'"([A-Z_]+)":\s*\w+', src)
    purpose_keywords = {"MYXO", "SCHEDULED", "APP"}
    found = {kw for kw in purpose_keywords if any(kw in k for k in secret_def_keys)}
    assert found == purpose_keywords, (
        f"SECRET_DEFS must contain purpose-based keys with {purpose_keywords}, "
        f"but only found {found}"
    )


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
