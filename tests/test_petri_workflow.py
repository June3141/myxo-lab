"""Tests for Petri preview environment lifecycle workflow."""

import re
from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "petri-preview.yml"


def _load_workflow() -> dict:
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    assert isinstance(data, dict)
    return data


def _get_on_block(data: dict) -> dict:
    return data.get(True, data.get("on", {}))


def test_workflow_exists():
    assert WORKFLOW_PATH.is_file(), "petri-preview.yml must exist"


def test_triggers_on_pr_open_and_close():
    data = _load_workflow()
    on_block = _get_on_block(data)
    pr = on_block.get("pull_request", {})
    types = pr.get("types", [])
    assert "opened" in types, "Must trigger on PR opened"
    assert "closed" in types, "Must trigger on PR closed"


def test_has_deploy_job():
    data = _load_workflow()
    jobs = data.get("jobs", {})
    assert "deploy" in jobs or "preview-deploy" in jobs, "Must have a deploy job"


def test_has_cleanup_job():
    data = _load_workflow()
    jobs = data.get("jobs", {})
    assert "cleanup" in jobs or "preview-cleanup" in jobs, "Must have a cleanup job"


def test_cleanup_runs_on_pr_close():
    data = _load_workflow()
    jobs = data.get("jobs", {})
    cleanup_job = jobs.get("cleanup") or jobs.get("preview-cleanup")
    assert cleanup_job is not None
    condition = cleanup_job.get("if", "")
    assert "closed" in condition, "Cleanup must run only on PR close"


def test_uses_pr_number_for_naming():
    content = WORKFLOW_PATH.read_text()
    assert "pr_number" in content.lower() or "pr-number" in content.lower() or "number" in content, (
        "Must use PR number for resource naming"
    )


def test_has_permissions():
    data = _load_workflow()
    assert "permissions" in data


def test_actions_sha_pinned():
    content = WORKFLOW_PATH.read_text()
    # All uses: lines should be SHA-pinned
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("uses:") or stripped.startswith("- uses:"):
            uses_ref = stripped.split("uses:")[-1].strip()
            if "/" in uses_ref and "@" in uses_ref:
                _, _, ref = uses_ref.partition("@")
                assert re.fullmatch(r"[0-9a-f]{40}", ref.split()[0]), (
                    f"Action must be SHA-pinned: {uses_ref}"
                )
