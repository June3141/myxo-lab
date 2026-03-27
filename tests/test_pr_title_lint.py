"""Tests for PR title lint script."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / ".github" / "scripts" / "pr-title-lint.py"


def _run(title: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), title],
        capture_output=True,
        text=True,
    )


VALID_TITLES = [
    pytest.param("feat: ✨ add hypothesis tracking endpoint", id="feat"),
    pytest.param("fix: 🐛 resolve scheduling race condition", id="fix"),
    pytest.param("chore: 🔧 add PR title validation", id="chore"),
    pytest.param("test: ✅ add myxo execution tests", id="test"),
    pytest.param("docs: 📝 update architecture diagram", id="docs"),
    pytest.param("refactor: ♻️ extract experiment validation logic", id="refactor"),
    pytest.param("feat: ✨ a", id="min-length-subject"),
]

INVALID_TITLES = [
    pytest.param("feat: add something", id="missing-emoji"),
    pytest.param("✨ add something", id="missing-type"),
    pytest.param("feat: ✨ Add something", id="uppercase-subject"),
    pytest.param("feat: ✨ add something.", id="trailing-period"),
    pytest.param("feat: ✨ " + "a" * 70, id="too-long"),
    pytest.param("", id="empty"),
]


@pytest.mark.parametrize("title", VALID_TITLES)
def test_valid_title(title: str):
    result = _run(title)
    assert result.returncode == 0


@pytest.mark.parametrize("title", INVALID_TITLES)
def test_reject_invalid_title(title: str):
    result = _run(title)
    assert result.returncode == 1
