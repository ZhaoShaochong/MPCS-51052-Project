"""Directory scan helpers shared by CLI and GUI."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

from organizer.file_types import file_matches_extensions
from organizer.models import FileEvent, Rule
from organizer.rule_engine import RuleEngine


def iter_directory_files(
    path: Path,
    *,
    allowed_extensions: frozenset[str] | None = None,
) -> Iterator[Path]:
    """Yield files in a directory (non-recursive), optionally filtered by extension."""
    for child in sorted(path.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_file():
            continue
        if allowed_extensions is not None:
            ext = child.suffix.lower().lstrip(".")
            if not file_matches_extensions(ext, allowed_extensions):
                continue
        yield child


def scan_directory(
    path: Path,
    rules: list[Rule],
    engine: RuleEngine,
    *,
    allowed_extensions: frozenset[str] | None = None,
    dry_run: bool = False,
    on_skip: Callable[[Path, OSError], None] | None = None,
    on_result: Callable[[FileEvent, Rule, Path | None], None] | None = None,
) -> int:
    """
    Apply rules to files in ``path``. Returns the number of files that matched a rule.

    ``on_result`` is called as ``(file_event, rule, new_path)`` for each hit.
    """
    hits = 0
    for child in iter_directory_files(path, allowed_extensions=allowed_extensions):
        try:
            fe = FileEvent.from_path(child)
        except OSError as exc:
            if on_skip is not None:
                on_skip(child, exc)
            continue
        hit = engine.apply_first(fe, rules, dry_run=dry_run)
        if hit is None:
            continue
        rule, new_path = hit
        hits += 1
        if on_result is not None:
            on_result(fe, rule, new_path)
    return hits
