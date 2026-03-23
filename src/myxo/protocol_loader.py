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


def _parse_protocol_content(content: str) -> Protocol:
    """Parse protocol content string into a Protocol object.

    Args:
        content: Raw protocol file content with YAML frontmatter.

    Returns:
        Protocol with parsed frontmatter dict and body string.

    Raises:
        ValueError: If the content does not have valid YAML frontmatter.
    """
    if not content.startswith("---\n"):
        raise ValueError("Protocol file missing YAML frontmatter")

    rest = content[4:]
    closing_idx = rest.find("\n---\n")
    if closing_idx == -1:
        raise ValueError("Protocol file missing closing frontmatter delimiter")

    yaml_text = rest[:closing_idx]
    body = rest[closing_idx + 5:]  # skip "\n---\n"

    try:
        frontmatter = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML frontmatter: {exc}") from exc
    if not isinstance(frontmatter, dict):
        raise ValueError("Frontmatter must be a YAML mapping")

    return Protocol(frontmatter=frontmatter, body=body)


def load_protocol(path: Path) -> Protocol:
    """Load a protocol file and return a Protocol object.

    Args:
        path: Path to the protocol markdown file.

    Returns:
        Protocol with parsed frontmatter dict and body string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file does not have valid YAML frontmatter
                    or path is a directory.
    """
    if not path.is_file():
        if path.is_dir():
            raise ValueError(f"Expected a file but got a directory: {path}")
        raise FileNotFoundError(f"Protocol file not found: {path}")

    content = path.read_text(encoding="utf-8")
    return _parse_protocol_content(content)


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
    try:
        protocol = _parse_protocol_content(content)
    except ValueError:
        return False

    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in protocol.frontmatter:
            return False

    if not isinstance(protocol.frontmatter.get("triggers"), list):
        return False

    for section in REQUIRED_BODY_SECTIONS:
        if section not in protocol.body:
            return False

    return True
