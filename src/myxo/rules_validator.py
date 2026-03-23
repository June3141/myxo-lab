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
    lines = content.split("\n")

    # Remove trailing empty line caused by final newline
    if lines and lines[-1] == "":
        lines = lines[:-1]

    if len(lines) > MAX_LINES:
        errors.append(f"rules.md exceeds {MAX_LINES} lines (found {len(lines)})")

    for i, line in enumerate(lines, start=1):
        # Check line length for ALL lines (including headers)
        if len(line) > MAX_LINE_LENGTH:
            errors.append(f"Line {i}: exceeds {MAX_LINE_LENGTH} characters (found {len(line)})")

        # Allow blank lines and header lines (no leading whitespace allowed)
        if line == "" or line.startswith("#"):
            continue

        # Must be a bullet line (no leading whitespace allowed)
        if not line.startswith("- "):
            errors.append(f"Line {i}: must start with '- ' (bullet point), got: {line[:40]}")

    return errors
