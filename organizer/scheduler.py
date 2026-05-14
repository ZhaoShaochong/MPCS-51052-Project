"""Async coordination: consume watcher queue and dispatch rule engine."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import Console

from organizer.file_watcher import FileWatcher
from organizer.models import FileEvent
from organizer.rule_engine import RuleEngine
from organizer.rule_manager import RuleManager


async def watch_loop(
    root: Path,
    manager: RuleManager,
    engine: RuleEngine,
    *,
    console: Console,
    dry_run: bool = False,
) -> None:
    queue: asyncio.Queue[Path] = asyncio.Queue(maxsize=512)
    watcher = FileWatcher(root, queue)
    watcher.start()
    console.print("[bold]Watching for changes...[/] Press Ctrl+C to stop.")
    try:
        while True:
            path = await queue.get()
            try:
                if not path.exists() or not path.is_file():
                    continue
                manager.load()
                rules = manager.list_rules()
                if not rules:
                    continue
                fe = FileEvent.from_path(path)
                try:
                    hit = engine.apply_first(fe, rules, dry_run=dry_run)
                except OSError as exc:
                    console.print(f"[red]Error applying rules to {path.name}:[/] {exc}")
                    continue
                if hit is None:
                    continue
                rule, new_path = hit
                if dry_run:
                    console.print(
                        f"[yellow]Would apply[/] {rule.raw_text!r} on [cyan]{path.name}[/]"
                    )
                else:
                    dest = new_path if new_path is not None else path
                    console.print(
                        f"New file detected: [cyan]{path.name}[/]\n"
                        f"Rule applied: [green]{rule.raw_text}[/] -> [cyan]{dest}[/]"
                    )
            finally:
                queue.task_done()
    except asyncio.CancelledError:
        raise
    finally:
        watcher.stop()
