"""Tests for CHANGELOG and release workflow configuration."""

import re
from pathlib import Path

from helpers import get_on_block, is_sha_pinned, load_workflow

ROOT = Path(__file__).parent.parent
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "release.yml"


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
    data = load_workflow(WORKFLOW_PATH)
    on_block = get_on_block(data)
    push = on_block.get("push", {})
    tags = push.get("tags", [])
    assert any("v*" in t or "v**" in t for t in tags), "Must trigger on v* tag push"


def test_release_has_permissions():
    data = load_workflow(WORKFLOW_PATH)
    permissions = data.get("permissions", {})
    assert "contents" in permissions, "Must declare contents permission"


def test_release_has_concurrency():
    data = load_workflow(WORKFLOW_PATH)
    assert "concurrency" in data, "Must have concurrency block"
    concurrency = data["concurrency"]
    assert "group" in concurrency


def test_release_all_actions_sha_pinned():
    data = load_workflow(WORKFLOW_PATH)
    for job_name, job in data.get("jobs", {}).items():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses and "/" in uses:
                assert is_sha_pinned(uses), f"Action must be SHA-pinned in job '{job_name}', got: {uses}"


def test_release_creates_github_release():
    """Release job must create a GitHub release (via gh CLI or action)."""
    data = load_workflow(WORKFLOW_PATH)
    all_steps = []
    for job in data.get("jobs", {}).values():
        all_steps.extend(job.get("steps", []))

    run_cmds = [s.get("run", "") for s in all_steps]
    uses_refs = [s.get("uses", "") for s in all_steps]

    has_gh_release = any("gh release create" in cmd for cmd in run_cmds)
    has_release_action = any("action-gh-release" in ref for ref in uses_refs)

    assert has_gh_release or has_release_action, "Must create a GitHub release"
