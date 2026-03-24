"""Tests for MyxoTask definition loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from myxo.myxo_task import MyxoTask, load_all_myxo_tasks, load_myxo_task

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "myxo_tasks"

# --- Sample content helpers ---

VALID_CONTENT = """\
---
name: sample-task
description: A sample myxo task
triggers:
  - manual
timeout: 120
env:
  - MY_TOKEN
---

## Steps
1. Do something

## Rules
- Be nice
"""

MINIMAL_CONTENT = """\
---
name: minimal
description: Only required keys
---

Body text here.
"""


# --- MyxoTask dataclass ---


class TestMyxoTaskDataclass:
    def test_has_frontmatter_and_body(self):
        task = MyxoTask(frontmatter={"name": "x", "description": "y"}, body="hello")
        assert task.frontmatter["name"] == "x"
        assert task.body == "hello"


# --- load_myxo_task ---


class TestLoadMyxoTask:
    def test_load_valid_file(self, tmp_path: Path):
        p = tmp_path / "task.md"
        p.write_text(VALID_CONTENT, encoding="utf-8")
        task = load_myxo_task(p)
        assert task.frontmatter["name"] == "sample-task"
        assert task.frontmatter["description"] == "A sample myxo task"
        assert task.frontmatter["triggers"] == ["manual"]
        assert task.frontmatter["timeout"] == 120
        assert task.frontmatter["env"] == ["MY_TOKEN"]
        assert "## Steps" in task.body

    def test_load_minimal_file(self, tmp_path: Path):
        p = tmp_path / "minimal.md"
        p.write_text(MINIMAL_CONTENT, encoding="utf-8")
        task = load_myxo_task(p)
        assert task.frontmatter["name"] == "minimal"
        assert task.frontmatter["description"] == "Only required keys"

    def test_optional_defaults(self, tmp_path: Path):
        p = tmp_path / "minimal.md"
        p.write_text(MINIMAL_CONTENT, encoding="utf-8")
        task = load_myxo_task(p)
        assert task.frontmatter.get("triggers") is None
        assert task.frontmatter.get("timeout") is None
        assert task.frontmatter.get("env") is None

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_myxo_task(Path("/nonexistent/task.md"))

    def test_directory_raises_value_error(self, tmp_path: Path):
        with pytest.raises(ValueError, match="directory"):
            load_myxo_task(tmp_path)

    def test_missing_frontmatter_delimiter(self, tmp_path: Path):
        p = tmp_path / "bad.md"
        p.write_text("no frontmatter here", encoding="utf-8")
        with pytest.raises(ValueError, match="frontmatter"):
            load_myxo_task(p)

    def test_missing_closing_delimiter(self, tmp_path: Path):
        p = tmp_path / "bad.md"
        p.write_text("---\nname: x\nNo closing\n", encoding="utf-8")
        with pytest.raises(ValueError, match="closing"):
            load_myxo_task(p)

    def test_invalid_yaml(self, tmp_path: Path):
        p = tmp_path / "bad.md"
        p.write_text("---\n: :\n---\nBody\n", encoding="utf-8")
        with pytest.raises(ValueError, match="YAML"):
            load_myxo_task(p)

    def test_missing_required_key_name(self, tmp_path: Path):
        content = "---\ndescription: missing name\n---\nBody\n"
        p = tmp_path / "bad.md"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError, match="name"):
            load_myxo_task(p)

    def test_missing_required_key_description(self, tmp_path: Path):
        content = "---\nname: no-desc\n---\nBody\n"
        p = tmp_path / "bad.md"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError, match="description"):
            load_myxo_task(p)


# --- load_all_myxo_tasks ---


class TestLoadAllMyxoTasks:
    def test_load_multiple_files(self, tmp_path: Path):
        (tmp_path / "a.md").write_text(VALID_CONTENT, encoding="utf-8")
        (tmp_path / "b.md").write_text(MINIMAL_CONTENT, encoding="utf-8")
        tasks = load_all_myxo_tasks(tmp_path)
        assert len(tasks) == 2
        names = {t.frontmatter["name"] for t in tasks}
        assert names == {"sample-task", "minimal"}

    def test_ignores_non_md_files(self, tmp_path: Path):
        (tmp_path / "a.md").write_text(VALID_CONTENT, encoding="utf-8")
        (tmp_path / "readme.txt").write_text("not a task", encoding="utf-8")
        (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
        tasks = load_all_myxo_tasks(tmp_path)
        assert len(tasks) == 1

    def test_empty_directory(self, tmp_path: Path):
        tasks = load_all_myxo_tasks(tmp_path)
        assert tasks == []

    def test_directory_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_all_myxo_tasks(Path("/nonexistent/dir"))


# --- Sample task file integration test ---

SAMPLE_TASK_PATH = (
    Path(__file__).parent.parent / ".myxo-lab" / "myxos" / "gitignore-setup.md"
)


class TestSampleTaskFile:
    def test_sample_file_exists(self):
        assert SAMPLE_TASK_PATH.is_file(), f"Expected sample at {SAMPLE_TASK_PATH}"

    def test_sample_file_loads_correctly(self):
        task = load_myxo_task(SAMPLE_TASK_PATH)
        assert task.frontmatter["name"] == "gitignore-setup"
        assert "gitignore" in task.frontmatter["description"].lower()
        assert isinstance(task.frontmatter["triggers"], list)
        assert task.frontmatter["timeout"] == 300
        assert "GITHUB_TOKEN" in task.frontmatter["env"]
        assert "## Steps" in task.body
        assert "## Rules" in task.body
