"""Persist rules as JSON (raw DSL strings)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from organizer.dsl_parser import RuleParser
from organizer.models import Rule


class RuleManager:
    """Load/save rules under the user's home directory."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self.path = storage_path or (Path.home() / ".organizer" / "rules.json")
        self._parser = RuleParser()
        self.rules: list[Rule] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.rules = []
            return
        raw = self.path.read_text(encoding="utf-8")
        data = cast(dict[str, Any], json.loads(raw))
        items = data.get("rules", [])
        if not isinstance(items, list):
            items = []
        self.rules = []
        for it in items:
            if not isinstance(it, dict):
                continue
            row = cast(dict[str, Any], it)
            text = str(row.get("raw") or row.get("raw_text") or "")
            rule = self._parser.parse(text)
            rule.priority = int(row.get("priority", 0))
            self.rules.append(rule)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "rules": [{"raw": r.raw_text, "priority": r.priority} for r in self.rules],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add_rule(self, raw: str) -> Rule:
        rule = self._parser.parse(raw.strip())
        self.rules.append(rule)
        self.save()
        return rule

    def remove_rule(self, index: int) -> None:
        if index < 0 or index >= len(self.rules):
            raise IndexError("Rule index out of range")
        del self.rules[index]
        self.save()

    def list_rules(self) -> list[Rule]:
        return list(self.rules)
