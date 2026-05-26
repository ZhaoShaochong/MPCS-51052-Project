"""Tests for directory scan filtering."""

from __future__ import annotations

from pathlib import Path

from organizer.dsl_parser import RuleParser
from organizer.file_types import extensions_for_keys
from organizer.rule_engine import RuleEngine
from organizer.scan import iter_directory_files, scan_directory


def test_iter_directory_files_filters_extensions(tmp_path: Path) -> None:
    (tmp_path / "a.pdf").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("y", encoding="utf-8")
    allowed = extensions_for_keys({"pdf"})
    names = [p.name for p in iter_directory_files(tmp_path, allowed_extensions=allowed)]
    assert names == ["a.pdf"]


def test_scan_directory_respects_filter(tmp_path: Path) -> None:
    (tmp_path / "doc.pdf").write_text("x", encoding="utf-8")
    (tmp_path / "note.txt").write_text("y", encoding="utf-8")
    dest = tmp_path / "pdfs"
    rule = RuleParser().parse(f"IF extension == pdf THEN move to {dest}")
    engine = RuleEngine()
    allowed = extensions_for_keys({"pdf"})
    hits = scan_directory(tmp_path, [rule], engine, allowed_extensions=allowed)
    assert hits == 1
    assert (dest / "doc.pdf").is_file()
    assert (tmp_path / "note.txt").is_file()
