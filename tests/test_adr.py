"""Tests for Architecture Decision Records structure."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = ROOT / "docs" / "adr"


def test_adr_directory_exists():
    assert ADR_DIR.is_dir(), "docs/adr/ directory must exist"


def test_at_least_one_adr_exists():
    adr_files = list(ADR_DIR.glob("*.md"))
    assert len(adr_files) > 0, "At least one ADR file must exist"


def test_adr_files_follow_naming_pattern():
    for path in ADR_DIR.glob("*.md"):
        assert re.match(r"\d{4}-.+\.md$", path.name), f"ADR must match NNNN-title.md: {path.name}"


def test_adr_files_have_required_sections():
    required = ["## Status", "## Context", "## Decision", "## Consequences"]
    for path in ADR_DIR.glob("*.md"):
        content = path.read_text()
        for section in required:
            assert section in content, f"{path.name} missing section: {section}"
