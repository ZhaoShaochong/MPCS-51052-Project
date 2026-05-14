"""Safe file moves and pattern-based renames."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from organizer.models import ActionKind, FileEvent

_PLACEHOLDER = re.compile(r"\{(\w+)(?::([^}]+))?\}")


def _unique_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    for i in range(1, 10_000):
        cand = parent / f"{stem}_{i}{suffix}"
        if not cand.exists():
            return cand
    raise OSError(f"Could not resolve unique path for {dest}")


def move(file: FileEvent, destination: str) -> Path:
    """Move file into a destination directory or to an explicit file path."""
    dest = Path(destination).expanduser()
    src = Path(file.path)
    if dest.exists() and dest.is_dir():
        target_dir = dest.resolve()
    elif not dest.exists() and dest.suffix == "":
        target_dir = dest.resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
    elif dest.suffix != "":
        dest.parent.mkdir(parents=True, exist_ok=True)
        return src.rename(_unique_path(dest.resolve()))
    else:
        target_dir = dest.resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

    target = _unique_path(target_dir / src.name)
    return src.rename(target)


def rename_with_pattern(file: FileEvent, pattern: str) -> Path:
    """Rename using `{stem}`, `{ext}`, `{name}`, `{date}`, `{date:fmt}` placeholders."""

    p = Path(file.path)

    def repl(m: re.Match[str]) -> str:
        key = m.group(1).lower()
        fmt = m.group(2)
        if key == "stem":
            return p.stem
        if key == "ext":
            return p.suffix.lstrip(".")
        if key == "name":
            return p.name
        if key == "date":
            ts = file.created_at or datetime.fromtimestamp(p.stat().st_mtime)
            if fmt:
                try:
                    return ts.strftime(fmt)
                except ValueError:
                    return ts.strftime("%Y-%m-%d")
            return ts.strftime("%Y-%m-%d")
        return m.group(0)

    new_name = _PLACEHOLDER.sub(repl, pattern)
    target = p.parent / new_name
    target = _unique_path(target)
    return p.rename(target)


def apply_action(file: FileEvent, kind: ActionKind, target: str) -> Path:
    if kind == ActionKind.MOVE:
        return move(file, target)
    if kind == ActionKind.RENAME:
        return rename_with_pattern(file, target)
    raise ValueError(f"Unsupported action: {kind}")
