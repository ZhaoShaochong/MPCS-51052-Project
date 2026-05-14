"""Evaluate parsed conditions against FileEvent snapshots."""

from __future__ import annotations

from typing import Any, cast

from organizer.models import Condition, FileEvent


def evaluate(condition: Condition, file: FileEvent) -> bool:
    k = condition.kind
    d: dict[str, Any] = condition.data

    if k == "ext_eq":
        return file.extension == cast(str, d["value"])

    if k == "ext_in":
        return file.extension in cast(list[str], d["values"])

    if k == "name_contains":
        return cast(str, d["needle"]).lower() in file.name.lower()

    if k == "size_cmp":
        op = cast(str, d["op"])
        limit = int(cast(int, d["bytes"]))
        sz = file.size
        if op == ">":
            return sz > limit
        if op == "<":
            return sz < limit
        if op == ">=":
            return sz >= limit
        if op == "<=":
            return sz <= limit
        raise ValueError(f"Unknown size operator: {op}")

    if k == "and":
        left = cast(Condition, d["left"])
        right = cast(Condition, d["right"])
        return evaluate(left, file) and evaluate(right, file)

    raise ValueError(f"Unknown condition kind: {k}")
