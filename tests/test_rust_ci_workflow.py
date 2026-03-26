"""Tests for Rust CI workflow configuration."""

from pathlib import Path

from helpers import get_on_block, is_sha_pinned, load_workflow

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "rust.yml"


# ── structure ──


def test_workflow_file_exists():
    assert WORKFLOW_PATH.is_file()


def test_has_permissions_block():
    data = load_workflow(WORKFLOW_PATH)
    permissions = data.get("permissions", {})
    assert permissions.get("contents") == "read", "Must declare contents: read"


def test_has_concurrency_block():
    data = load_workflow(WORKFLOW_PATH)
    assert "concurrency" in data, "Must have concurrency block"
    concurrency = data["concurrency"]
    assert "group" in concurrency
    assert concurrency.get("cancel-in-progress") is True


def test_triggers_on_pull_request_with_paths():
    data = load_workflow(WORKFLOW_PATH)
    on_block = get_on_block(data)
    pr = on_block.get("pull_request", {})
    paths = pr.get("paths", [])
    assert "crates/**" in paths
    assert "Cargo.toml" in paths


# ── jobs: lint (fmt + clippy) ──


def test_has_lint_job():
    data = load_workflow(WORKFLOW_PATH)
    assert "lint" in data["jobs"], "Must have separate lint job"


def test_lint_job_runs_fmt():
    data = load_workflow(WORKFLOW_PATH)
    steps = data["jobs"]["lint"].get("steps", [])
    run_cmds = [s["run"] for s in steps if "run" in s]
    assert any("cargo fmt" in cmd for cmd in run_cmds)


def test_lint_job_runs_clippy():
    data = load_workflow(WORKFLOW_PATH)
    steps = data["jobs"]["lint"].get("steps", [])
    run_cmds = [s["run"] for s in steps if "run" in s]
    assert any("cargo clippy" in cmd for cmd in run_cmds)


# ── jobs: test (with coverage) ──


def test_has_test_job():
    data = load_workflow(WORKFLOW_PATH)
    assert "test" in data["jobs"], "Must have separate test job"


def test_test_job_uses_llvm_cov():
    data = load_workflow(WORKFLOW_PATH)
    steps = data["jobs"]["test"].get("steps", [])
    run_cmds = [s["run"] for s in steps if "run" in s]
    uses_refs = [s["uses"] for s in steps if "uses" in s]
    has_llvm_cov = any("llvm-cov" in cmd for cmd in run_cmds) or any("cargo-llvm-cov" in u for u in uses_refs)
    assert has_llvm_cov, "test job must use cargo-llvm-cov for coverage"


def test_test_job_enforces_coverage_threshold():
    data = load_workflow(WORKFLOW_PATH)
    steps = data["jobs"]["test"].get("steps", [])
    run_cmds = [s["run"] for s in steps if "run" in s]
    assert any("fail-under-lines" in cmd for cmd in run_cmds), "Must enforce coverage threshold"


# ── SHA pinning ──


def test_all_actions_sha_pinned():
    data = load_workflow(WORKFLOW_PATH)
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses and "/" in uses:
                assert is_sha_pinned(uses), f"Action must be SHA-pinned, got: {uses}"
