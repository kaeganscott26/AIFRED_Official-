"""Reference Mode helpers for current-mix vs selected-target facts.

Responsibility:
    Calculate factual deltas between current mix metric facts and an explicit
    selected reference or target. Global pool behavior is not invoked unless a
    caller supplies explicit target data.

This module must not implement Compare A/B behavior, judge which mix is
better, generate advice, or invent metric values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence

from .privacy import redact_private_path


class ReferenceComparisonAvailability(str, Enum):
    """Availability state for one current-vs-target metric comparison."""

    AVAILABLE = "available"
    CURRENT_UNAVAILABLE = "current_unavailable"
    TARGET_UNAVAILABLE = "target_unavailable"
    BOTH_UNAVAILABLE = "both_unavailable"
    NON_NUMERIC = "non_numeric"
    MISSING = "missing"


@dataclass(frozen=True)
class ReferenceMetricComparison:
    """Factual comparison for one current-mix metric against a target metric."""

    name: str
    family: str | None
    unit: str | None
    current_value: object
    target_value: object
    delta_from_target: float | None
    absolute_delta: float | None
    percent_delta_from_target: float | None
    availability: ReferenceComparisonAvailability


@dataclass(frozen=True)
class ReferenceCompareResult:
    """Factual Reference Mode result with no interpretation or advice."""

    mode: str
    current_label: str
    target_label: str
    target_type: str
    comparisons: tuple[ReferenceMetricComparison, ...]
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
        raise ValueError("Reference comparison must not preserve fake placeholder metric values.")


def calculate_delta_from_target(current_value: object, target_value: object) -> float | None:
    """Calculate signed current-minus-target delta for numeric values."""
    _reject_fake_value(current_value)
    _reject_fake_value(target_value)
    if not is_numeric_value(current_value) or not is_numeric_value(target_value):
        return None
    return float(current_value) - float(target_value)


def calculate_percent_delta_from_target(current_value: object, target_value: object) -> float | None:
    """Calculate current-minus-target percent delta relative to target."""
    delta = calculate_delta_from_target(current_value, target_value)
    if delta is None or not is_numeric_value(target_value):
        return None
    denominator = float(target_value)
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


def _text_or_none(value: object) -> str | None:
    value = _enum_value(value)
    if value is None:
        return None
    return redact_private_path(str(value))


def _fact_available(fact: object | None) -> bool:
    if fact is None:
        return False
    if bool(_fact_value(fact, "available", True)) is False:
        return False
    return _fact_value(fact, "value") is not None


def _metric_key(fact: object) -> tuple[str | None, str]:
    return _text_or_none(_fact_value(fact, "family")), str(_fact_value(fact, "name", ""))


def _availability_for(
    current_fact: object | None,
    target_fact: object | None,
) -> ReferenceComparisonAvailability:
    if current_fact is None or target_fact is None:
        return ReferenceComparisonAvailability.MISSING
    current_available = _fact_available(current_fact)
    target_available = _fact_available(target_fact)
    if not current_available and not target_available:
        return ReferenceComparisonAvailability.BOTH_UNAVAILABLE
    if not current_available:
        return ReferenceComparisonAvailability.CURRENT_UNAVAILABLE
    if not target_available:
        return ReferenceComparisonAvailability.TARGET_UNAVAILABLE
    if not is_numeric_value(_fact_value(current_fact, "value")) or not is_numeric_value(_fact_value(target_fact, "value")):
        return ReferenceComparisonAvailability.NON_NUMERIC
    return ReferenceComparisonAvailability.AVAILABLE


def compare_reference_metric(
    current_fact: object | None,
    target_fact: object | None,
) -> ReferenceMetricComparison:
    """Compare one current metric fact against one selected target fact."""
    availability = _availability_for(current_fact, target_fact)
    source_fact = current_fact if current_fact is not None else target_fact
    name = str(_fact_value(source_fact, "name", ""))
    family = _text_or_none(_fact_value(source_fact, "family"))
    unit = _text_or_none(_fact_value(current_fact, "unit", _fact_value(target_fact, "unit")))
    current_value = _fact_value(current_fact, "value")
    target_value = _fact_value(target_fact, "value")
    _reject_fake_value(current_value)
    _reject_fake_value(target_value)

    delta = (
        calculate_delta_from_target(current_value, target_value)
        if availability is ReferenceComparisonAvailability.AVAILABLE
        else None
    )
    return ReferenceMetricComparison(
        name=name,
        family=family,
        unit=unit,
        current_value=current_value,
        target_value=target_value,
        delta_from_target=delta,
        absolute_delta=None if delta is None else abs(delta),
        percent_delta_from_target=(
            calculate_percent_delta_from_target(current_value, target_value)
            if availability is ReferenceComparisonAvailability.AVAILABLE
            else None
        ),
        availability=availability,
    )


def _index_facts(facts: Sequence[object]) -> dict[tuple[str | None, str], object]:
    indexed: dict[tuple[str | None, str], object] = {}
    for fact in facts:
        indexed[_metric_key(fact)] = fact
    return indexed


def compare_reference_collections(
    current_facts: Sequence[object],
    target_facts: Sequence[object],
    current_label: str = "Current Mix",
    target_label: str = "Selected Reference",
    target_type: str = "selected_reference",
) -> ReferenceCompareResult:
    """Compare current metric facts against selected target metric facts."""
    current_index = _index_facts(tuple(current_facts))
    target_index = _index_facts(tuple(target_facts))
    keys = sorted(set(current_index) | set(target_index), key=lambda item: (str(item[0]), item[1]))
    comparisons = tuple(compare_reference_metric(current_index.get(key), target_index.get(key)) for key in keys)
    limitations: list[str] = []
    if any(comparison.availability is not ReferenceComparisonAvailability.AVAILABLE for comparison in comparisons):
        limitations.append(
            "Some target-relative metric deltas are unavailable because one or both facts are missing, unavailable, or non-numeric."
        )

    return ReferenceCompareResult(
        mode="Reference",
        current_label=redact_private_path(str(current_label)),
        target_label=redact_private_path(str(target_label)),
        target_type=redact_private_path(str(target_type)),
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


def compare_packet_to_reference(
    current_packet: object,
    reference_packet: object,
    current_label: str = "Current Mix",
    target_label: str = "Selected Reference",
    target_type: str = "selected_reference",
) -> ReferenceCompareResult:
    """Compare facts from packet-like dictionaries or objects against target facts."""
    return compare_reference_collections(
        _packet_facts(current_packet),
        _packet_facts(reference_packet),
        current_label,
        target_label,
        target_type,
    )


def _comparison_to_dict(comparison: ReferenceMetricComparison) -> dict[str, object]:
    return {
        "name": comparison.name,
        "family": comparison.family,
        "unit": comparison.unit,
        "current_value": comparison.current_value,
        "target_value": comparison.target_value,
        "delta_from_target": comparison.delta_from_target,
        "absolute_delta": comparison.absolute_delta,
        "percent_delta_from_target": comparison.percent_delta_from_target,
        "availability": comparison.availability.value,
    }


def compare_to_reference(current_state: dict[str, Any], reference_state: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper returning factual selected-reference comparison data."""
    result = compare_packet_to_reference(current_state, reference_state)
    return {
        "mode": result.mode,
        "current_label": result.current_label,
        "target_label": result.target_label,
        "target_type": result.target_type,
        "comparisons": [_comparison_to_dict(comparison) for comparison in result.comparisons],
        "limitations": list(result.limitations),
        "warnings": list(result.warnings),
    }


def validate_reference_context(context: dict[str, Any]) -> dict[str, Any]:
    """Validate that Reference Mode has an explicit selected target."""
    target_keys = {"target", "reference", "reference_target", "selected_reference"}
    has_target = any(key in context and context[key] is not None for key in target_keys)
    compare_only_keys = {"a", "b", "mix_a", "mix_b"}
    present_compare_keys = sorted(key for key in compare_only_keys if key in context)
    return {
        "valid": has_target and not present_compare_keys,
        "missing": [] if has_target else ["selected_target"],
        "forbidden": present_compare_keys,
    }
