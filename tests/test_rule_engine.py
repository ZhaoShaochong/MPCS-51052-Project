"""Tests for rule matching and application (dry-run)."""

from __future__ import annotations

from pathlib import Path

from organizer.dsl_parser import RuleParser
from organizer.models import FileEvent
from organizer.rule_engine import RuleEngine


def test_apply_first_dry_run_respects_order(tmp_path: Path) -> None:
    p = RuleParser()
    low = p.parse("IF extension == txt THEN move to ./low")
    high = p.parse("IF extension == txt THEN move to ./high")
    high.priority = 10
    low.priority = 0
    f = tmp_path / "a.txt"
    f.write_text("hi", encoding="utf-8")
    fe = FileEvent.from_path(f)
    engine = RuleEngine()
    hit = engine.apply_first(fe, [low, high], dry_run=True)
    assert hit is not None
    rule, newp = hit
    assert rule is high
    assert newp is None
