"""Tests for jscpd (code duplication detection) configuration.

Verify that jscpd is properly configured with a JSON config file,
integrated into the CI workflow, and available as a Taskfile task.
"""

import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
JSCPD_CONFIG = ROOT / ".jscpd.json"
TASKFILE = ROOT / "Taskfile.yml"
LINT_WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"


class TestJscpdConfig:
    """jscpd configuration file tests."""

    def test_config_exists(self) -> None:
        assert JSCPD_CONFIG.is_file(), ".jscpd.json must exist at project root"

    @pytest.fixture()
    def config(self) -> dict:
        return json.loads(JSCPD_CONFIG.read_text(encoding="utf-8"))

    def test_threshold_is_set(self, config: dict) -> None:
        assert "threshold" in config
        assert isinstance(config["threshold"], (int, float))

    def test_min_lines_configured(self, config: dict) -> None:
        assert "minLines" in config
        assert config["minLines"] >= 5

    def test_reporters_include_console(self, config: dict) -> None:
        reporters = config.get("reporters", [])
        assert "console" in reporters

    def test_ignore_patterns(self, config: dict) -> None:
        """Config should exclude build artifacts and dependencies."""
        ignore = config.get("ignore", [])
        assert len(ignore) > 0, "ignore patterns should be configured"

    @pytest.mark.parametrize("pattern", ["**/*.py", "**/*.yml", "**/*.yaml"])
    def test_pattern_includes_key_file_types(self, config: dict, pattern: str) -> None:
        """Config should include Python and YAML patterns."""
        patterns = config.get("pattern", [])
        assert pattern in patterns, f"pattern should include {pattern}"


class TestJscpdTaskfile:
    """Taskfile integration tests."""

    @pytest.fixture()
    def taskfile(self) -> dict:
        data = yaml.safe_load(TASKFILE.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        return data

    def test_lint_dup_task_exists(self, taskfile: dict) -> None:
        tasks = taskfile.get("tasks", {})
        assert "lint:dup" in tasks, "Taskfile must have lint:dup task"

    def test_lint_dup_uses_jscpd(self, taskfile: dict) -> None:
        task = taskfile["tasks"]["lint:dup"]
        cmd = task.get("cmd", "")
        assert "jscpd" in cmd, "lint:dup task should run jscpd"


class TestJscpdCIWorkflow:
    """CI workflow integration tests."""

    def test_lint_workflow_has_jscpd_step(self) -> None:
        content = LINT_WORKFLOW.read_text(encoding="utf-8")
        assert "jscpd" in content, "lint workflow should include jscpd step"
