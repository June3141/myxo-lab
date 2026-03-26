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

    *path* can be absolute or relative to the project root.
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

    Uses ``importlib.util.spec_from_file_location`` with a unique module name
    to avoid conflicts between different handler directories.
    """
    handler_dir = Path(handler_dir)
    handler_file = handler_dir / "handler.py"
    module_name = f"handler_{handler_dir.name}"

    # Remove stale entry if exists
    if module_name in sys.modules:
        del sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, handler_file)
    assert spec is not None and spec.loader is not None, f"Cannot load handler from {handler_file}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
