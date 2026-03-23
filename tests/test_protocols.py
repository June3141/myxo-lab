"""Tests for protocol templates and protocol_loader module."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOLS_DIR = REPO_ROOT / ".myxo" / "protocols"

EXPECTED_PROTOCOLS = ["create-pr.md", "run-migration.md", "write-test.md"]

REQUIRED_FRONTMATTER_KEYS = {"name", "description", "triggers"}


# ---------------------------------------------------------------------------
# Protocol file existence tests
# ---------------------------------------------------------------------------


class TestProtocolFilesExist:
    """Each expected protocol template file must exist."""

    @pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
    def test_protocol_file_exists(self, filename: str) -> None:
        path = PROTOCOLS_DIR / filename
        assert path.exists(), f"{filename} should exist in .myxo/protocols/"

    @pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
    def test_protocol_file_is_not_empty(self, filename: str) -> None:
        path = PROTOCOLS_DIR / filename
        assert path.stat().st_size > 0, f"{filename} should not be empty"


# ---------------------------------------------------------------------------
# Protocol format validation tests
# ---------------------------------------------------------------------------


class TestProtocolFormatValidation:
    """Protocol files must follow the YAML frontmatter + markdown body format."""

    @pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
    def test_protocol_has_yaml_frontmatter(self, filename: str) -> None:
        content = (PROTOCOLS_DIR / filename).read_text()
        assert content.startswith("---\n"), f"{filename} should start with YAML frontmatter delimiter"
        # Must have closing delimiter
        rest = content[4:]
        assert "\n---\n" in rest, f"{filename} should have closing YAML frontmatter delimiter"

    @pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
    def test_protocol_has_required_frontmatter_keys(self, filename: str) -> None:
        from myxo.protocol_loader import load_protocol

        protocol = load_protocol(PROTOCOLS_DIR / filename)
        for key in REQUIRED_FRONTMATTER_KEYS:
            assert key in protocol.frontmatter, (
                f"{filename} frontmatter must contain '{key}'"
            )

    @pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
    def test_protocol_triggers_is_list(self, filename: str) -> None:
        from myxo.protocol_loader import load_protocol

        protocol = load_protocol(PROTOCOLS_DIR / filename)
        assert isinstance(protocol.frontmatter["triggers"], list), (
            f"{filename} 'triggers' must be a list"
        )

    @pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
    def test_protocol_has_markdown_body(self, filename: str) -> None:
        from myxo.protocol_loader import load_protocol

        protocol = load_protocol(PROTOCOLS_DIR / filename)
        assert len(protocol.body.strip()) > 0, f"{filename} must have a non-empty markdown body"

    @pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
    def test_protocol_body_contains_steps_section(self, filename: str) -> None:
        from myxo.protocol_loader import load_protocol

        protocol = load_protocol(PROTOCOLS_DIR / filename)
        assert "## Steps" in protocol.body, f"{filename} body must contain a '## Steps' section"

    @pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
    def test_protocol_body_contains_rules_section(self, filename: str) -> None:
        from myxo.protocol_loader import load_protocol

        protocol = load_protocol(PROTOCOLS_DIR / filename)
        assert "## Rules" in protocol.body, f"{filename} body must contain a '## Rules' section"


# ---------------------------------------------------------------------------
# protocol_loader unit tests
# ---------------------------------------------------------------------------


class TestLoadProtocol:
    """Tests for load_protocol function."""

    def test_load_protocol_returns_protocol_object(self, tmp_path: Path) -> None:
        from myxo.protocol_loader import Protocol, load_protocol

        proto_file = tmp_path / "test.md"
        proto_file.write_text(
            "---\nname: test\ndescription: A test\ntriggers:\n  - test\n---\n\n## Steps\n1. Do something\n\n## Rules\n- A rule\n"
        )
        result = load_protocol(proto_file)
        assert isinstance(result, Protocol)

    def test_load_protocol_parses_frontmatter(self, tmp_path: Path) -> None:
        from myxo.protocol_loader import load_protocol

        proto_file = tmp_path / "test.md"
        proto_file.write_text(
            "---\nname: demo\ndescription: Demo protocol\ntriggers:\n  - demo\n---\n\nBody here\n"
        )
        result = load_protocol(proto_file)
        assert result.frontmatter["name"] == "demo"
        assert result.frontmatter["description"] == "Demo protocol"
        assert result.frontmatter["triggers"] == ["demo"]

    def test_load_protocol_parses_body(self, tmp_path: Path) -> None:
        from myxo.protocol_loader import load_protocol

        proto_file = tmp_path / "test.md"
        proto_file.write_text(
            "---\nname: x\ndescription: x\ntriggers:\n  - x\n---\n\n## Steps\n1. Step one\n"
        )
        result = load_protocol(proto_file)
        assert "## Steps" in result.body
        assert "Step one" in result.body

    def test_load_protocol_file_not_found(self) -> None:
        from myxo.protocol_loader import load_protocol

        with pytest.raises(FileNotFoundError):
            load_protocol(Path("/nonexistent/protocol.md"))


class TestValidateProtocol:
    """Tests for validate_protocol function."""

    def test_validate_valid_protocol(self) -> None:
        from myxo.protocol_loader import validate_protocol

        content = "---\nname: test\ndescription: A test\ntriggers:\n  - test\n---\n\n## Steps\n1. Do\n\n## Rules\n- Rule\n"
        assert validate_protocol(content) is True

    def test_validate_missing_frontmatter(self) -> None:
        from myxo.protocol_loader import validate_protocol

        content = "# No frontmatter\n\nJust markdown\n"
        assert validate_protocol(content) is False

    def test_validate_missing_closing_delimiter(self) -> None:
        from myxo.protocol_loader import validate_protocol

        content = "---\nname: test\ndescription: broken\n\nNo closing delimiter\n"
        assert validate_protocol(content) is False

    def test_validate_missing_required_keys(self) -> None:
        from myxo.protocol_loader import validate_protocol

        content = "---\nname: test\n---\n\n## Steps\n1. Do\n\n## Rules\n- Rule\n"
        assert validate_protocol(content) is False

    def test_validate_triggers_not_list(self) -> None:
        from myxo.protocol_loader import validate_protocol

        content = "---\nname: test\ndescription: A test\ntriggers: single\n---\n\n## Steps\n1. Do\n\n## Rules\n- Rule\n"
        assert validate_protocol(content) is False

    def test_validate_missing_steps_section(self) -> None:
        from myxo.protocol_loader import validate_protocol

        content = "---\nname: test\ndescription: A test\ntriggers:\n  - test\n---\n\nNo steps here\n\n## Rules\n- Rule\n"
        assert validate_protocol(content) is False

    def test_validate_missing_rules_section(self) -> None:
        from myxo.protocol_loader import validate_protocol

        content = "---\nname: test\ndescription: A test\ntriggers:\n  - test\n---\n\n## Steps\n1. Do\n\nNo rules here\n"
        assert validate_protocol(content) is False
