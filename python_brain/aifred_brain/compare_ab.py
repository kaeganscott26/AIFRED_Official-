"""Compare Mode helpers for Mix A vs Mix B facts only.

Responsibility:
    Calculate direct A/B factual deltas from already-calculated metric facts
    without invoking hidden reference targets or global pools.

This module must not judge which mix is better, generate advice, compare to a
reference target, or invent metric values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence


class ComparisonAvailability(str, Enum):
    """Availability state for one A/B metric comparison."""

    AVAILABLE = "available"
    A_UNAVAILABLE = "a_unavailable"
    B_UNAVAILABLE = "b_unavailable"
    BOTH_UNAVAILABLE = "both_unavailable"
    NON_NUMERIC = "non_numeric"
    MISSING = "missing"


@dataclass(frozen=True)
class MetricComparison:
    """Factual A/B comparison for one named metric."""

    name: str
    family: str | None
    unit: str | None
    a_value: object
    b_value: object
    delta: float | None
    absolute_delta: float | None
    percent_delta: float | None
    availability: ComparisonAvailability


@dataclass(frozen=True)
class CompareABResult:
    """Factual Compare Mode result with no interpretation or advice."""

    mode: str
    a_label: str
    b_label: str
    comparisons: tuple[MetricComparison, ...]
    limitations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def is_numeric_value(value: object) -> bool:
    """Return whether `value` is a finite non-boolean number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    numeric = float(value)
    return numeric == numeric and numeric not in (float("inf"), float("-inf"))


def _reject_fake_value(value: object) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) == -999.0:
        raise ValueError("A/B comparison must not preserve fake placeholder metric values.")


def calculate_delta(a_value: object, b_value: object) -> float | None:
    """Calculate signed B-minus-A delta for finite numeric values."""
    _reject_fake_value(a_value)
    _reject_fake_value(b_value)
    if not is_numeric_value(a_value) or not is_numeric_value(b_value):
        return None
    return float(b_value) - float(a_value)


def calculate_percent_delta(a_value: object, b_value: object) -> float | None:
    """Calculate B-minus-A percent delta relative to A when meaningful."""
    delta = calculate_delta(a_value, b_value)
    if delta is None or not is_numeric_value(a_value):
        return None
    denominator = float(a_value)
    if denominator == 0.0:
        return None
    return (delta / abs(denominator)) * 100.0


def _fact_value(fact: object | None, key: str, default: object = None) -> object:
    if fact is None:
        return default
    if isinstance(fact, dict):
        return fact.get(key, default)
    return getattr(fact, key, default)


def _enum_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    return value


def _fact_available(fact: object | None) -> bool:
    if fact is None:
        return False
    if bool(_fact_value(fact, "available", True)) is False:
        return False
    return _fact_value(fact, "value") is not None


def _text_or_none(value: object) -> str | None:
    value = _enum_value(value)
    if value is None:
        return None
    return str(value)


def _metric_key(fact: object) -> tuple[str | None, str]:
    return _text_or_none(_fact_value(fact, "family")), str(_fact_value(fact, "name", ""))


def _availability_for(a_fact: object | None, b_fact: object | None) -> ComparisonAvailability:
    if a_fact is None or b_fact is None:
        return ComparisonAvailability.MISSING
    a_available = _fact_available(a_fact)
    b_available = _fact_available(b_fact)
    if not a_available and not b_available:
        return ComparisonAvailability.BOTH_UNAVAILABLE
    if not a_available:
        return ComparisonAvailability.A_UNAVAILABLE
    if not b_available:
        return ComparisonAvailability.B_UNAVAILABLE
    if not is_numeric_value(_fact_value(a_fact, "value")) or not is_numeric_value(_fact_value(b_fact, "value")):
        return ComparisonAvailability.NON_NUMERIC
    return ComparisonAvailability.AVAILABLE


