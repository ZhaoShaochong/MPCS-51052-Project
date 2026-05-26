"""Tests for GUI-generated rules."""

from __future__ import annotations

from pathlib import Path

from organizer.file_types import FILE_TYPE_OPTIONS
from organizer.rule_engine import RuleEngine
from organizer.scan import scan_directory
from organizer.ui_rules import build_rules_for_types


def test_build_rules_for_types_one_per_category(tmp_path: Path) -> None:
    out = tmp_path / "out"
    rules = build_rules_for_types({"pdf", "images"}, out)
    assert len(rules) == 2
    labels = {r.raw_text for r in rules}
    assert any("PDF" in t for t in labels)
    assert any("Images" in t for t in labels)


def test_gui_rules_move_files_without_dsl(tmp_path: Path) -> None:
    source = tmp_path / "Downloads"
    source.mkdir()
    out = tmp_path / "Sorted"
    (source / "a.pdf").write_text("x", encoding="utf-8")
    (source / "b.jpg").write_text("y", encoding="utf-8")
    (source / "c.txt").write_text("z", encoding="utf-8")

    rules = build_rules_for_types({"pdf", "images"}, out)
    engine = RuleEngine()
    from organizer.file_types import extensions_for_keys

    hits = scan_directory(
        source,
        rules,
        engine,
        allowed_extensions=extensions_for_keys({"pdf", "images"}),
    )
    assert hits == 2
    assert (out / "PDF" / "a.pdf").is_file()
    assert (out / "Images" / "b.jpg").is_file()
    assert (source / "c.txt").is_file()


def test_every_option_has_unique_subdir() -> None:
    subdirs = [opt.subdir for opt in FILE_TYPE_OPTIONS]
    assert len(subdirs) == len(set(subdirs))
