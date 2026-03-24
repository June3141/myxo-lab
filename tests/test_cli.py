"""CLI entrypoint tests."""

from typer.testing import CliRunner

from myxo.cli import app

runner = CliRunner()


def test_app_help_exits_successfully():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "mxl" in result.stdout.lower() or "Usage" in result.stdout


def test_init_command_exists():
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0


def test_sync_command_exists():
    result = runner.invoke(app, ["sync", "--help"])
    assert result.exit_code == 0


def test_verify_command_exists():
    result = runner.invoke(app, ["verify", "--help"])
    assert result.exit_code == 0
