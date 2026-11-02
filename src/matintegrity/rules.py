"""Declarative applicability and workflow checks with three-valued results."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .contracts import Contract, check_finite


class Rule(Contract):
    id: str = Field(min_length=1)
    field: str = Field(min_length=1)
    operator: Literal["lt", "le", "gt", "ge", "eq", "in", "between"]
    expected: Any
    unit: str | None = None
    source_id: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


def evaluate_rules(rules: list[Rule], values: dict[str, Any], units: dict[str, str]) -> dict:
    check_finite(values)
    rows = []
    operations = {
        "lt": lambda a, b: a < b,
        "le": lambda a, b: a <= b,
        "gt": lambda a, b: a > b,
        "ge": lambda a, b: a >= b,
        "eq": lambda a, b: a == b,
        "in": lambda a, b: a in b,
        "between": lambda a, b: b[0] <= a <= b[1],
    }
    if not rules or len({rule.id for rule in rules}) != len(rules):
        raise ValueError("nonempty unique rule identifiers required")
    for rule in rules:
        check_finite(rule.expected)
        if rule.field not in values or values[rule.field] is None:
            outcome, reason = "unknown", "missing input"
        elif rule.unit is not None and units.get(rule.field) != rule.unit:
            outcome, reason = "unknown", "unresolved unit mapping"
        else:
            try:
                outcome = (
                    "satisfied"
                    if operations[rule.operator](values[rule.field], rule.expected)
                    else "not_satisfied"
                )
                reason = rule.rationale
            except (TypeError, IndexError):
                outcome, reason = "unknown", "incompatible rule input"
        rows.append(dict(rule_id=rule.id, outcome=outcome, reason=reason, source_id=rule.source_id))
    overall = (
        "not_satisfied"
        if any(r["outcome"] == "not_satisfied" for r in rows)
        else "unknown"
        if any(r["outcome"] == "unknown" for r in rows)
        else "satisfied"
    )
    return dict(
        schema_version="matintegrity.rule_evaluation.v1",
        outcome=overall,
        rules=rows,
        meaning="Conformance to the supplied rules only; no unprovided standard requirements are inferred.",
    )
