"""Myxo task definitions — load and validate .myxo-lab/myxos/ task files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REQUIRED_KEYS = {"name", "description"}


@dataclass
class MyxoTask:
    """Parsed myxo task with YAML frontmatter and markdown body."""

    frontmatter: dict
    body: str


def _parse_task_content(content: str) -> MyxoTask:
    """Parse task content string into a MyxoTask object.

    Args:
        content: Raw task file content with YAML frontmatter.

    Returns:
        MyxoTask with parsed frontmatter dict and body string.

    Raises:
        ValueError: If the content does not have valid YAML frontmatter
                    or is missing required keys.
    """
    if not content.startswith("---\n"):
        raise ValueError("Task file missing YAML frontmatter")

    rest = content[4:]
    closing_idx = rest.find("\n---\n")
    if closing_idx == -1:
        raise ValueError("Task file missing closing frontmatter delimiter")

    yaml_text = rest[:closing_idx]
    body = rest[closing_idx + 5 :]  # skip "\n---\n"

    try:
        frontmatter = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML frontmatter: {exc}") from exc

    if not isinstance(frontmatter, dict):
        raise ValueError("Frontmatter must be a YAML mapping")

    missing = REQUIRED_KEYS - frontmatter.keys()
    if missing:
        raise ValueError(f"Missing required frontmatter keys: {', '.join(sorted(missing))}")

    return MyxoTask(frontmatter=frontmatter, body=body)


def load_myxo_task(path: Path) -> MyxoTask:
    """Load a myxo task file and return a MyxoTask object.

    Args:
        path: Path to the task markdown file.

    Returns:
        MyxoTask with parsed frontmatter dict and body string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is invalid or path is a directory.
    """
    if not path.is_file():
        if path.is_dir():
            raise ValueError(f"Expected a file but got a directory: {path}")
        raise FileNotFoundError(f"Task file not found: {path}")

    content = path.read_text(encoding="utf-8")
    return _parse_task_content(content)


def load_all_myxo_tasks(directory: Path) -> list[MyxoTask]:
    """Load all .md task files from a directory.

    Args:
        directory: Path to the directory containing task files.

    Returns:
        List of MyxoTask objects, sorted by filename.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not directory.is_dir():
        raise FileNotFoundError(f"Task directory not found: {directory}")

    tasks = []
    for md_file in sorted(directory.glob("*.md")):
        tasks.append(load_myxo_task(md_file))
    return tasks
