"""Tests for pytest marker configuration (small/medium/large)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFTEST = Path(__file__).parent / "conftest.py"
PYPROJECT = ROOT / "pyproject.toml"


class TestMarkerRegistration:
    """Verify that small/medium/large markers are registered in pytest."""

    def test_small_marker_registered(self):
        """pytest --markers should list the 'small' marker."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--markers"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert "@pytest.mark.small" in result.stdout

    def test_medium_marker_registered(self):
        """pytest --markers should list the 'medium' marker."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--markers"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert "@pytest.mark.medium" in result.stdout

    def test_large_marker_registered(self):
        """pytest --markers should list the 'large' marker."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--markers"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert "@pytest.mark.large" in result.stdout


class TestPyprojectMarkerConfig:
    """Verify pyproject.toml contains marker definitions."""

    def test_markers_defined_in_pyproject(self):
        """pyproject.toml should define markers under [tool.pytest.ini_options]."""
        content = PYPROJECT.read_text()
        assert "markers" in content
        assert "small" in content
        assert "medium" in content
        assert "large" in content


class TestConftestExists:
    """Verify conftest.py exists with marker-related configuration."""

    def test_conftest_exists(self):
        """tests/conftest.py should exist."""
        assert CONFTEST.is_file(), f"Expected conftest.py at {CONFTEST}"

    def test_conftest_has_auto_mark_logic(self):
        """conftest.py should contain logic to auto-apply 'small' marker to unmarked tests."""
        content = CONFTEST.read_text()
        # Should reference the marker names for auto-marking
        assert "small" in content
        assert "medium" in content
        assert "large" in content


class TestDefaultMarkerBehavior:
    """Verify unmarked tests automatically receive the 'small' marker."""

    def test_unmarked_test_gets_small_marker(self):
        """A test without any size marker should be collected when running -m small."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-m", "small", "-q"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert result.returncode == 0
        # Should collect tests (unmarked tests should be included as 'small')
        assert "no tests ran" not in result.stdout.lower()
        assert "test_cli.py" in result.stdout or "test_" in result.stdout

    def test_unmarked_test_excluded_from_large(self):
        """Unmarked tests should NOT be collected when running -m large."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-m", "large", "-q"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        # Should collect 0 tests (no tests are explicitly marked large)
        output = result.stdout.lower()
        assert "no tests collected" in output or "no tests ran" in output or "0 selected" in output


class TestCIConfiguration:
    """Verify CI workflow runs only small and medium tests by default."""

    def test_lint_yml_uses_marker_filter(self):
        """The test job in lint.yml should filter by small/medium markers."""
        lint_yml = ROOT / ".github" / "workflows" / "lint.yml"
        assert lint_yml.is_file(), "lint.yml should exist"
        content = lint_yml.read_text()
        # Should use -m flag to select small and medium tests
        assert "-m" in content
        assert "small" in content
        assert "medium" in content
