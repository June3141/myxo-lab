"""Tests for CI pipeline optimization strategy."""

from pathlib import Path

import yaml

WORKFLOWS_DIR = Path(__file__).parent.parent / ".github" / "workflows"


def _load_workflow(name: str) -> dict:
    path = WORKFLOWS_DIR / name
    data = yaml.safe_load(path.read_text())
    assert isinstance(data, dict)
    return data


def _get_triggers(data: dict) -> dict:
    """Return the workflow trigger dict, handling YAML 'on' -> True key."""
    if "on" in data:
        return data["on"]
    if True in data:
        return data[True]
    raise KeyError("workflow has no 'on' trigger key")


# ---------------------------------------------------------------------------
# uv cache — all setup-uv steps should enable caching
# ---------------------------------------------------------------------------


def test_lint_workflow_uses_uv_cache():
    content = (WORKFLOWS_DIR / "lint.yml").read_text()
    assert "enable-cache: true" in content, "lint.yml should enable uv cache"


def test_pulumi_preview_uses_uv_cache():
    content = (WORKFLOWS_DIR / "pulumi-preview.yml").read_text()
    assert "enable-cache: true" in content, "pulumi-preview.yml should enable uv cache"


# ---------------------------------------------------------------------------
# paths filter — lint.yml should only run on relevant changes
# ---------------------------------------------------------------------------


def test_lint_workflow_has_paths_filter():
    data = _load_workflow("lint.yml")
    triggers = _get_triggers(data)
    pr_config = triggers.get("pull_request", {})
    assert "paths" in pr_config, "lint.yml should have paths filter on pull_request"


def test_lint_workflow_paths_include_src_and_tests():
    data = _load_workflow("lint.yml")
    triggers = _get_triggers(data)
    paths = triggers["pull_request"]["paths"]
    path_str = " ".join(paths)
    assert "src/" in path_str or "src/**" in path_str, "paths should include src/"
    assert "tests/" in path_str or "tests/**" in path_str, "paths should include tests/"
    assert "pyproject.toml" in path_str, "paths should include pyproject.toml"
    assert "lint.yml" in path_str, "paths should include the workflow file itself"


# ---------------------------------------------------------------------------
# pr-title-lint.yml should use setup-uv for consistency
# ---------------------------------------------------------------------------


def test_pr_title_lint_uses_setup_uv():
    content = (WORKFLOWS_DIR / "pr-title-lint.yml").read_text()
    assert "astral-sh/setup-uv" in content, "pr-title-lint.yml should use setup-uv"
    assert "actions/setup-python" not in content, "pr-title-lint.yml should not use setup-python"
