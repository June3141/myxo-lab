"""Tests for GitHub App infrastructure module."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITHUB_APP_MODULE = ROOT / "infra" / "github_app.py"
MAIN_MODULE = ROOT / "infra" / "__main__.py"


def test_github_app_module_exists():
    assert GITHUB_APP_MODULE.is_file(), "infra/github_app.py must exist"


def test_github_app_imports_pulumi():
    content = GITHUB_APP_MODULE.read_text()
    assert "import pulumi" in content


def test_github_app_defines_permissions():
    content = GITHUB_APP_MODULE.read_text()
    for perm in ["issues", "pull_requests", "contents"]:
        assert perm in content, f"GitHub App must define {perm} permission"


def test_github_app_defines_webhook_events():
    content = GITHUB_APP_MODULE.read_text()
    assert "issues" in content
    assert "pull_request" in content


def test_main_imports_github_app():
    content = MAIN_MODULE.read_text()
    assert "github_app" in content, "__main__.py must import github_app module"
