"""Myxo CLI — uv + typer entrypoint."""

from pathlib import Path

import typer

app = typer.Typer(
    name="myxo",
    help="Myxo — AI Agent Infrastructure Platform.",
)

_DEFAULT_CONFIG = '# Myxo repository configuration\nversion: "0.1"\n'
_DEFAULT_RULES = "# Myxo Rules\n"
_SUBDIRS = ("protocols", "procedures", "pseudopods")


@app.command()
def init() -> None:
    """Initialize a new .myxo/ configuration in the current repository."""
    myxo_dir = Path.cwd() / ".myxo"

    if myxo_dir.exists():
        if not myxo_dir.is_dir():
            typer.echo(".myxo exists but is not a directory. Please remove or rename it before running `myxo init`.")
            raise typer.Exit(code=1)
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
def sync(
    target: str | None = typer.Option(
        None,
        "--target",
        help="Sync only a specific target (claude, codex, cursor, windsurf).",
    ),
) -> None:
    """Sync agent configurations (Claude Code / Codex / Cursor / Windsurf)."""
    from myxo.syncer import MyxoSyncer

    myxo_dir = Path.cwd() / ".myxo"

    if not myxo_dir.is_dir():
        typer.echo("Error: .myxo/ directory not found. Run `myxo init` first.")
        raise typer.Exit(code=1)

    rules_path = myxo_dir / "rules.md"
    if not rules_path.is_file():
        typer.echo("Error: .myxo/rules.md not found. Run `myxo init` or create .myxo/rules.md.")
        raise typer.Exit(code=1)

    syncer = MyxoSyncer(myxo_dir)
    root = Path.cwd()

    if target is not None:
        try:
            path = syncer.sync(root, target)
        except ValueError as exc:
            typer.echo(f"Error: {exc}")
            raise typer.Exit(code=1)
        rel = path.relative_to(root)
        typer.echo(f"{rel} generated ({path})")
    else:
        paths = syncer.sync_all(root)
        for path in paths:
            rel = path.relative_to(root)
            typer.echo(f"{rel} generated ({path})")


@app.command()
def verify() -> None:
    """Verify GitHub settings match .myxo/ configuration."""
    typer.echo("myxo verify: not yet implemented")
