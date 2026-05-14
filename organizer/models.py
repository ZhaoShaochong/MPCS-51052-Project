from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ActionKind(str, Enum):
    MOVE = "move"
    RENAME = "rename"


@dataclass(frozen=True)
class FileEvent:
    """Snapshot of a file for rule matching and execution."""

    path: Path
    name: str
    extension: str  # lower, without leading dot; empty if none
    size: int
    created_at: datetime | None = None

    @classmethod
    def from_path(cls, path: Path) -> FileEvent:
        path = path.resolve()
        st = path.stat()
        ext = path.suffix.lower().lstrip(".")
        created_ts = getattr(st, "st_birthtime", None)
        if created_ts is None:
            created_ts = st.st_ctime
        try:
            created = datetime.fromtimestamp(created_ts)
        except (OSError, ValueError, OverflowError):
            created = None
        return cls(
            path=path,
            name=path.name,
            extension=ext,
            size=st.st_size,
            created_at=created,
        )


@dataclass(frozen=True)
class Condition:
    """Structured condition tree (from DSL)."""

    kind: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Rule:
    condition: Condition
    action_kind: ActionKind
    action_target: str  # destination dir for move, or rename pattern
    raw_text: str
    priority: int = 0
