"""CLI: run, watch, rules add/list/remove."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from lark.exceptions import LarkError
from rich.console import Console

from organizer.models import FileEvent, Rule
from organizer.rule_engine import RuleEngine
from organizer.rule_manager import RuleManager
from organizer.scan import scan_directory
from organizer.scheduler import watch_loop

app = typer.Typer(help="Smart File Organizer — rule-driven cleanup with a small DSL.")
rules_app = typer.Typer(help="Manage persisted rules.")
app.add_typer(rules_app, name="rules")

_console = Console()


@app.command()
def run(
    path: Path = typer.Option(
        ...,
        "--path",
        "-p",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory to scan (non-recursive).",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print matches without changing files."),
) -> None:
    """One-off scan: apply rules to existing files in a directory."""
    manager = RuleManager()
    engine = RuleEngine()
    rules = manager.list_rules()
    _console.print("[bold]Scanning directory...[/]")
    if not rules:
        _console.print("[yellow]No rules configured.[/] Use [cyan]organizer rules add[/].")
        raise typer.Exit(code=0)
    _console.print("[bold]Applying rules...[/]")

    def on_skip(child: Path, exc: OSError) -> None:
        _console.print(f"[red]Skip {child.name}:[/] {exc}")

    def on_result(fe: FileEvent, rule: Rule, new_path: Path | None) -> None:
        if dry_run:
            _console.print(f"[yellow]Would apply[/] {rule.raw_text!r} on [cyan]{fe.name}[/]")
        elif rule.action_kind.value == "move" and new_path is not None:
            _console.print(f"Moved: [cyan]{fe.name}[/] -> [green]{new_path}[/]")
        elif rule.action_kind.value == "rename" and new_path is not None:
            _console.print(f"Renamed: [cyan]{fe.name}[/] -> [green]{new_path.name}[/]")
        else:
            _console.print(f"Applied: [cyan]{fe.name}[/]")

    scan_directory(
        path,
        rules,
        engine,
        dry_run=dry_run,
        on_skip=on_skip,
        on_result=on_result,
    )


@app.command()
def watch(
    path: Path = typer.Option(
        ...,
        "--path",
        "-p",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Watch a directory and apply rules as new files appear."""
    try:
        asyncio.run(
            watch_loop(path, RuleManager(), RuleEngine(), console=_console, dry_run=dry_run)
        )
    except KeyboardInterrupt:
        _console.print("\n[dim]Stopped.[/]")


@rules_app.command("add")
def rules_add(
    rule: str | None = typer.Option(
        None, "--rule", "-r", help="Rule text; omit to enter interactively."
    ),
) -> None:
    """Add a rule (DSL) to ~/.organizer/rules.json."""
    manager = RuleManager()
    text = rule
    if not text:
        text = _console.input("Enter rule:\n> ").strip()
    if not text:
        raise typer.BadParameter("Empty rule")
    try:
        manager.add_rule(text)
    except (LarkError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    _console.print("[green]Rule saved.[/]")


@rules_app.command("list")
def rules_list() -> None:
    """List saved rules (1-based indices match `rules remove`)."""
    manager = RuleManager()
    if not manager.rules:
        _console.print("[dim]No rules.[/]")
        return
    for i, r in enumerate(manager.rules, start=1):
        _console.print(f"{i}. {r.raw_text}")


@rules_app.command("remove")
def rules_remove(
    index: int = typer.Argument(..., min=1, help="1-based index from `organizer rules list`."),
) -> None:
    """Delete a rule by index."""
    manager = RuleManager()
    manager.remove_rule(index - 1)
    _console.print("[green]Rule deleted.[/]")


@app.command()
def gui() -> None:
    """Open a graphical UI to pick a folder and file types."""
    from organizer.gui import run_gui

    run_gui()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
