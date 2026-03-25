"""Tests for gitleaks secret scanning configuration and CI workflow."""

import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
GITLEAKS_TOML = ROOT / ".gitleaks.toml"
SECURITY_YML = ROOT / ".github" / "workflows" / "security.yml"


# ── .gitleaks.toml ──────────────────────────────────────────────


def test_gitleaks_toml_exists():
    assert GITLEAKS_TOML.is_file(), ".gitleaks.toml must exist at project root"


def test_gitleaks_toml_is_valid_toml():
    data = tomllib.loads(GITLEAKS_TOML.read_text())
    assert isinstance(data, dict)


def test_gitleaks_toml_has_allowlist():
    data = tomllib.loads(GITLEAKS_TOML.read_text())
    assert "allowlist" in data, ".gitleaks.toml must contain an [allowlist] section"


def test_gitleaks_toml_allowlist_has_paths():
    data = tomllib.loads(GITLEAKS_TOML.read_text())
    allowlist = data["allowlist"]
    assert "paths" in allowlist, "[allowlist] must define paths patterns"
    assert isinstance(allowlist["paths"], list)
    assert len(allowlist["paths"]) > 0


# ── .github/workflows/security.yml ─────────────────────────────


def test_security_workflow_exists():
    assert SECURITY_YML.is_file(), ".github/workflows/security.yml must exist"


def test_security_workflow_is_valid_yaml():
    data = yaml.safe_load(SECURITY_YML.read_text())
    assert isinstance(data, dict)


def test_security_workflow_has_name():
    data = yaml.safe_load(SECURITY_YML.read_text())
    assert "name" in data, "workflow must have a name"


def _get_triggers(data: dict) -> dict:
    """Return the workflow trigger dict, handling YAML 'on' -> True key."""
    # PyYAML parses bare `on:` as boolean True
    if "on" in data:
        return data["on"]
    if True in data:
        return data[True]
    raise KeyError("workflow has no 'on' trigger key")


def test_security_workflow_triggers_on_pull_request():
    data = yaml.safe_load(SECURITY_YML.read_text())
    triggers = _get_triggers(data)
    assert "pull_request" in triggers, "workflow must trigger on pull_request"


def test_security_workflow_pr_types():
    data = yaml.safe_load(SECURITY_YML.read_text())
    triggers = _get_triggers(data)
    pr_config = triggers["pull_request"]
    assert "types" in pr_config, "pull_request trigger must specify types"
    types = pr_config["types"]
    for expected in ("opened", "synchronize", "reopened"):
        assert expected in types, f"pull_request types must include '{expected}'"


def test_security_workflow_uses_gitleaks_action():
    content = SECURITY_YML.read_text()
    assert "gitleaks/gitleaks-action" in content, "workflow must reference gitleaks/gitleaks-action"


def test_security_workflow_gitleaks_action_v2():
    content = SECURITY_YML.read_text()
    assert "gitleaks/gitleaks-action@" in content, "workflow must use gitleaks-action"


def test_security_workflow_has_permissions():
    data = yaml.safe_load(SECURITY_YML.read_text())
    assert "permissions" in data, "workflow must define permissions block"
    assert data["permissions"]["contents"] == "read"


def test_security_workflow_references_gitleaks_config():
    content = SECURITY_YML.read_text()
    assert ".gitleaks.toml" in content, "workflow must reference .gitleaks.toml config"
