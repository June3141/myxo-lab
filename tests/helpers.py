"""Shared test helper functions for workflow and handler tests."""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = ROOT / ".github" / "workflows"


def load_workflow(path: Path) -> dict:
    """Load workflow YAML and return parsed dict.

    *path* should be an absolute ``Path`` to a workflow YAML file.
    """
    data = yaml.safe_load(path.read_text())
    assert isinstance(data, dict), "Workflow YAML must be a valid mapping"
    return data


def get_on_block(data: dict) -> dict:
    """Return the ``on`` trigger block from a parsed workflow.

    PyYAML parses the bare YAML key ``on`` as boolean ``True``, so this
    helper checks both ``True`` and ``"on"`` keys.
    """
    return data.get(True, data.get("on", {}))


def is_sha_pinned(ref: str) -> bool:
    """Return *True* if *ref* is pinned to a full 40-char commit SHA."""
    _, _, version = ref.partition("@")
    return bool(re.fullmatch(r"[0-9a-f]{40}", version))


def load_handler(handler_dir: str | Path) -> object:
    """Dynamically import ``handler`` module from *handler_dir*.

    The directory is temporarily prepended to ``sys.path`` and cleaned up
    after import.
    """
    handler_dir = str(handler_dir)
    original_path = sys.path.copy()
    try:
        if handler_dir not in sys.path:
            sys.path.insert(0, handler_dir)
        if "handler" in sys.modules:
            return importlib.reload(sys.modules["handler"])
        return importlib.import_module("handler")
    finally:
        sys.path[:] = original_path
