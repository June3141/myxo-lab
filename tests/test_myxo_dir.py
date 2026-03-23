"""Tests for .myxo/ directory structure."""

from pathlib import Path

MYXO_DIR = Path(__file__).parent.parent / ".myxo"


def test_myxo_dir_exists():
    assert MYXO_DIR.is_dir()


def test_config_yaml_exists():
    assert (MYXO_DIR / "config.yaml").is_file()


def test_rules_md_exists():
    assert (MYXO_DIR / "rules.md").is_file()


def test_protocols_dir_exists():
    assert (MYXO_DIR / "protocols").is_dir()


def test_procedures_dir_exists():
    assert (MYXO_DIR / "procedures").is_dir()


def test_pseudopods_dir_exists():
    assert (MYXO_DIR / "pseudopods").is_dir()
