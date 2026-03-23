"""Myxo CLI — uv + typer entrypoint."""

import typer

app = typer.Typer(
    name="myxo",
    help="Myxo — AI Agent Infrastructure Platform.",
)


@app.command()
def init() -> None:
    """Initialize a new .myxo/ configuration in the current repository."""
    typer.echo("myxo init: not yet implemented")


@app.command()
def sync() -> None:
    """Sync agent configurations (Claude Code / Codex / Cursor)."""
    typer.echo("myxo sync: not yet implemented")


@app.command()
def verify() -> None:
    """Verify GitHub settings match .myxo/ configuration."""
    typer.echo("myxo verify: not yet implemented")
