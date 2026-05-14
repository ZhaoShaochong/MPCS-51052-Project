"""Tests for condition evaluation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from organizer.condition_evaluator import evaluate
from organizer.models import Condition, FileEvent


def _fe(tmp_path: Path, name: str, *, size: int = 1) -> FileEvent:
    p = tmp_path / name
    p.write_bytes(b"x" * size)
    return FileEvent.from_path(p)


def test_ext_eq(tmp_path: Path) -> None:
    fe = _fe(tmp_path, "a.PDF")
    c = Condition("ext_eq", {"value": "pdf"})
    assert evaluate(c, fe) is True
    assert evaluate(Condition("ext_eq", {"value": "txt"}), fe) is False


def test_ext_in(tmp_path: Path) -> None:
    fe = _fe(tmp_path, "x.png")
    c = Condition("ext_in", {"values": ["jpg", "png"]})
    assert evaluate(c, fe) is True


def test_name_contains(tmp_path: Path) -> None:
    fe = _fe(tmp_path, "invoice_april.pdf")
    assert evaluate(Condition("name_contains", {"needle": "invoice"}), fe) is True


def test_size_cmp(tmp_path: Path) -> None:
    fe = _fe(tmp_path, "big.bin", size=2048)
    assert evaluate(Condition("size_cmp", {"op": ">", "bytes": 1000}), fe) is True
    assert evaluate(Condition("size_cmp", {"op": "<", "bytes": 1000}), fe) is False


def test_and_combines(tmp_path: Path) -> None:
    fe = _fe(tmp_path, "vacation.JPG")
    left = Condition("ext_eq", {"value": "jpg"})
    right = Condition("name_contains", {"needle": "vacation"})
    c = Condition("and", {"left": left, "right": right})
    assert evaluate(c, fe) is True


def test_unknown_condition_kind() -> None:
    dummy = FileEvent(Path("nope"), "nope", "txt", 1, datetime.now())
    with pytest.raises(ValueError, match="Unknown condition kind"):
        evaluate(Condition("bogus", {}), dummy)
