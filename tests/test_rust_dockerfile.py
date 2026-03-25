"""Tests for Rust binary Dockerfile."""

from pathlib import Path

DOCKERFILE = Path(__file__).resolve().parent.parent / "container" / "Dockerfile"


def test_dockerfile_exists():
    assert DOCKERFILE.is_file()


def test_has_rust_build_stage():
    content = DOCKERFILE.read_text()
    assert "rust:" in content.lower() or "cargo build" in content.lower(), "Dockerfile must have a Rust build stage"


def test_has_multi_stage_build():
    content = DOCKERFILE.read_text()
    from_count = content.lower().count("from ")
    assert from_count >= 3, "Dockerfile must have at least 3 stages (nix builder, rust builder, final)"


def test_copies_rust_binary():
    content = DOCKERFILE.read_text()
    assert "mxl" in content, "Dockerfile must reference the mxl binary"


def test_final_stage_is_minimal():
    """Final stage should use a slim/distroless base, not a full Rust image."""
    lines = DOCKERFILE.read_text().splitlines()
    last_from = [l for l in lines if l.strip().upper().startswith("FROM")][-1]
    assert "slim" in last_from or "distroless" in last_from or "alpine" in last_from, (
        f"Final stage should use a minimal base image, got: {last_from}"
    )
