"""Myxo CLI — uv + typer entrypoint."""

from pathlib import Path

import typer

app = typer.Typer(
    name="myxo",
    help="Myxo — AI Agent Infrastructure Platform.",
)

_DEFAULT_CONFIG = "# Myxo repository configuration\nversion: \"0.1\"\n"
_DEFAULT_RULES = "# Myxo Rules\n"
_SUBDIRS = ("protocols", "procedures", "pseudopods")


@app.command()
def init() -> None:
    """Initialize a new .myxo/ configuration in the current repository."""
    myxo_dir = Path.cwd() / ".myxo"

    if myxo_dir.exists():
        typer.echo(".myxo/ already exists — skipping initialization.")
        return

    myxo_dir.mkdir()

    (myxo_dir / "config.yaml").write_text(_DEFAULT_CONFIG)
    (myxo_dir / "rules.md").write_text(_DEFAULT_RULES)

    for subdir in _SUBDIRS:
        sub = myxo_dir / subdir
        sub.mkdir()
        (sub / ".gitkeep").touch()


@app.command()
def sync() -> None:
    """Sync agent configurations (Claude Code / Codex / Cursor)."""
    typer.echo("myxo sync: not yet implemented")


@app.command()
def verify() -> None:
    """Verify GitHub settings match .myxo/ configuration."""
    typer.echo("myxo verify: not yet implemented")
