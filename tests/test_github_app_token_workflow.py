"""Tests for GitHub App Token migration in workflows."""

import re
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"

# Workflows that need elevated permissions (issues/PR management)
APP_TOKEN_WORKFLOWS = [
    "myxo-verify.yml",
    "myxo-procedure.yml",
    "kanban-sync.yml",
]


def test_app_token_workflows_use_generate_step():
    """Workflows needing elevated permissions must generate an App token."""
    for wf_name in APP_TOKEN_WORKFLOWS:
        content = (WORKFLOWS_DIR / wf_name).read_text()
        assert "create-github-app-token" in content, (
            f"{wf_name} must use create-github-app-token action"
        )


def test_app_token_action_is_sha_pinned():
    """The App token action must be SHA-pinned."""
    for wf_name in APP_TOKEN_WORKFLOWS:
        content = (WORKFLOWS_DIR / wf_name).read_text()
        assert re.search(r"create-github-app-token@[0-9a-f]{40}", content), (
            f"{wf_name} must SHA-pin the App token action"
        )


def test_app_token_uses_secrets():
    """App token step must reference APP_ID and PRIVATE_KEY secrets."""
    for wf_name in APP_TOKEN_WORKFLOWS:
        content = (WORKFLOWS_DIR / wf_name).read_text()
        assert "MYXO_APP_ID" in content, f"{wf_name} must reference MYXO_APP_ID secret"
        assert "GITHUB_APP_PRIVATE_KEY" in content, f"{wf_name} must reference GITHUB_APP_PRIVATE_KEY secret"


def test_no_legacy_token_in_migrated_workflows():
    """Migrated workflows must not use github.token or secrets.GITHUB_TOKEN for GH_TOKEN."""
    for wf_name in APP_TOKEN_WORKFLOWS:
        content = (WORKFLOWS_DIR / wf_name).read_text()
        assert "github.token" not in content, f"{wf_name} must not use github.token"
        assert "secrets.GITHUB_TOKEN" not in content, f"{wf_name} must not use secrets.GITHUB_TOKEN"


def test_gh_token_uses_app_token_output():
    """GH_TOKEN must be sourced from steps.app-token.outputs.token."""
    for wf_name in APP_TOKEN_WORKFLOWS:
        content = (WORKFLOWS_DIR / wf_name).read_text()
        assert "steps.app-token.outputs.token" in content, (
            f"{wf_name} GH_TOKEN must use steps.app-token.outputs.token"
        )
