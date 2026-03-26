"""Tests for Pulumi preview CI workflow."""

import re
from pathlib import Path

from helpers import load_workflow

WORKFLOW_PATH = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "pulumi-preview.yml"


def test_workflow_file_exists_and_is_valid_yaml():
    """The workflow file must exist and be parseable YAML."""
    wf = load_workflow(WORKFLOW_PATH)
    assert isinstance(wf, dict)


def test_trigger_on_pull_request_with_paths_filter():
    """Workflow triggers on pull_request with paths filter for infra/**."""
    wf = load_workflow(WORKFLOW_PATH)
    # PyYAML parses bare `on` as boolean True
    pr_trigger = wf.get("on") or wf.get(True)
    pr_trigger = pr_trigger["pull_request"]
    assert "opened" in pr_trigger["types"]
    assert "synchronize" in pr_trigger["types"]
    assert "reopened" in pr_trigger["types"]
    assert "infra/**" in pr_trigger["paths"]


def test_references_pulumi_actions():
    """Workflow must use pulumi/actions for the preview step."""
    content = WORKFLOW_PATH.read_text()
    assert "pulumi/actions" in content


def test_permissions_are_correct():
    """Workflow needs contents:read and pull-requests:write."""
    wf = load_workflow(WORKFLOW_PATH)
    # Permissions can be at top-level or job-level
    perms = wf.get("permissions") or {}
    # Also check job-level permissions
    for job in wf.get("jobs", {}).values():
        if isinstance(job, dict) and "permissions" in job:
            perms.update(job["permissions"])
    if not perms:
        # Check top-level again
        perms = wf.get("permissions", {})
    assert perms.get("contents") == "read"
    assert perms.get("pull-requests") == "write"


def test_no_direct_interpolation_in_run_blocks():
    """No direct ${{ }} interpolation in run: blocks (security)."""
    wf = load_workflow(WORKFLOW_PATH)
    for job_name, job in wf.get("jobs", {}).items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps", []):
            if not isinstance(step, dict):
                continue
            run_block = step.get("run")
            if run_block is None:
                continue
            assert not re.search(r"\$\{\{", run_block), (
                f"Direct ${{{{ }}}} interpolation found in run block of job '{job_name}': {run_block!r}"
            )
