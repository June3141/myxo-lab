"""Tests for rules.md validation."""

from myxo.rules_validator import validate_rules


def test_valid_rules_returns_no_errors() -> None:
    content = (
        "# Rules\n"
        "\n"
        "## Code Review\n"
        "- DB schema changes require researcher-review\n"
        "- All public API changes need security review\n"
    )
    errors = validate_rules(content)
    assert errors == []


def test_non_bullet_line_is_rejected() -> None:
    content = (
        "# Rules\n"
        "\n"
        "This line is not a bullet point\n"
    )
    errors = validate_rules(content)
    assert len(errors) == 1
    assert "line 3" in errors[0].lower() or "3" in errors[0]


def test_header_lines_are_allowed() -> None:
    content = (
        "# Rules\n"
        "## Section\n"
        "### Subsection\n"
        "- A bullet item\n"
    )
    errors = validate_rules(content)
    assert errors == []


def test_blank_lines_are_allowed() -> None:
    content = (
        "# Rules\n"
        "\n"
        "- Item one\n"
        "\n"
        "- Item two\n"
    )
    errors = validate_rules(content)
    assert errors == []


def test_max_50_lines() -> None:
    lines = ["# Rules\n"]
    for i in range(50):
        lines.append(f"- Rule {i}\n")
    content = "".join(lines)
    # 51 lines total — should fail
    errors = validate_rules(content)
    assert any("50" in e for e in errors)


def test_exactly_50_lines_is_ok() -> None:
    lines = []
    for i in range(49):
        lines.append(f"- Rule {i}\n")
    # Add a header to make it 50 lines
    lines.insert(0, "# Rules\n")
    content = "".join(lines)
    assert len(content.strip().split("\n")) == 50
    errors = validate_rules(content)
    assert not any("50" in e for e in errors)


def test_line_exceeding_120_chars() -> None:
    long_line = "- " + "x" * 119  # 121 chars total
    content = f"# Rules\n{long_line}\n"
    errors = validate_rules(content)
    assert any("120" in e for e in errors)


def test_line_exactly_120_chars_is_ok() -> None:
    line = "- " + "x" * 118  # 120 chars total
    content = f"# Rules\n{line}\n"
    errors = validate_rules(content)
    assert errors == []


def test_multiple_violations() -> None:
    long_line = "- " + "x" * 119  # too long
    content = (
        "# Rules\n"
        "Not a bullet\n"
        f"{long_line}\n"
    )
    errors = validate_rules(content)
    # Should have at least 2 errors: format + length
    assert len(errors) >= 2


def test_empty_content() -> None:
    errors = validate_rules("")
    assert errors == []


def test_only_headers_and_blanks() -> None:
    content = "# Rules\n\n## Section\n\n"
    errors = validate_rules(content)
    assert errors == []


def test_long_header_line_is_rejected() -> None:
    long_header = "# " + "A" * 119  # 121 chars total
    content = f"{long_header}\n- A bullet item\n"
    errors = validate_rules(content)
    assert any("120" in e for e in errors)


def test_indented_bullet_is_rejected() -> None:
    content = (
        "# Rules\n"
        "  - indented item\n"
    )
    errors = validate_rules(content)
    assert len(errors) == 1
    assert "must start with" in errors[0].lower() or "bullet" in errors[0].lower()
