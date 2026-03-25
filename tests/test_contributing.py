"""Tests for CONTRIBUTING.md and .env.example.

Verify that developer onboarding files exist and contain
the expected sections and environment variables.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
ENV_EXAMPLE = ROOT / ".env.example"


class TestContributingExists:
    """CONTRIBUTING.md must exist at project root."""

    def test_file_exists(self) -> None:
        assert CONTRIBUTING.exists(), "CONTRIBUTING.md must exist at project root"

    def test_is_not_empty(self) -> None:
        assert CONTRIBUTING.is_file(), "CONTRIBUTING.md must be a regular file"


class TestContributingSections:
    """CONTRIBUTING.md must contain required sections."""

    REQUIRED_SECTIONS = [
        "Prerequisites",
        "Setup",
        "Testing",
        "Commits",
    ]

    @pytest.fixture()
    def content(self) -> str:
        assert CONTRIBUTING.is_file(), "CONTRIBUTING.md must exist before reading"
        return CONTRIBUTING.read_text()

    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_has_required_section(self, content: str, section: str) -> None:
        assert section.lower() in content.lower(), f"CONTRIBUTING.md must have a section about '{section}'"


class TestEnvExample:
    """.env.example must exist and list required variables."""

    def test_file_exists(self) -> None:
        assert ENV_EXAMPLE.exists(), ".env.example must exist at project root"

    def test_is_not_empty(self) -> None:
        assert ENV_EXAMPLE.is_file(), ".env.example must be a regular file"

    REQUIRED_VARS = [
        "GITHUB_TOKEN",
        "PULUMI_ACCESS_TOKEN",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ]

    @pytest.mark.parametrize("var", REQUIRED_VARS)
    def test_has_required_var(self, var: str) -> None:
        content = ENV_EXAMPLE.read_text()
        assert var in content, f".env.example must include {var}"
