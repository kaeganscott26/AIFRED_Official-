"""Interpretation packet assembly for downstream AI input facts.

Responsibility:
    Package verified facts, mode, source labels, selected metric families,
    privacy-safe metadata, warnings, and limitations for a later interpretation
    layer.

This module must not generate final user-facing advice, canned response text,
metric values, report writing, compare analysis, or reference comparison.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence

from .metric_relevance import MetricFamily
from .privacy import scrub_private_metadata


class PacketAvailability(str, Enum):
    """Availability state for a factual interpretation packet."""

    READY = "ready"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class MetricFact:
    """Single factual metric value for packet assembly."""

    family: MetricFamily
    name: str
    value: object
    unit: str | None = None
    available: bool = True
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class InterpretationPacket:
    """Structured facts for downstream interpretation, without final prose."""

    question: str
    mode: str
    source_label: str
    confidence: str
    freshness: str
    availability: PacketAvailability
    metric_families: tuple[MetricFamily, ...]
    facts: tuple[MetricFact, ...]
    limitations: tuple[str, ...]
    warnings: tuple[str, ...]
    metadata: dict[str, object]
    session_label: str | None = None


def _enum_value(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _coerce_metric_family(value: MetricFamily | str) -> MetricFamily:
    if isinstance(value, MetricFamily):
        return value
    return MetricFamily(str(value))


def _reject_fake_value(value: object) -> None:
    if isinstance(value, (int, float)) and value == -999:
        raise ValueError("Metric facts must not use fake placeholder values.")


def create_metric_fact(
    family: MetricFamily | str,
    name: str,
    value: object,
    unit: str | None = None,
    available: bool = True,
    limitations: Sequence[str] = (),
) -> MetricFact:
    """Create a factual metric entry for an interpretation packet."""
    _reject_fake_value(value)
    return MetricFact(
        family=_coerce_metric_family(family),
        name=str(name),
        value=value,
        unit=unit,
        available=bool(available),
        limitations=tuple(str(limitation) for limitation in limitations),
    )


def sanitize_packet_metadata(metadata: dict[str, object] | None) -> dict[str, object]:
    """Return privacy-safe packet metadata without full local paths."""
    if metadata is None:
        return {}
    return scrub_private_metadata(dict(metadata))


def determine_packet_availability(
    facts: Sequence[MetricFact],
    limitations: Sequence[str] = (),
) -> PacketAvailability:
    """Determine packet availability from factual data and limitations."""
    fact_tuple = tuple(facts)
    limitation_tuple = tuple(limitations)
    if not fact_tuple:
        return PacketAvailability.LIMITED if limitation_tuple else PacketAvailability.UNAVAILABLE
    if not any(fact.available for fact in fact_tuple):
        return PacketAvailability.LIMITED if limitation_tuple else PacketAvailability.UNAVAILABLE
    if limitation_tuple or any(fact.limitations for fact in fact_tuple):
        return PacketAvailability.LIMITED
    return PacketAvailability.READY


def _context_value(analysis_context: object, attribute: str, fallback: str = "") -> str:
    if isinstance(analysis_context, dict):
        value = analysis_context.get(attribute, fallback)
        if attribute == "source_label" and value == fallback:
            value = analysis_context.get("source", fallback)
    else:
        source_attribute = "source" if attribute == "source_label" else attribute
        value = getattr(analysis_context, source_attribute, fallback)
    return _enum_value(value)


def _selected_metric_families(relevance_result: object) -> tuple[MetricFamily, ...]:
    if isinstance(relevance_result, dict):
        primary = relevance_result.get("primary_metrics", ())
        secondary = relevance_result.get("secondary_metrics", ())
    else:
        primary = getattr(relevance_result, "primary_metrics", ())
        secondary = getattr(relevance_result, "secondary_metrics", ())

    seen: set[MetricFamily] = set()
    families: list[MetricFamily] = []
    for family in (*primary, *secondary):
        metric_family = _coerce_metric_family(family)
        if metric_family not in seen:
            seen.add(metric_family)
            families.append(metric_family)
    return tuple(families)


def create_interpretation_packet(
    question: str,
    analysis_context: object,
    relevance_result: object,
    facts: Sequence[MetricFact] | None = None,
    limitations: Sequence[str] = (),
    warnings: Sequence[str] = (),
    metadata: dict[str, object] | None = None,
    session_label: str | None = None,
) -> InterpretationPacket:
    """Create a structured factual packet for downstream interpretation."""
    fact_tuple = tuple(facts or ())
    limitation_tuple = tuple(str(limitation) for limitation in limitations)
    return InterpretationPacket(
        question=str(question),
        mode=_context_value(analysis_context, "mode"),
        source_label=_context_value(analysis_context, "source_label"),
        confidence=_context_value(analysis_context, "confidence"),
        freshness=_context_value(analysis_context, "freshness"),
        availability=determine_packet_availability(fact_tuple, limitation_tuple),
        metric_families=_selected_metric_families(relevance_result),
        facts=fact_tuple,
        limitations=limitation_tuple,
        warnings=tuple(str(warning) for warning in warnings),
        metadata=sanitize_packet_metadata(metadata),
        session_label=session_label,
    )


def _fact_to_dict(fact: MetricFact) -> dict[str, object]:
    return {
        "family": fact.family.value,
        "name": fact.name,
        "value": fact.value,
        "unit": fact.unit,
        "available": fact.available,
        "limitations": list(fact.limitations),
    }


def packet_to_dict(packet: InterpretationPacket) -> dict[str, object]:
    """Return a standard-library serializable packet dictionary."""
    return {
        "question": packet.question,
        "mode": packet.mode,
        "source_label": packet.source_label,
        "confidence": packet.confidence,
        "freshness": packet.freshness,
        "availability": packet.availability.value,
        "metric_families": [family.value for family in packet.metric_families],
        "facts": [_fact_to_dict(fact) for fact in packet.facts],
        "limitations": list(packet.limitations),
        "warnings": list(packet.warnings),
        "metadata": packet.metadata,
        "session_label": packet.session_label,
    }


def build_interpretation_packet(
    *,
    analysis_state: dict[str, Any],
    selected_metrics: dict[str, Any],
    user_question: str | None,
) -> dict[str, Any]:
    """Compatibility wrapper that returns a factual packet dictionary."""
    relevance_result = {
        "primary_metrics": tuple(selected_metrics.get("primary_metrics", ())),
        "secondary_metrics": tuple(selected_metrics.get("secondary_metrics", ())),
    }
    facts = tuple(selected_metrics.get("facts", ()))
    packet = create_interpretation_packet(
        question=user_question or "",
        analysis_context=analysis_state,
        relevance_result=relevance_result,
        facts=facts,
        limitations=tuple(analysis_state.get("limitations", ())),
        warnings=tuple(analysis_state.get("warnings", ())),
        metadata=analysis_state.get("metadata") if isinstance(analysis_state.get("metadata"), dict) else None,
        session_label=analysis_state.get("session_label"),
    )
    return packet_to_dict(packet)


def validate_interpretation_packet(packet: dict[str, Any]) -> dict[str, Any]:
    """Validate required factual packet fields without interpreting content."""
    required = {"question", "mode", "source_label", "confidence", "freshness", "availability", "metric_families", "facts"}
    missing = sorted(required - set(packet))
    return {"valid": not missing, "missing": missing}