def compare_metric_fact(a_fact: object | None, b_fact: object | None) -> MetricComparison:
    """Compare two packet-like metric facts without inventing values."""
    availability = _availability_for(a_fact, b_fact)
    source_fact = a_fact if a_fact is not None else b_fact
    name = str(_fact_value(source_fact, "name", ""))
    family = _text_or_none(_fact_value(source_fact, "family"))
    unit = _text_or_none(_fact_value(a_fact, "unit", _fact_value(b_fact, "unit")))
    a_value = _fact_value(a_fact, "value")
    b_value = _fact_value(b_fact, "value")
    _reject_fake_value(a_value)
    _reject_fake_value(b_value)

    delta = calculate_delta(a_value, b_value) if availability is ComparisonAvailability.AVAILABLE else None
    return MetricComparison(
        name=name,
        family=family,
        unit=unit,
        a_value=a_value,
        b_value=b_value,
        delta=delta,
        absolute_delta=None if delta is None else abs(delta),
        percent_delta=calculate_percent_delta(a_value, b_value) if availability is ComparisonAvailability.AVAILABLE else None,
        availability=availability,
    )


def _index_facts(facts: Sequence[object]) -> dict[tuple[str | None, str], object]:
    indexed: dict[tuple[str | None, str], object] = {}
    for fact in facts:
        indexed[_metric_key(fact)] = fact
    return indexed


def compare_metric_collections(
    a_facts: Sequence[object],
    b_facts: Sequence[object],
    a_label: str = "Mix A",
    b_label: str = "Mix B",
) -> CompareABResult:
    """Compare two collections of named metric facts by family and name."""
    a_index = _index_facts(tuple(a_facts))
    b_index = _index_facts(tuple(b_facts))
    keys = sorted(set(a_index) | set(b_index), key=lambda item: ("", "") if item is None else (str(item[0]), item[1]))
    comparisons = tuple(compare_metric_fact(a_index.get(key), b_index.get(key)) for key in keys)
    limitations: list[str] = []
    if any(comparison.availability is not ComparisonAvailability.AVAILABLE for comparison in comparisons):
        limitations.append("Some A/B metric deltas are unavailable because one or both facts are missing, unavailable, or non-numeric.")

    return CompareABResult(
        mode="Compare A/B",
        a_label=str(a_label),
        b_label=str(b_label),
        comparisons=comparisons,
        limitations=tuple(limitations),
        warnings=(),
    )


def _packet_facts(packet: object) -> tuple[object, ...]:
    if isinstance(packet, dict):
        facts = packet.get("facts", ())
    else:
        facts = getattr(packet, "facts", ())
    if facts is None:
        return ()
    return tuple(facts)


def compare_packet_facts(
    a_packet: object,
    b_packet: object,
    a_label: str = "Mix A",
    b_label: str = "Mix B",
) -> CompareABResult:
    """Compare facts from packet-like dictionaries or objects."""
    return compare_metric_collections(_packet_facts(a_packet), _packet_facts(b_packet), a_label, b_label)


def compare_mix_a_to_mix_b(mix_a_state: dict[str, Any], mix_b_state: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper returning factual A/B comparison data."""
    result = compare_packet_facts(mix_a_state, mix_b_state)
    return {
        "mode": result.mode,
        "a_label": result.a_label,
        "b_label": result.b_label,
        "comparisons": [comparison.__dict__ for comparison in result.comparisons],
        "limitations": list(result.limitations),
        "warnings": list(result.warnings),
    }


def validate_compare_context(context: dict[str, Any]) -> dict[str, Any]:
    """Validate that Compare Mode contains only A/B context keys."""
    forbidden_keys = {"reference", "reference_target", "reference_pool", "target", "pool"}
    present_forbidden = sorted(key for key in forbidden_keys if key in context)
    required = {"a", "b"}
    missing = sorted(required - set(context))
    return {
        "valid": not present_forbidden and not missing,
        "missing": missing,
        "forbidden": present_forbidden,
    }
