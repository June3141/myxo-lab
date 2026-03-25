"""Tests for cargo-nextest configuration.

Verify that:
- `.config/nextest.toml` exists and contains valid TOML settings
- `rust.yml` has a `test-integration` job with `--run-ignored`
- `Taskfile.yml` has a `rust:test:all` task
"""

from pathlib import Path

import pytest
import yaml

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
NEXTEST_CONFIG = ROOT / ".config" / "nextest.toml"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "rust.yml"
TASKFILE = ROOT / "Taskfile.yml"


# ── nextest.toml ──


class TestNextestConfig:
    """Validate .config/nextest.toml structure."""

    def test_nextest_config_exists(self) -> None:
        assert NEXTEST_CONFIG.is_file(), ".config/nextest.toml must exist"

    def test_nextest_config_valid_toml(self) -> None:
        content = NEXTEST_CONFIG.read_bytes()
        data = tomllib.loads(content.decode())
        assert isinstance(data, dict), "nextest.toml must be a valid TOML mapping"

    def test_has_default_profile(self) -> None:
        data = tomllib.loads(NEXTEST_CONFIG.read_bytes().decode())
        assert "profile" in data, "nextest.toml must have [profile] section"
        assert "default" in data["profile"], "Must have [profile.default]"

    def test_default_profile_has_slow_timeout(self) -> None:
        data = tomllib.loads(NEXTEST_CONFIG.read_bytes().decode())
        default = data["profile"]["default"]
        assert "slow-timeout" in default, "default profile must have slow-timeout"
        timeout = default["slow-timeout"]
        assert "period" in timeout
        assert "terminate-after" in timeout

    def test_has_ci_profile(self) -> None:
        data = tomllib.loads(NEXTEST_CONFIG.read_bytes().decode())
        assert "ci" in data["profile"], "Must have [profile.ci]"

    def test_ci_profile_fail_fast(self) -> None:
        data = tomllib.loads(NEXTEST_CONFIG.read_bytes().decode())
        ci = data["profile"]["ci"]
        assert ci.get("fail-fast") is True, "CI profile must set fail-fast = true"


# ── rust.yml – test-integration job ──


class TestRustWorkflowNextest:
    """Validate rust.yml has nextest integration."""

    @pytest.fixture()
    def workflow(self) -> dict:
        data = yaml.safe_load(WORKFLOW_PATH.read_text())
        assert isinstance(data, dict)
        return data

    def test_has_test_integration_job(self, workflow: dict) -> None:
        jobs = workflow.get("jobs", {})
        assert "test-integration" in jobs, "rust.yml must have test-integration job"

    def test_integration_job_runs_ignored(self, workflow: dict) -> None:
        job = workflow["jobs"]["test-integration"]
        steps = job.get("steps", [])
        run_steps = [s.get("run", "") for s in steps if "run" in s]
        combined = " ".join(run_steps)
        assert "--run-ignored" in combined, (
            "test-integration must use --run-ignored flag"
        )

    def test_test_job_uses_nextest(self, workflow: dict) -> None:
        """Test job should use cargo llvm-cov nextest."""
        job = workflow["jobs"]["test"]
        steps = job.get("steps", [])
        run_steps = [s.get("run", "") for s in steps if "run" in s]
        combined = " ".join(run_steps)
        assert "nextest" in combined, "test job must use nextest"

    def test_installs_cargo_nextest(self, workflow: dict) -> None:
        """CI must install cargo-nextest."""
        job = workflow["jobs"]["test"]
        steps = job.get("steps", [])
        tools = []
        for step in steps:
            uses = step.get("uses", "")
            if "install-action" in uses:
                tool = step.get("with", {}).get("tool", "")
                tools.append(tool)
        assert any("cargo-nextest" in t for t in tools), (
            "Must install cargo-nextest via install-action"
        )


# ── Taskfile – rust:test:all ──


class TestTaskfileNextest:
    """Validate Taskfile has nextest tasks."""

    @pytest.fixture()
    def taskfile(self) -> dict:
        data = yaml.safe_load(TASKFILE.read_text())
        assert isinstance(data, dict)
        return data

    def test_has_rust_test_all_task(self, taskfile: dict) -> None:
        tasks = taskfile.get("tasks", {})
        assert "rust:test:all" in tasks, "Taskfile must have rust:test:all task"

    def test_rust_test_all_runs_ignored(self, taskfile: dict) -> None:
        task = taskfile["tasks"]["rust:test:all"]
        cmd = task.get("cmd", "")
        assert "--run-ignored all" in cmd, (
            "rust:test:all must use --run-ignored all"
        )

    def test_rust_test_uses_nextest(self, taskfile: dict) -> None:
        task = taskfile["tasks"]["rust:test"]
        cmd = task.get("cmd", "")
        assert "nextest" in cmd, "rust:test must use cargo nextest"
