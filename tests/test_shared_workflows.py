"""Tests for shared/reusable GitHub Actions workflows."""

from pathlib import Path

import yaml

REUSABLE_CI_PATH = (
    Path(__file__).parent.parent / ".github" / "workflows" / "reusable-python-ci.yml"
)
LINT_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "lint.yml"


def _load_workflow(path: Path) -> dict:
    """Load workflow YAML, handling 'on' key parsed as boolean True."""
    return yaml.safe_load(path.read_text())


def _get_on_block(data: dict) -> dict:
    """Get the 'on' trigger block (YAML parses bare 'on' as True)."""
    return data.get(True, data.get("on", {}))


# ── reusable-python-ci.yml existence & validity ──


def test_reusable_workflow_file_exists():
    assert REUSABLE_CI_PATH.is_file(), "reusable-python-ci.yml must exist"


def test_reusable_workflow_is_valid_yaml():
    data = _load_workflow(REUSABLE_CI_PATH)
    assert isinstance(data, dict), "Workflow must be a valid YAML mapping"


# ── workflow_call trigger & inputs ──


def test_has_workflow_call_trigger():
    data = _load_workflow(REUSABLE_CI_PATH)
    on_block = _get_on_block(data)
    assert "workflow_call" in on_block, "Must have workflow_call trigger"


def test_workflow_call_has_python_version_input():
    data = _load_workflow(REUSABLE_CI_PATH)
    on_block = _get_on_block(data)
    inputs = on_block["workflow_call"].get("inputs", {})
    pv = inputs.get("python-version", {})
    assert pv, "Must define python-version input"
    assert pv.get("default") == "3.13", "python-version default must be '3.13'"


def test_workflow_call_has_run_tests_input():
    data = _load_workflow(REUSABLE_CI_PATH)
    on_block = _get_on_block(data)
    inputs = on_block["workflow_call"].get("inputs", {})
    rt = inputs.get("run-tests", {})
    assert rt, "Must define run-tests input"
    assert rt.get("default") is True, "run-tests default must be true"


def test_workflow_call_has_run_lint_input():
    data = _load_workflow(REUSABLE_CI_PATH)
    on_block = _get_on_block(data)
    inputs = on_block["workflow_call"].get("inputs", {})
    rl = inputs.get("run-lint", {})
    assert rl, "Must define run-lint input"
    assert rl.get("default") is True, "run-lint default must be true"


# ── jobs ──


def test_defines_lint_job():
    data = _load_workflow(REUSABLE_CI_PATH)
    jobs = data.get("jobs", {})
    assert "lint" in jobs, "Must define lint job"


def test_defines_test_job():
    data = _load_workflow(REUSABLE_CI_PATH)
    jobs = data.get("jobs", {})
    assert "test" in jobs, "Must define test job"


def test_lint_job_runs_ruff_check():
    data = _load_workflow(REUSABLE_CI_PATH)
    lint_steps = data["jobs"]["lint"].get("steps", [])
    run_cmds = [s["run"] for s in lint_steps if "run" in s]
    assert any("ruff check" in cmd for cmd in run_cmds), "lint job must run ruff check"


def test_lint_job_runs_ruff_format():
    data = _load_workflow(REUSABLE_CI_PATH)
    lint_steps = data["jobs"]["lint"].get("steps", [])
    run_cmds = [s["run"] for s in lint_steps if "run" in s]
    assert any("ruff format" in cmd for cmd in run_cmds), "lint job must run ruff format"


def test_test_job_runs_pytest_with_markers():
    data = _load_workflow(REUSABLE_CI_PATH)
    test_steps = data["jobs"]["test"].get("steps", [])
    run_cmds = [s["run"] for s in test_steps if "run" in s]
    assert any("pytest" in cmd and "small or medium" in cmd for cmd in run_cmds), (
        'test job must run pytest with -m "small or medium"'
    )


# ── actions versions ──


def test_uses_actions_checkout_v6():
    data = _load_workflow(REUSABLE_CI_PATH)
    checkout_found = False
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if "actions/checkout" in uses:
                assert uses == "actions/checkout@v6"
                checkout_found = True
    assert checkout_found, "Must use actions/checkout@v6"


def test_uses_setup_uv_v7():
    data = _load_workflow(REUSABLE_CI_PATH)
    uv_found = False
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if "setup-uv" in uses:
                assert uses == "astral-sh/setup-uv@v7"
                uv_found = True
    assert uv_found, "Must use astral-sh/setup-uv@v7"


def test_setup_uv_enables_cache():
    data = _load_workflow(REUSABLE_CI_PATH)
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "setup-uv" in step.get("uses", ""):
                with_block = step.get("with", {})
                assert with_block.get("enable-cache") is True, (
                    "setup-uv must have enable-cache: true"
                )


# ── permissions ──


def test_has_contents_read_permission():
    data = _load_workflow(REUSABLE_CI_PATH)
    permissions = data.get("permissions", {})
    assert permissions.get("contents") == "read", "Must declare contents: read"


# ── security: no expression interpolation in run blocks ──


def test_no_expression_interpolation_in_run_blocks():
    """Ensure no ${{ }} expressions appear in run: blocks."""
    data = _load_workflow(REUSABLE_CI_PATH)
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "run" in step:
                assert "${{" not in step["run"], (
                    f"run: blocks must not contain ${{{{ }}}} expressions; "
                    f"use env: instead. Found in: {step['run']}"
                )


# ── lint.yml calls reusable workflow ──


def test_lint_yml_calls_reusable_workflow():
    """lint.yml should delegate to the reusable workflow."""
    data = _load_workflow(LINT_PATH)
    jobs = data.get("jobs", {})
    uses_reusable = False
    for job in jobs.values():
        uses = job.get("uses", "")
        if "reusable-python-ci.yml" in uses:
            uses_reusable = True
    assert uses_reusable, "lint.yml must call reusable-python-ci.yml"
