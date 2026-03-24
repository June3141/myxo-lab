"""Tests for PR title lint script."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / ".github" / "scripts" / "pr-title-lint.py"


def _run(title: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), title],
        capture_output=True,
        text=True,
    )


def test_valid_feat_title():
    result = _run("feat: ✨ add hypothesis tracking endpoint")
    assert result.returncode == 0


def test_valid_fix_title():
    result = _run("fix: 🐛 resolve scheduling race condition")
    assert result.returncode == 0


def test_valid_chore_title():
    result = _run("chore: 🔧 add PR title validation")
    assert result.returncode == 0


def test_valid_test_title():
    result = _run("test: ✅ add myxo execution tests")
    assert result.returncode == 0


def test_valid_docs_title():
    result = _run("docs: 📝 update architecture diagram")
    assert result.returncode == 0


def test_valid_refactor_title():
    result = _run("refactor: ♻️ extract experiment validation logic")
    assert result.returncode == 0


def test_valid_min_length_subject():
    result = _run("feat: ✨ a")
    assert result.returncode == 0


def test_reject_missing_emoji():
    result = _run("feat: add something")
    assert result.returncode == 1


def test_reject_missing_type():
    result = _run("✨ add something")
    assert result.returncode == 1


def test_reject_uppercase_subject():
    result = _run("feat: ✨ Add something")
    assert result.returncode == 1


def test_reject_trailing_period():
    result = _run("feat: ✨ add something.")
    assert result.returncode == 1


def test_reject_too_long():
    result = _run("feat: ✨ " + "a" * 70)
    assert result.returncode == 1


def test_reject_empty():
    result = _run("")
    assert result.returncode == 1
