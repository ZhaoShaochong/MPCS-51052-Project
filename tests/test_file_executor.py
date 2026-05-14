"""Tests for file operations."""

from __future__ import annotations

from pathlib import Path

from organizer.file_executor import apply_action, move
from organizer.models import ActionKind, FileEvent


def test_move_into_directory(tmp_path: Path) -> None:
    src = tmp_path / "in" / "doc.pdf"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_bytes(b"%PDF-1.4")
    dest_dir = tmp_path / "out"
    fe = FileEvent.from_path(src)
    newp = move(fe, str(dest_dir))
    assert newp.parent == dest_dir.resolve()
    assert newp.name == "doc.pdf"
    assert not src.exists()


def test_rename_pattern_date(tmp_path: Path) -> None:
    f = tmp_path / "IMG_001.jpg"
    f.write_bytes(b"fake")
    fe = FileEvent.from_path(f)
    newp = apply_action(fe, ActionKind.RENAME, "{date}_{stem}.{ext}")
    assert newp.suffix == ".jpg"
    assert newp.parent == tmp_path.resolve()
    assert newp != f
