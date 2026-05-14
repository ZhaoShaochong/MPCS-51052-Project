"""Tests for the rule DSL parser."""

from __future__ import annotations

import pytest
from lark.exceptions import LarkError

from organizer.dsl_parser import RuleParser
from organizer.models import ActionKind


def test_parse_move_bare_path() -> None:
    p = RuleParser()
    r = p.parse("IF extension == pdf THEN move to ~/Documents/PDFs")
    assert r.action_kind == ActionKind.MOVE
    assert "PDFs" in r.action_target.replace("\\", "/")
    assert r.condition.kind == "ext_eq"


def test_parse_extension_in_quoted() -> None:
    p = RuleParser()
    r = p.parse('IF extension IN ["jpg", "png"] THEN move to ~/Pictures')
    assert r.condition.kind == "ext_in"
    assert set(r.condition.data["values"]) == {"jpg", "png"}


def test_parse_name_contains_and_size() -> None:
    p = RuleParser()
    r = p.parse('IF name CONTAINS "invoice" THEN move to ~/Finance')
    assert r.condition.kind == "name_contains"
    r2 = p.parse("IF size > 10MB THEN move to ~/LargeFiles")
    assert r2.condition.kind == "size_cmp"
    assert r2.condition.data["bytes"] == 10 * 1024 * 1024


def test_parse_and_condition() -> None:
    p = RuleParser()
    r = p.parse(
        "IF extension == jpg AND name CONTAINS vacation THEN move to ~/Pictures",
    )
    assert r.condition.kind == "and"


def test_parse_rename() -> None:
    p = RuleParser()
    r = p.parse('IF extension == jpg THEN rename to "{date}_{stem}.{ext}"')
    assert r.action_kind == ActionKind.RENAME
    assert "{date}" in r.action_target


def test_invalid_syntax_raises() -> None:
    p = RuleParser()
    with pytest.raises(LarkError):
        p.parse("IF extension == THEN move to x")
