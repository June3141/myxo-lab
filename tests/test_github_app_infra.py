"""Tests for GitHub App infrastructure module."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITHUB_APP_MODULE = ROOT / "infra" / "github_app.py"
MAIN_MODULE = ROOT / "infra" / "__main__.py"

EXPECTED_PERMISSIONS = {"issues", "pull_requests", "contents", "actions"}
EXPECTED_EVENTS = {"issues", "pull_request", "push", "workflow_run"}


def test_github_app_module_exists():
    assert GITHUB_APP_MODULE.is_file(), "infra/github_app.py must exist"


def test_github_app_imports_pulumi():
    content = GITHUB_APP_MODULE.read_text()
    assert "import pulumi" in content


def test_github_app_defines_all_permissions():
    content = GITHUB_APP_MODULE.read_text()
    for perm in EXPECTED_PERMISSIONS:
        assert f'"{perm}"' in content, f"PERMISSIONS must include {perm}"


def test_github_app_defines_all_webhook_events():
    content = GITHUB_APP_MODULE.read_text()
    for event in EXPECTED_EVENTS:
        assert f'"{event}"' in content, f"WEBHOOK_EVENTS must include {event}"


def test_main_imports_github_app():
    content = MAIN_MODULE.read_text()
    assert "import github_app" in content, "__main__.py must import github_app module"
