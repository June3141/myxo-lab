"""Tests for CHANGELOG and release workflow configuration."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "release.yml"


def _load_workflow() -> dict:
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    assert isinstance(data, dict), "Workflow YAML must be a valid mapping"
    return data


def _get_on_block(data: dict) -> dict:
    return data.get(True, data.get("on", {}))


def _is_sha_pinned(ref: str) -> bool:
    _, _, version = ref.partition("@")
    return bool(re.fullmatch(r"[0-9a-f]{40}", version))


# ── CHANGELOG.md ──


def test_changelog_file_exists():
    assert CHANGELOG_PATH.is_file(), "CHANGELOG.md must exist at repository root"


def test_changelog_has_keep_a_changelog_header():
    text = CHANGELOG_PATH.read_text()
    assert "Keep a Changelog" in text, "CHANGELOG must reference Keep a Changelog format"


def test_changelog_has_semver_reference():
    text = CHANGELOG_PATH.read_text()
    assert "Semantic Versioning" in text, "CHANGELOG must reference Semantic Versioning"


def test_changelog_has_unreleased_section():
    text = CHANGELOG_PATH.read_text()
    assert "## [Unreleased]" in text, "CHANGELOG must have an [Unreleased] section"


def test_changelog_has_initial_release():
    text = CHANGELOG_PATH.read_text()
    assert re.search(r"## \[0\.1\.0\]", text), "CHANGELOG must have a 0.1.0 release entry"


# ── release.yml: structure ──


def test_release_workflow_exists():
    assert WORKFLOW_PATH.is_file(), "release.yml must exist"


def test_release_triggers_on_tag_push():
    data = _load_workflow()
    on_block = _get_on_block(data)
    push = on_block.get("push", {})
    tags = push.get("tags", [])
    assert any("v*" in t or "v**" in t for t in tags), "Must trigger on v* tag push"


def test_release_has_permissions():
    data = _load_workflow()
    permissions = data.get("permissions", {})
    assert "contents" in permissions, "Must declare contents permission"


def test_release_has_concurrency():
    data = _load_workflow()
    assert "concurrency" in data, "Must have concurrency block"
    concurrency = data["concurrency"]
    assert "group" in concurrency


def test_release_all_actions_sha_pinned():
    data = _load_workflow()
    for job_name, job in data.get("jobs", {}).items():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses and "/" in uses:
                assert _is_sha_pinned(uses), f"Action must be SHA-pinned in job '{job_name}', got: {uses}"


def test_release_creates_github_release():
    """Release job must create a GitHub release (via gh CLI or action)."""
    data = _load_workflow()
    all_steps = []
    for job in data.get("jobs", {}).values():
        all_steps.extend(job.get("steps", []))

    run_cmds = [s.get("run", "") for s in all_steps]
    uses_refs = [s.get("uses", "") for s in all_steps]

    has_gh_release = any("gh release create" in cmd for cmd in run_cmds)
    has_release_action = any("action-gh-release" in ref for ref in uses_refs)

    assert has_gh_release or has_release_action, "Must create a GitHub release"
