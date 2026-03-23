"""Protocol loader — read and validate .myxo/protocols/ templates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REQUIRED_FRONTMATTER_KEYS = {"name", "description", "triggers"}
REQUIRED_BODY_SECTIONS = ["## Steps", "## Rules"]


@dataclass
class Protocol:
    """Parsed protocol with YAML frontmatter and markdown body."""

    frontmatter: dict
    body: str


def load_protocol(path: Path) -> Protocol:
    """Load a protocol file and return a Protocol object.

    Args:
        path: Path to the protocol markdown file.

    Returns:
        Protocol with parsed frontmatter dict and body string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file does not have valid YAML frontmatter.
    """
    if not path.exists():
        raise FileNotFoundError(f"Protocol file not found: {path}")

    content = path.read_text()

    if not content.startswith("---\n"):
        raise ValueError(f"Protocol file missing YAML frontmatter: {path}")

    rest = content[4:]
    closing_idx = rest.find("\n---\n")
    if closing_idx == -1:
        raise ValueError(f"Protocol file missing closing frontmatter delimiter: {path}")

    yaml_text = rest[:closing_idx]
    body = rest[closing_idx + 5:]  # skip "\n---\n"

    frontmatter = yaml.safe_load(yaml_text)
    if not isinstance(frontmatter, dict):
        frontmatter = {}

    return Protocol(frontmatter=frontmatter, body=body)


def validate_protocol(content: str) -> bool:
    """Validate that a protocol string follows the required format.

    Checks:
      - Starts with YAML frontmatter delimiters (``---``)
      - Contains required keys: name, description, triggers
      - ``triggers`` is a list
      - Body contains ``## Steps`` and ``## Rules`` sections

    Args:
        content: Raw protocol file content.

    Returns:
        True if valid, False otherwise.
    """
    if not content.startswith("---\n"):
        return False

    rest = content[4:]
    closing_idx = rest.find("\n---\n")
    if closing_idx == -1:
        return False

    yaml_text = rest[:closing_idx]
    body = rest[closing_idx + 5:]

    try:
        frontmatter = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return False

    if not isinstance(frontmatter, dict):
        return False

    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in frontmatter:
            return False

    if not isinstance(frontmatter.get("triggers"), list):
        return False

    for section in REQUIRED_BODY_SECTIONS:
        if section not in body:
            return False

    return True
