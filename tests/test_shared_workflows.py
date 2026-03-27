"""Tests for shared/reusable GitHub Actions workflows."""

from pathlib import Path

import pytest
from helpers import get_on_block, is_sha_pinned, load_workflow

REUSABLE_CI_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "reusable-python-ci.yml"
LINT_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "lint.yml"


# ── reusable-python-ci.yml existence & validity ──


def test_reusable_workflow_file_exists():
    assert REUSABLE_CI_PATH.is_file(), "reusable-python-ci.yml must exist"


def test_reusable_workflow_is_valid_yaml():
    data = load_workflow(REUSABLE_CI_PATH)
    assert isinstance(data, dict), "Workflow must be a valid YAML mapping"


# ── workflow_call trigger & inputs ──


def test_has_workflow_call_trigger():
    data = load_workflow(REUSABLE_CI_PATH)
    on_block = get_on_block(data)
    assert "workflow_call" in on_block, "Must have workflow_call trigger"


WORKFLOW_CALL_INPUTS = [
    pytest.param("python_version", "3.13", id="python_version"),
    pytest.param("run_tests", True, id="run_tests"),
    pytest.param("run_lint", True, id="run_lint"),
]


@pytest.mark.parametrize("input_name,expected_default", WORKFLOW_CALL_INPUTS)
def test_workflow_call_has_input(input_name: str, expected_default):
    data = load_workflow(REUSABLE_CI_PATH)
    on_block = get_on_block(data)
    inputs = on_block["workflow_call"].get("inputs", {})
    entry = inputs.get(input_name, {})
    assert entry, f"Must define {input_name} input"
    assert entry.get("default") == expected_default, f"{input_name} default must be {expected_default!r}"


# ── jobs ──

REQUIRED_JOBS = ["lint", "test"]


@pytest.mark.parametrize("job_name", REQUIRED_JOBS)
def test_defines_job(job_name: str):
    data = load_workflow(REUSABLE_CI_PATH)
    jobs = data.get("jobs", {})
    assert job_name in jobs, f"Must define {job_name} job"


RUFF_COMMANDS = ["ruff check", "ruff format"]


@pytest.mark.parametrize("ruff_cmd", RUFF_COMMANDS)
def test_lint_job_runs_ruff_command(ruff_cmd: str):
    data = load_workflow(REUSABLE_CI_PATH)
    lint_steps = data["jobs"]["lint"].get("steps", [])
    run_cmds = [s["run"] for s in lint_steps if "run" in s]
    assert any(ruff_cmd in cmd for cmd in run_cmds), f"lint job must run {ruff_cmd}"


def test_test_job_runs_pytest_with_markers():
    data = load_workflow(REUSABLE_CI_PATH)
    test_steps = data["jobs"]["test"].get("steps", [])
    run_cmds = [s["run"] for s in test_steps if "run" in s]
    assert any("pytest" in cmd and "small or medium" in cmd for cmd in run_cmds), (
        'test job must run pytest with -m "small or medium"'
    )


# ── actions versions ──

SHA_PINNED_ACTIONS = [
    pytest.param("actions/checkout", id="checkout"),
    pytest.param("astral-sh/setup-uv", id="setup-uv"),
]


@pytest.mark.parametrize("action_name", SHA_PINNED_ACTIONS)
def test_action_is_sha_pinned(action_name: str):
    data = load_workflow(REUSABLE_CI_PATH)
    found = False
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if action_name in uses:
                assert is_sha_pinned(uses), f"{action_name} must be SHA-pinned, got: {uses}"
                found = True
    assert found, f"Must use {action_name}"


def test_setup_uv_enables_cache():
    data = load_workflow(REUSABLE_CI_PATH)
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "setup-uv" in step.get("uses", ""):
                with_block = step.get("with", {})
                assert with_block.get("enable-cache") is True, "setup-uv must have enable-cache: true"


# ── permissions ──


def test_has_contents_read_permission():
    data = load_workflow(REUSABLE_CI_PATH)
    permissions = data.get("permissions", {})
    assert permissions.get("contents") == "read", "Must declare contents: read"


# ── security: no expression interpolation in run blocks ──


def test_no_expression_interpolation_in_run_blocks():
    """Ensure no ${{ }} expressions appear in run: blocks."""
    data = load_workflow(REUSABLE_CI_PATH)
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "run" in step:
                assert "${{" not in step["run"], (
                    f"run: blocks must not contain ${{{{ }}}} expressions; use env: instead. Found in: {step['run']}"
                )


# ── lint.yml calls reusable workflow ──


def test_lint_yml_calls_reusable_workflow():
    """lint.yml should delegate to the reusable workflow."""
    data = load_workflow(LINT_PATH)
    jobs = data.get("jobs", {})
    uses_reusable = False
    for job in jobs.values():
        uses = job.get("uses", "")
        if "reusable-python-ci.yml" in uses:
            uses_reusable = True
    assert uses_reusable, "lint.yml must call reusable-python-ci.yml"
