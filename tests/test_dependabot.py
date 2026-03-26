"""Tests for .github/dependabot.yml configuration."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
DEPENDABOT_PATH = REPO_ROOT / ".github" / "dependabot.yml"


def test_dependabot_file_exists():
    """dependabot.yml must exist in .github/."""
    assert DEPENDABOT_PATH.is_file(), "Missing .github/dependabot.yml"


def test_dependabot_is_valid_yaml():
    """dependabot.yml must be parseable YAML."""
    content = DEPENDABOT_PATH.read_text()
    data = yaml.safe_load(content)
    assert isinstance(data, dict), "dependabot.yml should be a YAML mapping"


def test_dependabot_has_version():
    """dependabot.yml must declare version 2."""
    data = yaml.safe_load(DEPENDABOT_PATH.read_text())
    assert data.get("version") == 2


def test_dependabot_has_updates():
    """dependabot.yml must contain an updates list."""
    data = yaml.safe_load(DEPENDABOT_PATH.read_text())
    assert isinstance(data.get("updates"), list)
    assert len(data["updates"]) >= 2


def _get_ecosystem(data: dict, ecosystem: str) -> dict | None:
    """Return the update entry for a given ecosystem, or None."""
    for entry in data.get("updates", []):
        if entry.get("package-ecosystem") == ecosystem:
            return entry
    return None


@pytest.mark.parametrize("ecosystem", ["pip", "github-actions"])
def test_ecosystem_configured(ecosystem: str):
    """Required ecosystems must be configured."""
    data = yaml.safe_load(DEPENDABOT_PATH.read_text())
    entry = _get_ecosystem(data, ecosystem)
    assert entry is not None, f"Missing {ecosystem} ecosystem configuration"


def test_target_branch_is_develop():
    """All ecosystems must target the develop branch."""
    data = yaml.safe_load(DEPENDABOT_PATH.read_text())
    for entry in data["updates"]:
        assert entry.get("target-branch") == "develop", (
            f"Ecosystem {entry.get('package-ecosystem')} should target develop, got {entry.get('target-branch')}"
        )


def test_schedule_interval_defined():
    """All ecosystems must define a schedule interval."""
    data = yaml.safe_load(DEPENDABOT_PATH.read_text())
    for entry in data["updates"]:
        schedule = entry.get("schedule", {})
        assert "interval" in schedule, f"Ecosystem {entry.get('package-ecosystem')} must define schedule.interval"


def test_open_pull_requests_limit():
    """All ecosystems should disable PR creation (alerts only)."""
    data = yaml.safe_load(DEPENDABOT_PATH.read_text())
    for entry in data["updates"]:
        assert entry.get("open-pull-requests-limit") == 0, (
            f"Ecosystem {entry.get('package-ecosystem')} should have open-pull-requests-limit: 0"
        )
