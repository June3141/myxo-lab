"""Tests for GitHub App Token migration in workflows."""

import re
from pathlib import Path

import yaml

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"

# Workflows that need elevated permissions (issues/PR management)
APP_TOKEN_WORKFLOWS = [
    "myxo-verify.yml",
    "myxo-procedure.yml",
    "kanban-sync.yml",
]


def _load_workflow(name: str) -> dict:
    data = yaml.safe_load((WORKFLOWS_DIR / name).read_text())
    assert isinstance(data, dict)
    return data


def test_app_token_workflows_use_generate_step():
    """Workflows needing elevated permissions must generate an App token."""
    for wf_name in APP_TOKEN_WORKFLOWS:
        content = (WORKFLOWS_DIR / wf_name).read_text()
        assert "create-github-app-token" in content or "github-app-token" in content, (
            f"{wf_name} must use a GitHub App token generation action"
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
        assert "APP_ID" in content or "app-id" in content, f"{wf_name} must reference App ID"
        assert "PRIVATE_KEY" in content or "private-key" in content, f"{wf_name} must reference private key"
