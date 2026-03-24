"""Tests for mxl init command."""

from pathlib import Path

from typer.testing import CliRunner

from myxo.cli import app

runner = CliRunner()


def test_init_creates_myxo_lab_directory(tmp_path: Path, monkeypatch):
    """mxl init should create .myxo-lab/ directory in the current working directory."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / ".myxo-lab").is_dir()


def test_init_creates_config_yaml(tmp_path: Path, monkeypatch):
    """mxl init should create .myxo-lab/config.yaml with default content."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    config = tmp_path / ".myxo-lab" / "config.yaml"
    assert config.is_file()
    content = config.read_text()
    assert "version" in content


def test_init_creates_rules_md(tmp_path: Path, monkeypatch):
    """mxl init should create .myxo-lab/rules.md."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / ".myxo-lab" / "rules.md").is_file()


def test_init_creates_subdirectories(tmp_path: Path, monkeypatch):
    """mxl init should create protocols/, procedures/, myxos/ subdirectories."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    myxo = tmp_path / ".myxo-lab"
    assert (myxo / "protocols").is_dir()
    assert (myxo / "procedures").is_dir()
    assert (myxo / "myxos").is_dir()


def test_init_creates_gitkeep_in_subdirectories(tmp_path: Path, monkeypatch):
    """Subdirectories should contain .gitkeep files."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    myxo = tmp_path / ".myxo-lab"
    assert (myxo / "protocols" / ".gitkeep").is_file()
    assert (myxo / "procedures" / ".gitkeep").is_file()
    assert (myxo / "myxos" / ".gitkeep").is_file()


def test_init_fails_when_myxo_is_file(tmp_path: Path, monkeypatch):
    """mxl init should fail if .myxo-lab exists as a file."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".myxo-lab").write_text("not a directory")
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert "not a directory" in result.stdout.lower()


def test_init_twice_does_not_overwrite(tmp_path: Path, monkeypatch):
    """Running init twice should not overwrite existing files."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    # Modify config.yaml with custom content
    config = tmp_path / ".myxo-lab" / "config.yaml"
    config.write_text('version: "0.2"\ncustom: true\n')

    # Run init again
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    # Existing file should not be overwritten
    content = config.read_text()
    assert "custom: true" in content


def test_init_twice_shows_warning(tmp_path: Path, monkeypatch):
    """Running init when .myxo-lab/ already exists should show a message."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "already exists" in result.stdout.lower()
