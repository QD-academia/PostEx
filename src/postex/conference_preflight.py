from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from postex.conference import ConferencePack, ConferenceRule

_MISSING = object()


@dataclass(frozen=True)
class ConferencePreflightFinding:
    code: str
    label: str
    origin: str
    level: str
    severity: str
    passed: bool
    actual: Any
    expected: Any
    message: str
    provenance_ref: str | None

    def as_payload(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "label": self.label,
            "origin": self.origin,
            "level": self.level,
            "severity": self.severity,
            "passed": self.passed,
            "actual": None if self.actual is _MISSING else self.actual,
            "expected": self.expected,
            "message": self.message,
            "provenance_ref": self.provenance_ref,
        }


@dataclass(frozen=True)
class ConferencePreflightReport:
    pack_id: str
    presentation_id: str
    passed: bool
    recommendations_satisfied: bool
    findings: tuple[ConferencePreflightFinding, ...]

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "0.5",
            "pack_id": self.pack_id,
            "presentation_id": self.presentation_id,
            "passed": self.passed,
            "recommendations_satisfied": self.recommendations_satisfied,
            "findings": [item.as_payload() for item in self.findings],
        }


class ConferencePreflightValidator:
    """Evaluate declarative Conference Pack rules against a normalized artifact snapshot."""

    def validate(
        self,
        pack: ConferencePack,
        artifact: dict[str, Any],
        *,
        presentation_id: str | None = None,
    ) -> ConferencePreflightReport:
        presentation = pack.presentation(presentation_id)
        target = str(presentation["presentation_id"])
        rules = tuple(
            rule for rule in pack.rules if rule.applies_to in {None, target}
        )
        findings = tuple(self._evaluate(rule, artifact) for rule in rules)
        passed = all(item.passed for item in findings if item.level == "required")
        recommendations_satisfied = all(item.passed for item in findings)
        return ConferencePreflightReport(
            pack_id=pack.pack_id,
            presentation_id=target,
            passed=passed,
            recommendations_satisfied=recommendations_satisfied,
            findings=findings,
        )

    def _evaluate(
        self, rule: ConferenceRule, artifact: dict[str, Any]
    ) -> ConferencePreflightFinding:
        actual = _lookup(artifact, rule.path)
        passed = _evaluate_rule(rule, actual, artifact)
        severity = {
            "required": "error",
            "recommended": "warning",
            "postex": "info",
        }[rule.level]
        return ConferencePreflightFinding(
            code=f"conference.{rule.rule_id}",
            label=rule.label,
            origin=rule.origin,
            level=rule.level,
            severity=severity,
            passed=passed,
            actual=actual,
            expected=rule.expected,
            message=rule.message,
            provenance_ref=rule.provenance_ref,
        )


def _lookup(data: dict[str, Any], path: str) -> Any:
    value: Any = data
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _evaluate_rule(rule: ConferenceRule, actual: Any, artifact: dict[str, Any]) -> bool:
    if rule.operator == "present_if":
        condition = rule.condition or {}
        condition_actual = _lookup(artifact, str(condition.get("path", "")))
        if not _equals(condition_actual, condition.get("equals"), 0.0):
            return True
        return actual is not _MISSING and _equals(actual, rule.expected, rule.tolerance)
    if rule.operator == "present":
        return actual is not _MISSING and actual not in (None, "", [], {})
    if rule.operator == "absent":
        return actual is _MISSING or actual in (None, "", [], {})
    if actual is _MISSING:
        return False
    if rule.operator == "equals":
        return _equals(actual, rule.expected, rule.tolerance)
    if rule.operator == "one_of":
        return isinstance(rule.expected, list) and actual in rule.expected
    if rule.operator == "minimum":
        if not _is_number(actual) or not _is_number(rule.expected):
            return False
        return _number(actual) >= _number(rule.expected) - rule.tolerance
    if rule.operator == "maximum":
        if not _is_number(actual) or not _is_number(rule.expected):
            return False
        return _number(actual) <= _number(rule.expected) + rule.tolerance
    if rule.operator == "between":
        if not isinstance(rule.expected, list) or len(rule.expected) != 2:
            raise ValueError(f"between expects a two-item list: {rule.rule_id}")
        if not _is_number(actual) or not all(_is_number(item) for item in rule.expected):
            return False
        value = _number(actual)
        return (
            _number(rule.expected[0]) - rule.tolerance
            <= value
            <= _number(rule.expected[1]) + rule.tolerance
        )
    raise ValueError(f"Unsupported conference rule operator: {rule.operator}")


def _equals(actual: Any, expected: Any, tolerance: float) -> bool:
    if actual is _MISSING:
        return False
    if isinstance(actual, (int, float)) and not isinstance(actual, bool):
        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            return abs(float(actual) - float(expected)) <= tolerance
    return bool(actual == expected)


def _number(value: Any) -> float:
    if not _is_number(value):
        raise TypeError(f"Conference numeric rule received non-numeric value: {value!r}")
    return float(value)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
