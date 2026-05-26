"""Build move rules from GUI file-type selections (no DSL required)."""

from __future__ import annotations

from pathlib import Path

from organizer.file_types import FILE_TYPE_OPTIONS
from organizer.models import ActionKind, Condition, Rule


def _condition_for_extensions(extensions: frozenset[str]) -> Condition:
    if len(extensions) == 1:
        return Condition("ext_eq", {"value": next(iter(extensions))})
    return Condition("ext_in", {"values": sorted(extensions)})


def build_rules_for_types(enabled_keys: set[str], destination_root: Path) -> list[Rule]:
    """
    One move rule per enabled category.

    Files are moved to ``destination_root / <category subdir> /``.
    """
    rules: list[Rule] = []
    root = destination_root.expanduser().resolve()
    for opt in FILE_TYPE_OPTIONS:
        if opt.key not in enabled_keys:
            continue
        dest = root / opt.subdir
        dest_str = str(dest)
        rules.append(
            Rule(
                condition=_condition_for_extensions(opt.extensions),
                action_kind=ActionKind.MOVE,
                action_target=dest_str,
                raw_text=f"GUI: {opt.label} -> {dest_str}",
                priority=0,
            )
        )
    return rules
