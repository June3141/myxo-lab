"""Taskfile.yml structure tests.

Verify that the project Taskfile exists, is valid YAML,
and declares the expected top-level and namespaced tasks.
"""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKFILE = ROOT / "Taskfile.yml"


@pytest.fixture()
def taskfile() -> dict:
    """Load and return parsed Taskfile."""
    assert TASKFILE.exists(), "Taskfile.yml must exist at project root"
    content = TASKFILE.read_text()
    data = yaml.safe_load(content)
    assert isinstance(data, dict), "Taskfile.yml must be a valid YAML mapping"
    return data


class TestTaskfileStructure:
    """Taskfile top-level structure."""

    def test_taskfile_exists(self) -> None:
        assert TASKFILE.exists(), "Taskfile.yml must exist at project root"

    def test_valid_yaml(self) -> None:
        content = TASKFILE.read_text()
        data = yaml.safe_load(content)
        assert isinstance(data, dict)

    def test_has_version(self, taskfile: dict) -> None:
        assert "version" in taskfile
        assert taskfile["version"] == "3"

    def test_has_tasks_section(self, taskfile: dict) -> None:
        assert "tasks" in taskfile


class TestRequiredTopLevelTasks:
    """Required aggregate tasks."""

    REQUIRED = ["lint", "test", "fmt", "check", "verify"]

    @pytest.mark.parametrize("task_name", REQUIRED)
    def test_top_level_task_exists(self, taskfile: dict, task_name: str) -> None:
        tasks = taskfile["tasks"]
        assert task_name in tasks, f"Missing required top-level task: {task_name}"


class TestNamespacedTasks:
    """Python and Rust namespaced tasks."""

    PY_TASKS = ["py:lint", "py:fmt", "py:fmt:fix", "py:typecheck", "py:test"]
    RUST_TASKS = ["rust:fmt", "rust:fmt:fix", "rust:lint", "rust:test", "rust:cov"]

    @pytest.mark.parametrize("task_name", PY_TASKS)
    def test_python_task_exists(self, taskfile: dict, task_name: str) -> None:
        tasks = taskfile["tasks"]
        assert task_name in tasks, f"Missing Python task: {task_name}"

    @pytest.mark.parametrize("task_name", RUST_TASKS)
    def test_rust_task_exists(self, taskfile: dict, task_name: str) -> None:
        tasks = taskfile["tasks"]
        assert task_name in tasks, f"Missing Rust task: {task_name}"
