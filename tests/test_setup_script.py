"""Tests for developer setup script."""

import os
import stat
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "setup-dev.sh"


def test_script_exists():
    assert SCRIPT.is_file(), "scripts/setup-dev.sh must exist"


def test_script_is_executable():
    assert SCRIPT.is_file()
    mode = os.stat(SCRIPT).st_mode
    assert mode & stat.S_IXUSR, "setup-dev.sh must be executable"


def test_script_has_shebang():
    content = SCRIPT.read_text()
    assert content.startswith("#!/"), "setup-dev.sh must start with a shebang"


def test_script_uses_strict_mode():
    content = SCRIPT.read_text()
    assert "set -euo pipefail" in content


def test_script_checks_required_tools():
    content = SCRIPT.read_text()
    for tool in ["uv", "cargo", "task"]:
        assert tool in content, f"setup-dev.sh should check for {tool}"
