"""Parse rule DSL into Rule objects using Lark."""

from __future__ import annotations

import ast
from typing import Any

from lark import Lark, Token, Tree

from organizer.models import ActionKind, Condition, Rule

_GRAMMAR = r"""
start: "IF"i condition "THEN"i action

?condition: extension_eq
          | extension_in
          | name_contains
          | size_cmp
          | "(" condition ")"
          | condition "AND"i condition -> cond_and

extension_eq: "extension"i "==" atom
extension_in: "extension"i "IN"i "[" atom_list "]"
name_contains: "name"i "CONTAINS"i atom
size_cmp: "size"i size_op size_value

atom_list: atom ("," atom)*

atom: string | IDENT
IDENT: /[A-Za-z0-9_.-]+/

size_op: GT | LT | GE | LE
GT: ">"
LT: "<"
GE: ">="
LE: "<="

size_value: SIGNED_INT size_suffix?
size_suffix: KB | MB | GB
KB: "kb"i
MB: "mb"i
GB: "gb"i

action: "move"i "to"i move_target
      | "rename"i "to"i string

move_target: string | bare_path
bare_path: /[^\n#]+/

string: ESCAPED_STRING

%import common.WS_INLINE
%import common.ESCAPED_STRING
%import common.SIGNED_INT

%ignore WS_INLINE
%ignore /#[^\n]*/
"""


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        try:
            return str(ast.literal_eval(s))
        except (SyntaxError, ValueError):
            return s[1:-1]
    return s


def _suffix_bytes(suf: str | None) -> int:
    if suf is None:
        return 1
    u = suf.lower()
    if u == "kb":
        return 1024
    if u == "mb":
        return 1024**2
    if u == "gb":
        return 1024**3
    return 1


def _string_value(st: Tree[Any]) -> str:
    assert str(st.data) == "string" and st.children
    return _unquote(str(st.children[0]))


def _atom_text(t: Tree[Any]) -> str:
    assert str(t.data) == "atom" and t.children
    inner = t.children[0]
    if isinstance(inner, Tree) and str(inner.data) == "string":
        return _string_value(inner)
    if isinstance(inner, Token):
        return str(inner)
    raise ValueError("Invalid atom")


def _parse_condition(t: Tree[Any]) -> Condition:
    name = str(t.data)
    ch = t.children

    if name == "extension_eq":
        for x in reversed(ch):
            if isinstance(x, Tree) and str(x.data) == "atom":
                return Condition("ext_eq", {"value": _atom_text(x).lower()})

    if name == "extension_in":
        lst = ch[-1]
        assert isinstance(lst, Tree) and str(lst.data) == "atom_list"
        vals: list[str] = []
        for x in lst.children:
            if isinstance(x, Tree) and str(x.data) == "atom":
                vals.append(_atom_text(x).lower())
        return Condition("ext_in", {"values": vals})

    if name == "name_contains":
        for x in reversed(ch):
            if isinstance(x, Tree) and str(x.data) == "atom":
                return Condition("name_contains", {"needle": _atom_text(x)})

    if name == "size_cmp":
        op_tree = next(c for c in ch if isinstance(c, Tree) and str(c.data) == "size_op")
        op_tok = op_tree.children[0]
        assert isinstance(op_tok, Token)
        op = str(op_tok)
        sv = next(c for c in ch if isinstance(c, Tree) and str(c.data) == "size_value")
        n = int(str(sv.children[0]))
        suf = None
        if len(sv.children) > 1:
            st = sv.children[1]
            assert isinstance(st, Tree) and str(st.data) == "size_suffix"
            suf_tok = st.children[0]
            assert isinstance(suf_tok, Token)
            suf = str(suf_tok)
        b = n * _suffix_bytes(suf)
        return Condition("size_cmp", {"op": op, "bytes": b})

    if name == "cond_and":
        subs = [c for c in ch if isinstance(c, Tree)]
        if len(subs) >= 2:
            return Condition(
                "and",
                {"left": _parse_condition(subs[0]), "right": _parse_condition(subs[1])},
            )

    if name == "condition" and len(ch) == 1:
        c0 = ch[0]
        assert isinstance(c0, Tree)
        return _parse_condition(c0)

    if len(ch) == 3 and isinstance(ch[0], Token) and str(ch[0]) == "(":
        c1 = ch[1]
        assert isinstance(c1, Tree)
        return _parse_condition(c1)

    raise ValueError(f"Unsupported condition node: {name}")


def _parse_action(t: Tree[Any]) -> tuple[ActionKind, str]:
    assert str(t.data) == "action"
    ch = t.children
    if len(ch) == 1 and isinstance(ch[0], Tree):
        sub = ch[0]
        if str(sub.data) == "move_target":
            inner = sub.children[0]
            if isinstance(inner, Tree) and str(inner.data) == "string":
                return ActionKind.MOVE, _string_value(inner)
            if isinstance(inner, Tree) and str(inner.data) == "bare_path":
                tok = inner.children[0]
                assert isinstance(tok, Token)
                return ActionKind.MOVE, str(tok).strip()
            if isinstance(inner, Token):
                raw = str(inner)
                path = _unquote(raw) if raw.strip().startswith(('"', "'")) else raw.strip()
                return ActionKind.MOVE, path
            return ActionKind.MOVE, str(inner).strip()
        if str(sub.data) == "string":
            return ActionKind.RENAME, _string_value(sub)
    raise ValueError("Invalid action")


class RuleParser:
    def __init__(self) -> None:
        self._lark = Lark(_GRAMMAR, parser="lalr", maybe_placeholders=False)

    def parse(self, rule_str: str) -> Rule:
        text = rule_str.strip()
        if not text:
            raise ValueError("Empty rule")
        tree = self._lark.parse(text)
        assert isinstance(tree, Tree) and str(tree.data) == "start"
        cond_t = tree.children[0]
        act_t = tree.children[1]
        assert isinstance(cond_t, Tree)
        assert isinstance(act_t, Tree)
        cond = _parse_condition(cond_t)
        action_kind, action_target = _parse_action(act_t)
        return Rule(
            condition=cond,
            action_kind=action_kind,
            action_target=action_target,
            raw_text=rule_str,
        )
