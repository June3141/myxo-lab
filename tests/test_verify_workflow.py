"""Tests for weekly mxl verify CI workflow."""

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "myxo-verify.yml"


def _load_workflow() -> dict:
    """Load workflow YAML, handling 'on' key parsed as boolean True."""
    return yaml.safe_load(WORKFLOW_PATH.read_text())


def _get_on_block(data: dict) -> dict:
    """Get the 'on' trigger block (YAML parses bare 'on' as True)."""
    return data.get(True, data.get("on", {}))


def test_workflow_file_exists():
    assert WORKFLOW_PATH.is_file(), "myxo-verify.yml must exist"


def test_workflow_is_valid_yaml():
    data = _load_workflow()
    assert isinstance(data, dict), "Workflow must be a valid YAML mapping"


def test_has_schedule_trigger_with_cron():
    data = _load_workflow()
    on_block = _get_on_block(data)
    schedule = on_block.get("schedule")
    assert schedule is not None, "Must have schedule trigger"
    assert isinstance(schedule, list), "schedule must be a list"
    crons = [entry.get("cron", "") for entry in schedule]
    assert any(crons), "schedule must contain at least one cron expression"


def test_has_workflow_dispatch_trigger():
    data = _load_workflow()
    on_block = _get_on_block(data)
    assert "workflow_dispatch" in on_block, "Must have workflow_dispatch trigger"


def test_references_mxl_verify_in_run_blocks():
    data = _load_workflow()
    run_steps = []
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "run" in step:
                run_steps.append(step["run"])
    assert any("mxl verify" in run or "myxo verify" in run for run in run_steps), (
        "At least one run step must contain 'mxl verify' or 'myxo verify'"
    )


def test_has_permissions():
    data = _load_workflow()
    permissions = data.get("permissions", {})
    assert permissions.get("contents") == "read", "Must have contents: read permission"
    assert permissions.get("issues") == "write", "Must have issues: write permission"


def test_no_expression_interpolation_in_run_blocks():
    """Ensure no ${{ }} expressions appear in run: blocks (security best practice)."""
    data = _load_workflow()
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "run" in step:
                assert "${{" not in step["run"], (
                    f"run: blocks must not contain ${{{{ }}}} expressions; use env: instead. Found in: {step['run']}"
                )
