"""Tests for myxo init command."""

from pathlib import Path

from typer.testing import CliRunner

from myxo.cli import app

runner = CliRunner()


def test_init_creates_myxo_directory(tmp_path: Path, monkeypatch):
    """myxo init should create .myxo/ directory in the current working directory."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / ".myxo").is_dir()


def test_init_creates_config_yaml(tmp_path: Path, monkeypatch):
    """myxo init should create .myxo/config.yaml with default content."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    config = tmp_path / ".myxo" / "config.yaml"
    assert config.is_file()
    content = config.read_text()
    assert "version" in content


def test_init_creates_rules_md(tmp_path: Path, monkeypatch):
    """myxo init should create .myxo/rules.md."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    assert (tmp_path / ".myxo" / "rules.md").is_file()


def test_init_creates_subdirectories(tmp_path: Path, monkeypatch):
    """myxo init should create protocols/, procedures/, pseudopods/ subdirectories."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    myxo = tmp_path / ".myxo"
    assert (myxo / "protocols").is_dir()
    assert (myxo / "procedures").is_dir()
    assert (myxo / "pseudopods").is_dir()


def test_init_creates_gitkeep_in_subdirectories(tmp_path: Path, monkeypatch):
    """Subdirectories should contain .gitkeep files."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    myxo = tmp_path / ".myxo"
    assert (myxo / "protocols" / ".gitkeep").is_file()
    assert (myxo / "procedures" / ".gitkeep").is_file()
    assert (myxo / "pseudopods" / ".gitkeep").is_file()


def test_init_twice_does_not_overwrite(tmp_path: Path, monkeypatch):
    """Running init twice should not overwrite existing files."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])

    # Modify config.yaml with custom content
    config = tmp_path / ".myxo" / "config.yaml"
    config.write_text("version: \"0.2\"\ncustom: true\n")

    # Run init again
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    # Existing file should not be overwritten
    content = config.read_text()
    assert "custom: true" in content


def test_init_twice_shows_warning(tmp_path: Path, monkeypatch):
    """Running init when .myxo/ already exists should show a message."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "already exists" in result.stdout.lower()
