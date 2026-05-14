"""Tests for JSON rule persistence."""

from __future__ import annotations

from pathlib import Path

from organizer.rule_manager import RuleManager


def test_rule_manager_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    m = RuleManager(path)
    m.add_rule("IF extension == pdf THEN move to ./archive")
    m2 = RuleManager(path)
    assert len(m2.rules) == 1
    assert "pdf" in m2.rules[0].raw_text
    m2.remove_rule(0)
    m3 = RuleManager(path)
    assert m3.rules == []
