"""Match rules to files and apply actions."""

from __future__ import annotations

from pathlib import Path

from organizer.condition_evaluator import evaluate
from organizer.file_executor import apply_action
from organizer.models import FileEvent, Rule


class RuleEngine:
    def match(self, file: FileEvent, rule: Rule) -> bool:
        return evaluate(rule.condition, file)

    def apply_first(
        self,
        file: FileEvent,
        rules: list[Rule],
        *,
        dry_run: bool = False,
    ) -> tuple[Rule, Path | None] | None:
        ordered = sorted(rules, key=lambda r: r.priority, reverse=True)
        for rule in ordered:
            if not self.match(file, rule):
                continue
            if dry_run:
                return rule, None
            new_path = apply_action(file, rule.action_kind, rule.action_target)
            return rule, new_path
        return None
