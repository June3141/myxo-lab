"""Tests for SecureFilesystemMCP file access allowlist."""

import pytest

from myxo.secure_filesystem import SecureFilesystemMCP


# ---------------------------------------------------------------------------
# Default patterns used across tests
# ---------------------------------------------------------------------------

BLOCKED_PATTERNS = [
    ".env*",
    "secrets/**",
    "credentials/**",
    "*.pem",
    "*.key",
]

ALLOWED_PATTERNS = [
    "src/**",
    "tests/**",
    "*.py",
    "*.toml",
    "*.yaml",
    "*.yml",
    "*.json",
    "*.cfg",
]


@pytest.fixture()
def mcp() -> SecureFilesystemMCP:
    return SecureFilesystemMCP(
        allowed_patterns=ALLOWED_PATTERNS,
        blocked_patterns=BLOCKED_PATTERNS,
    )


# ===== check_access: allowed paths =====


def test_python_file_in_src(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("src/myxo/cli.py") is True


def test_python_file_in_tests(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("tests/test_cli.py") is True


def test_toml_config(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("pyproject.toml") is True


def test_yaml_config(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("config.yaml") is True


def test_yml_config(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("config.yml") is True


def test_json_config(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("settings.json") is True


def test_cfg_file(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("setup.cfg") is True


def test_nested_src_file(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("src/myxo/subdir/module.py") is True


# ===== check_access: blocked paths =====


def test_env_file(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access(".env") is False


def test_env_local(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access(".env.local") is False


def test_env_production(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access(".env.production") is False


def test_secrets_dir(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("secrets/api_key.txt") is False


def test_credentials_dir(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("credentials/token.json") is False


def test_pem_file(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("server.pem") is False


def test_key_file(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("private.key") is False


def test_pem_in_src(mcp: SecureFilesystemMCP) -> None:
    """Blocked patterns take priority over allowed patterns."""
    assert mcp.check_access("src/certs/server.pem") is False


def test_env_in_tests(mcp: SecureFilesystemMCP) -> None:
    """Blocked patterns take priority even inside allowed dirs."""
    assert mcp.check_access("tests/.env") is False


# ===== check_access: not in allowed list =====


def test_random_txt_file(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("notes.txt") is False


def test_binary_file(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("program.exe") is False


def test_markdown_outside_src(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("docs/readme.md") is False


# ===== blocked_patterns priority over allowed_patterns =====


def test_key_in_allowed_dir(mcp: SecureFilesystemMCP) -> None:
    assert mcp.check_access("src/myxo/service.key") is False


def test_secrets_json_matches_both(mcp: SecureFilesystemMCP) -> None:
    """secrets/config.json matches allowed *.json AND blocked secrets/**."""
    assert mcp.check_access("secrets/config.json") is False


# ===== validate_access =====


def test_validate_allowed_path_does_not_raise(mcp: SecureFilesystemMCP) -> None:
    mcp.validate_access("src/myxo/cli.py")  # should not raise


def test_validate_blocked_path_raises_permission_error(
    mcp: SecureFilesystemMCP,
) -> None:
    with pytest.raises(PermissionError):
        mcp.validate_access(".env")


def test_validate_not_allowed_path_raises_permission_error(
    mcp: SecureFilesystemMCP,
) -> None:
    with pytest.raises(PermissionError):
        mcp.validate_access("notes.txt")


def test_validate_error_message_contains_path(mcp: SecureFilesystemMCP) -> None:
    with pytest.raises(PermissionError, match="private.key"):
        mcp.validate_access("private.key")


# ===== constructor stores patterns =====


def test_stores_allowed_patterns(mcp: SecureFilesystemMCP) -> None:
    assert mcp.allowed_patterns == ALLOWED_PATTERNS


def test_stores_blocked_patterns(mcp: SecureFilesystemMCP) -> None:
    assert mcp.blocked_patterns == BLOCKED_PATTERNS


def test_empty_patterns() -> None:
    fs = SecureFilesystemMCP(allowed_patterns=[], blocked_patterns=[])
    # Nothing is allowed when allowed list is empty
    assert fs.check_access("anything.py") is False


def test_no_blocked_patterns() -> None:
    fs = SecureFilesystemMCP(allowed_patterns=["*.py"], blocked_patterns=[])
    assert fs.check_access("main.py") is True


# ===== path normalization (Windows-style backslashes & absolute paths) =====


def test_backslash_path_allowed(mcp: SecureFilesystemMCP) -> None:
    """Windows-style backslash path should be normalized and matched."""
    assert mcp.check_access("src\\myxo\\cli.py") is True


def test_backslash_path_blocked(mcp: SecureFilesystemMCP) -> None:
    """Blocked patterns should catch backslash paths too."""
    assert mcp.check_access("src\\certs\\server.pem") is False


def test_backslash_secrets_blocked(mcp: SecureFilesystemMCP) -> None:
    """Directory-based blocked pattern must work with backslash separators."""
    assert mcp.check_access("secrets\\api_key.txt") is False


def test_mixed_separators(mcp: SecureFilesystemMCP) -> None:
    """Paths mixing forward and back slashes should be normalized."""
    assert mcp.check_access("src\\myxo/module.py") is True


def test_absolute_posix_path_allowed(mcp: SecureFilesystemMCP) -> None:
    """Absolute POSIX path containing an allowed subtree."""
    fs = SecureFilesystemMCP(
        allowed_patterns=["src/**"],
        blocked_patterns=[],
    )
    # Absolute path — the 'src' component still appears, so sub-path matching works
    assert fs.check_access("/home/user/project/src/main.py") is True


def test_absolute_windows_path_blocked(mcp: SecureFilesystemMCP) -> None:
    """Absolute Windows-style path with a blocked filename."""
    assert mcp.check_access("C:\\Users\\dev\\project\\private.key") is False


# ===== broad glob does not bypass blocked patterns =====


def test_broad_glob_does_not_bypass_blocked_env(mcp: SecureFilesystemMCP) -> None:
    """*.py glob in allowed should not let .env* slip through."""
    assert mcp.check_access("src/.env.local") is False


def test_broad_glob_does_not_bypass_blocked_pem(mcp: SecureFilesystemMCP) -> None:
    """Even deeply nested .pem files must be blocked."""
    assert mcp.check_access("src/deep/nested/cert.pem") is False


def test_broad_glob_does_not_bypass_blocked_key(mcp: SecureFilesystemMCP) -> None:
    """Even deeply nested .key files must be blocked."""
    assert mcp.check_access("tests/fixtures/server.key") is False
