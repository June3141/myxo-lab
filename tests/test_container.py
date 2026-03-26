"""Tests for container image definition files."""

import json
from pathlib import Path

import pytest

CONTAINER_DIR = Path(__file__).parent.parent / "container"


class TestDevboxJson:
    """Tests for container/devbox.json."""

    def test_devbox_json_exists(self):
        assert CONTAINER_DIR.joinpath("devbox.json").is_file()

    def test_devbox_json_is_valid_json(self):
        content = CONTAINER_DIR.joinpath("devbox.json").read_text()
        data = json.loads(content)
        assert isinstance(data, dict)

    def test_devbox_json_has_packages(self):
        data = json.loads(CONTAINER_DIR.joinpath("devbox.json").read_text())
        assert "packages" in data
        assert isinstance(data["packages"], list)
        assert len(data["packages"]) > 0

    REQUIRED_PACKAGES = ["git", "gh", "python", "nodejs"]

    @pytest.mark.parametrize("package", REQUIRED_PACKAGES)
    def test_devbox_json_contains_package(self, package: str):
        data = json.loads(CONTAINER_DIR.joinpath("devbox.json").read_text())
        pkg_str = " ".join(data["packages"])
        assert package in pkg_str


class TestDockerfile:
    """Tests for container/Dockerfile."""

    def test_dockerfile_exists(self):
        assert CONTAINER_DIR.joinpath("Dockerfile").is_file()

    def test_dockerfile_has_from_instruction(self):
        content = CONTAINER_DIR.joinpath("Dockerfile").read_text()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        from_lines = [line for line in lines if line.upper().startswith("FROM")]
        assert len(from_lines) >= 1

    def test_dockerfile_uses_multi_stage_build(self):
        content = CONTAINER_DIR.joinpath("Dockerfile").read_text()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        from_lines = [line for line in lines if line.upper().startswith("FROM")]
        assert len(from_lines) >= 2, "Dockerfile should use multi-stage build"

    def test_dockerfile_references_devbox(self):
        content = CONTAINER_DIR.joinpath("Dockerfile").read_text().lower()
        assert "devbox" in content

    def test_dockerfile_base_is_debian_bookworm_slim(self):
        content = CONTAINER_DIR.joinpath("Dockerfile").read_text()
        assert "debian:bookworm-slim" in content
