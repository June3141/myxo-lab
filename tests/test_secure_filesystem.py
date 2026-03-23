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


@pytest.fixture
def mcp() -> SecureFilesystemMCP:
    return SecureFilesystemMCP(
        allowed_patterns=ALLOWED_PATTERNS,
        blocked_patterns=BLOCKED_PATTERNS,
    )


# ===== check_access: allowed paths =====


class TestCheckAccessAllowed:
    def test_python_file_in_src(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("src/myxo/cli.py") is True

    def test_python_file_in_tests(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("tests/test_cli.py") is True

    def test_toml_config(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("pyproject.toml") is True

    def test_yaml_config(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("config.yaml") is True

    def test_yml_config(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("config.yml") is True

    def test_json_config(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("settings.json") is True

    def test_cfg_file(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("setup.cfg") is True

    def test_nested_src_file(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("src/myxo/subdir/module.py") is True


# ===== check_access: blocked paths =====


class TestCheckAccessBlocked:
    def test_env_file(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access(".env") is False

    def test_env_local(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access(".env.local") is False

    def test_env_production(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access(".env.production") is False

    def test_secrets_dir(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("secrets/api_key.txt") is False

    def test_credentials_dir(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("credentials/token.json") is False

    def test_pem_file(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("server.pem") is False

    def test_key_file(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("private.key") is False

    def test_pem_in_src(self, mcp: SecureFilesystemMCP) -> None:
        """Blocked patterns take priority over allowed patterns."""
        assert mcp.check_access("src/certs/server.pem") is False

    def test_env_in_tests(self, mcp: SecureFilesystemMCP) -> None:
        """Blocked patterns take priority even inside allowed dirs."""
        assert mcp.check_access("tests/.env") is False


# ===== check_access: not in allowed list =====


class TestCheckAccessNotAllowed:
    def test_random_txt_file(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("notes.txt") is False

    def test_binary_file(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("program.exe") is False

    def test_markdown_outside_src(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("docs/readme.md") is False


# ===== blocked_patterns priority over allowed_patterns =====


class TestBlockedPriority:
    def test_key_in_allowed_dir(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.check_access("src/myxo/service.key") is False

    def test_secrets_json_matches_both(self, mcp: SecureFilesystemMCP) -> None:
        """secrets/config.json matches allowed *.json AND blocked secrets/**."""
        assert mcp.check_access("secrets/config.json") is False


# ===== validate_access =====


class TestValidateAccess:
    def test_allowed_path_does_not_raise(self, mcp: SecureFilesystemMCP) -> None:
        mcp.validate_access("src/myxo/cli.py")  # should not raise

    def test_blocked_path_raises_permission_error(
        self, mcp: SecureFilesystemMCP
    ) -> None:
        with pytest.raises(PermissionError):
            mcp.validate_access(".env")

    def test_not_allowed_path_raises_permission_error(
        self, mcp: SecureFilesystemMCP
    ) -> None:
        with pytest.raises(PermissionError):
            mcp.validate_access("notes.txt")

    def test_error_message_contains_path(self, mcp: SecureFilesystemMCP) -> None:
        with pytest.raises(PermissionError, match="private.key"):
            mcp.validate_access("private.key")


# ===== constructor stores patterns =====


class TestConstructor:
    def test_stores_allowed_patterns(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.allowed_patterns == ALLOWED_PATTERNS

    def test_stores_blocked_patterns(self, mcp: SecureFilesystemMCP) -> None:
        assert mcp.blocked_patterns == BLOCKED_PATTERNS

    def test_empty_patterns(self) -> None:
        fs = SecureFilesystemMCP(allowed_patterns=[], blocked_patterns=[])
        # Nothing is allowed when allowed list is empty
        assert fs.check_access("anything.py") is False

    def test_no_blocked_patterns(self) -> None:
        fs = SecureFilesystemMCP(allowed_patterns=["*.py"], blocked_patterns=[])
        assert fs.check_access("main.py") is True
