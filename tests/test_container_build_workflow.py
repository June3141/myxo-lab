"""Tests for container image build verification CI workflow."""

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "container-build.yml"


def _load_workflow() -> dict:
    """Load workflow YAML, handling 'on' key parsed as boolean True."""
    return yaml.safe_load(WORKFLOW_PATH.read_text())


def _get_on_block(data: dict) -> dict:
    """Get the 'on' trigger block (YAML parses bare 'on' as True)."""
    return data.get(True, data.get("on", {}))


def test_workflow_file_exists():
    assert WORKFLOW_PATH.is_file(), "container-build.yml must exist"


def test_workflow_is_valid_yaml():
    data = _load_workflow()
    assert isinstance(data, dict), "Workflow must be a valid YAML mapping"


def test_pr_trigger_excludes_rust_paths():
    """PR trigger should include container/** but exclude Rust paths (verified by rust.yml)."""
    data = _load_workflow()
    on_block = _get_on_block(data)
    pr_trigger = on_block.get("pull_request", {})
    paths = pr_trigger.get("paths", [])
    assert "container/**" in paths, "Must filter on container/** path"
    assert "crates/**" not in paths, "crates/** should not trigger container build on PR"
    assert "Cargo.toml" not in paths, "Cargo.toml should not trigger container build on PR"
    assert "Cargo.lock" not in paths, "Cargo.lock should not trigger container build on PR"


def test_push_to_main_triggers_build():
    """Push to main should trigger container build for full verification."""
    data = _load_workflow()
    on_block = _get_on_block(data)
    push_trigger = on_block.get("push", {})
    branches = push_trigger.get("branches", [])
    assert "main" in branches, "Must trigger on push to main"


def test_pull_request_trigger_types():
    data = _load_workflow()
    on_block = _get_on_block(data)
    pr_trigger = on_block["pull_request"]
    types = pr_trigger.get("types", [])
    assert "opened" in types
    assert "synchronize" in types
    assert "reopened" in types


def test_has_permissions_block():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    permissions = data.get("permissions", {})
    assert "contents" in permissions, "Must declare contents permission"
    assert permissions["contents"] == "read"


def test_builds_docker_image():
    """Build step must exist — either as a run command or a docker/build-push-action."""
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    run_steps = []
    uses_steps = []
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "run" in step:
                run_steps.append(step["run"])
            if "uses" in step:
                uses_steps.append(step["uses"])
    has_docker_build = any("docker build" in run for run in run_steps)
    has_build_push = any("docker/build-push-action" in uses for uses in uses_steps)
    assert has_docker_build or has_build_push, "Must have a docker build step"


def test_no_expression_interpolation_in_run_blocks():
    """Ensure no ${{ }} expressions appear in run: blocks (security best practice)."""
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "run" in step:
                assert "${{" not in step["run"], (
                    f"run: blocks must not contain ${{{{ }}}} expressions; use env: instead. Found in: {step['run']}"
                )


def test_uses_actions_checkout_sha_pinned():
    import re

    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    checkout_found = False
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if "actions/checkout" in uses:
                _, _, ref = uses.partition("@")
                assert re.fullmatch(r"[0-9a-f]{40}", ref), f"actions/checkout must be SHA-pinned, got: {uses}"
                checkout_found = True
    assert checkout_found, "Must use actions/checkout"
