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


@pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
def test_protocol_file_exists(filename: str) -> None:
    path = PROTOCOLS_DIR / filename
    assert path.exists(), f"{filename} should exist in .myxo/protocols/"


@pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
def test_protocol_file_is_not_empty(filename: str) -> None:
    path = PROTOCOLS_DIR / filename
    assert path.stat().st_size > 0, f"{filename} should not be empty"


# ---------------------------------------------------------------------------
# Protocol format validation tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
def test_protocol_has_yaml_frontmatter(filename: str) -> None:
    content = (PROTOCOLS_DIR / filename).read_text(encoding="utf-8")
    assert content.startswith("---\n"), f"{filename} should start with YAML frontmatter delimiter"
    # Must have closing delimiter
    rest = content[4:]
    assert "\n---\n" in rest, f"{filename} should have closing YAML frontmatter delimiter"


@pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
def test_protocol_has_required_frontmatter_keys(filename: str) -> None:
    from myxo.protocol_loader import load_protocol

    protocol = load_protocol(PROTOCOLS_DIR / filename)
    for key in REQUIRED_FRONTMATTER_KEYS:
        assert key in protocol.frontmatter, (
            f"{filename} frontmatter must contain '{key}'"
        )


@pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
def test_protocol_triggers_is_list(filename: str) -> None:
    from myxo.protocol_loader import load_protocol

    protocol = load_protocol(PROTOCOLS_DIR / filename)
    assert isinstance(protocol.frontmatter["triggers"], list), (
        f"{filename} 'triggers' must be a list"
    )


@pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
def test_protocol_has_markdown_body(filename: str) -> None:
    from myxo.protocol_loader import load_protocol

    protocol = load_protocol(PROTOCOLS_DIR / filename)
    assert len(protocol.body.strip()) > 0, f"{filename} must have a non-empty markdown body"


@pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
def test_protocol_body_contains_steps_section(filename: str) -> None:
    from myxo.protocol_loader import load_protocol

    protocol = load_protocol(PROTOCOLS_DIR / filename)
    assert "## Steps" in protocol.body, f"{filename} body must contain a '## Steps' section"


@pytest.mark.parametrize("filename", EXPECTED_PROTOCOLS)
def test_protocol_body_contains_rules_section(filename: str) -> None:
    from myxo.protocol_loader import load_protocol

    protocol = load_protocol(PROTOCOLS_DIR / filename)
    assert "## Rules" in protocol.body, f"{filename} body must contain a '## Rules' section"


# ---------------------------------------------------------------------------
# protocol_loader unit tests
# ---------------------------------------------------------------------------


def test_load_protocol_returns_protocol_object(tmp_path: Path) -> None:
    from myxo.protocol_loader import Protocol, load_protocol

    proto_file = tmp_path / "test.md"
    proto_file.write_text(
        "---\nname: test\ndescription: A test\ntriggers:\n  - test\n---\n\n## Steps\n1. Do something\n\n## Rules\n- A rule\n",
        encoding="utf-8",
    )
    result = load_protocol(proto_file)
    assert isinstance(result, Protocol)


def test_load_protocol_parses_frontmatter(tmp_path: Path) -> None:
    from myxo.protocol_loader import load_protocol

    proto_file = tmp_path / "test.md"
    proto_file.write_text(
        "---\nname: demo\ndescription: Demo protocol\ntriggers:\n  - demo\n---\n\nBody here\n",
        encoding="utf-8",
    )
    result = load_protocol(proto_file)
    assert result.frontmatter["name"] == "demo"
    assert result.frontmatter["description"] == "Demo protocol"
    assert result.frontmatter["triggers"] == ["demo"]


def test_load_protocol_parses_body(tmp_path: Path) -> None:
    from myxo.protocol_loader import load_protocol

    proto_file = tmp_path / "test.md"
    proto_file.write_text(
        "---\nname: x\ndescription: x\ntriggers:\n  - x\n---\n\n## Steps\n1. Step one\n",
        encoding="utf-8",
    )
    result = load_protocol(proto_file)
    assert "## Steps" in result.body
    assert "Step one" in result.body


def test_load_protocol_file_not_found(tmp_path: Path) -> None:
    from myxo.protocol_loader import load_protocol

    with pytest.raises(FileNotFoundError):
        load_protocol(tmp_path / "nonexistent.md")


def test_load_protocol_invalid_yaml_raises_value_error(tmp_path: Path) -> None:
    from myxo.protocol_loader import load_protocol

    proto_file = tmp_path / "bad.md"
    proto_file.write_text(
        "---\n: invalid: yaml: {{{\n---\n\nBody\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Invalid YAML frontmatter"):
        load_protocol(proto_file)


# ---------------------------------------------------------------------------
# validate_protocol unit tests
# ---------------------------------------------------------------------------


def test_validate_valid_protocol() -> None:
    from myxo.protocol_loader import validate_protocol

    content = "---\nname: test\ndescription: A test\ntriggers:\n  - test\n---\n\n## Steps\n1. Do\n\n## Rules\n- Rule\n"
    assert validate_protocol(content) is True


def test_validate_missing_frontmatter() -> None:
    from myxo.protocol_loader import validate_protocol

    content = "# No frontmatter\n\nJust markdown\n"
    assert validate_protocol(content) is False


def test_validate_missing_closing_delimiter() -> None:
    from myxo.protocol_loader import validate_protocol

    content = "---\nname: test\ndescription: broken\n\nNo closing delimiter\n"
    assert validate_protocol(content) is False


def test_validate_missing_required_keys() -> None:
    from myxo.protocol_loader import validate_protocol

    content = "---\nname: test\n---\n\n## Steps\n1. Do\n\n## Rules\n- Rule\n"
    assert validate_protocol(content) is False


def test_validate_triggers_not_list() -> None:
    from myxo.protocol_loader import validate_protocol

    content = "---\nname: test\ndescription: A test\ntriggers: single\n---\n\n## Steps\n1. Do\n\n## Rules\n- Rule\n"
    assert validate_protocol(content) is False


def test_validate_missing_steps_section() -> None:
    from myxo.protocol_loader import validate_protocol

    content = "---\nname: test\ndescription: A test\ntriggers:\n  - test\n---\n\nNo steps here\n\n## Rules\n- Rule\n"
    assert validate_protocol(content) is False


def test_validate_missing_rules_section() -> None:
    from myxo.protocol_loader import validate_protocol

    content = "---\nname: test\ndescription: A test\ntriggers:\n  - test\n---\n\n## Steps\n1. Do\n\nNo rules here\n"
    assert validate_protocol(content) is False
