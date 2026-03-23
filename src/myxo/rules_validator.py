"""Validator for .myxo/rules.md brevity guidelines."""

MAX_LINES = 50
MAX_LINE_LENGTH = 120


def validate_rules(content: str) -> list[str]:
    """Validate rules.md content and return a list of violation messages.

    Rules:
    - Each line must start with ``- `` (bullet), ``#`` (header), or be blank.
    - Maximum 50 lines total.
    - Each line must be at most 120 characters.
    """
    if not content.strip():
        return []

    errors: list[str] = []
    lines = content.strip().split("\n")

    if len(lines) > MAX_LINES:
        errors.append(
            f"rules.md exceeds {MAX_LINES} lines (found {len(lines)})"
        )

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Allow blank lines and header lines
        if stripped == "" or stripped.startswith("#"):
            continue

        # Must be a bullet line
        if not stripped.startswith("- "):
            errors.append(
                f"Line {i}: must start with '- ' (bullet point), got: {stripped[:40]}"
            )

        if len(line) > MAX_LINE_LENGTH:
            errors.append(
                f"Line {i}: exceeds {MAX_LINE_LENGTH} characters (found {len(line)})"
            )

    return errors
