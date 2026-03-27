"""Tests for the label-triggered procedure workflow."""

from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).parent.parent / ".github" / "workflows" / "myxo-procedure.yml"


def test_workflow_file_exists():
    assert WORKFLOW.exists(), "myxo-procedure.yml should exist"


def test_workflow_is_valid_yaml():
    data = yaml.safe_load(WORKFLOW.read_text())
    assert isinstance(data, dict), "Workflow should parse as a YAML mapping"


def test_triggers_on_issues_labeled():
    data = yaml.safe_load(WORKFLOW.read_text())
    on = data.get("on") or data.get(True)  # YAML parses `on:` as True key
    assert "issues" in on, "Workflow should trigger on issues event"
    issues_config = on["issues"]
    assert "labeled" in issues_config.get("types", []), "Workflow should trigger on labeled type"


MYXO_LABELS = ["myxo-ready", "myxo-active", "myxo-complete", "myxo-abort"]


@pytest.mark.parametrize("label", MYXO_LABELS)
def test_references_myxo_label(label: str):
    content = WORKFLOW.read_text()
    assert f"state: {label}" in content, f"Workflow should reference the {label} label"


def test_uses_env_for_issue_data():
    """Workflow should use env: block for issue data instead of direct interpolation in run: blocks."""
    data = yaml.safe_load(WORKFLOW.read_text())
    content = WORKFLOW.read_text()

    # Collect all run: values from steps and verify none contain direct interpolation
    jobs = data.get("jobs", {})
    for job_name, job_config in jobs.items():
        for step in job_config.get("steps", []):
            run_value = step.get("run", "")
            assert "${{ github.event.issue" not in run_value, (
                f"Step '{step.get('name', 'unnamed')}' in job '{job_name}' "
                "should not contain direct ${{ github.event.issue }} interpolation in run:; "
                "use env: instead for security"
            )

    # Verify env: is actually used somewhere with issue data
    assert "env:" in content, "Workflow should use env: blocks for issue data"
    assert "github.event.issue" in content, "Workflow should reference github.event.issue (via env:)"
