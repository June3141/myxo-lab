"""Myxo CLI — uv + typer entrypoint."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from myxo.verifier import CheckResult, GitHubVerifier

app = typer.Typer(
    help="Myxo Lab CLI.",
)

_DEFAULT_CONFIG = '# Myxo repository configuration\nversion: "0.1"\n'
_DEFAULT_RULES = "# Myxo Rules\n"
_SUBDIRS = ("protocols", "procedures", "myxos")


@app.command()
def init() -> None:
    """Initialize a new .myxo-lab/ configuration in the current repository."""
    myxo_dir = Path.cwd() / ".myxo-lab"

    if myxo_dir.exists():
        if not myxo_dir.is_dir():
            typer.echo(".myxo-lab exists but is not a directory. Please remove or rename it before running `mxl init`.")
            raise typer.Exit(code=1)
        typer.echo(".myxo-lab/ already exists — skipping initialization.")
        return

    myxo_dir.mkdir()

    (myxo_dir / "config.yaml").write_text(_DEFAULT_CONFIG, encoding="utf-8")
    (myxo_dir / "rules.md").write_text(_DEFAULT_RULES, encoding="utf-8")

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

    myxo_dir = Path.cwd() / ".myxo-lab"

    if not myxo_dir.is_dir():
        typer.echo("Error: .myxo-lab/ directory not found. Run `mxl init` first.")
        raise typer.Exit(code=1)

    rules_path = myxo_dir / "rules.md"
    if not rules_path.is_file():
        typer.echo("Error: .myxo-lab/rules.md not found. Run `mxl init` or create .myxo-lab/rules.md.")
        raise typer.Exit(code=1)

    syncer = MyxoSyncer(myxo_dir)
    root = Path.cwd()

    if target is not None:
        try:
            path = syncer.sync(root, target)
        except ValueError as exc:
            typer.echo(f"Error: {exc}")
            raise typer.Exit(code=1) from None
        rel = path.relative_to(root)
        typer.echo(f"{rel} generated ({path})")
    else:
        paths = syncer.sync_all(root)
        for path in paths:
            rel = path.relative_to(root)
            typer.echo(f"{rel} generated ({path})")


def _create_verifier() -> GitHubVerifier:
    """Create a GitHubVerifier with the token from the environment."""
    token = os.environ.get("GITHUB_TOKEN", "")
    return GitHubVerifier(token=token)


def _render_results(results: list[CheckResult], console: Console) -> None:
    """Render check results as a Rich table."""
    table = Table(title="mxl verify")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Message")

    status_style = {"ok": "green", "fail": "red", "warn": "yellow"}

    for r in results:
        style = status_style.get(r.status, "")
        table.add_row(r.name, f"[{style}]{r.status}[/{style}]", r.message)

    console.print(table)


def _run_verify(fix: bool = False) -> int:
    """Run all verification checks. Returns 0 if all ok, 1 otherwise."""
    myxo_dir = Path.cwd() / ".myxo-lab"
    config_path = myxo_dir / "config.yaml"

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    gh_config = config.get("github", {})
    repo = gh_config.get("repo", "")

    if not repo:
        typer.echo("Error: 'github.repo' is not set in .myxo-lab/config.yaml.")
        return 1

    verifier = _create_verifier()
    all_results: list[CheckResult] = []

    # Run checks
    labels_cfg = gh_config.get("labels", [])
    bp_cfg = gh_config.get("branch_protection", {})
    secrets_cfg = gh_config.get("secrets", [])

    all_results.extend(asyncio.run(verifier.check_labels(repo, labels_cfg)))
    if bp_cfg:
        all_results.extend(asyncio.run(verifier.check_branch_protection(repo, bp_cfg)))
    all_results.extend(asyncio.run(verifier.check_secrets(repo, secrets_cfg)))

    console = Console()
    _render_results(all_results, console)

    has_failures = any(r.status == "fail" for r in all_results)

    if fix and has_failures:
        label_failures = [r for r in all_results if r.name.startswith("label:") and r.status == "fail"]
        if label_failures:
            asyncio.run(verifier.fix_labels(repo, labels_cfg))
        bp_failures = [r for r in all_results if r.name.startswith("branch_protection:") and r.status == "fail"]
        if bp_failures and bp_cfg:
            asyncio.run(verifier.fix_branch_protection(repo, bp_cfg))

    return 1 if has_failures else 0


@app.command()
def verify(
    fix: bool = typer.Option(False, "--fix", help="Automatically fix issues"),
) -> None:
    """Verify GitHub settings match .myxo-lab/ configuration."""
    myxo_dir = Path.cwd() / ".myxo-lab"

    if not myxo_dir.is_dir():
        typer.echo("Error: .myxo-lab/ directory not found. Run `mxl init` first.")
        raise typer.Exit(code=1)

    exit_code = _run_verify(fix=fix)
    raise typer.Exit(code=exit_code)
