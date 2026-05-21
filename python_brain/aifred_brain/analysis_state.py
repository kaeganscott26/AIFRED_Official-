"""Analysis state objects for mode, source, confidence, and freshness.

Responsibility:
    Represent explicit source-of-truth state and mode separation.

This module must not blur Analyze, Reference, and Compare contexts or invent
metric values.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, field, replace
from enum import Enum
from typing import Any, Mapping, Sequence

from .privacy import scrub_private_metadata


class AnalysisMode(str, Enum):
    """Supported analysis modes."""

    ANALYZE = "analyze"
    REFERENCE = "reference"
    COMPARE = "compare"


class SourceLabel(str, Enum):
    """Allowed source-of-truth labels."""

    LIVE_BUFFER = "Live Buffer"
    LAST_SNAPSHOT = "Last Snapshot"
    FILE_ANALYSIS = "File Analysis"
    COMPARE_AB = "Compare A/B"
    REFERENCE_MODE = "Reference Mode"
    EXPORT_HISTORY = "Export History"
    SAVED_REPORT = "Saved Report"
    GENERAL_ADVICE = "General Advice"
    METER_ONLY_FALLBACK = "Meter-Only Fallback"
    NO_AI_FALLBACK = "No-AI Fallback"


class ConfidenceState(str, Enum):
    """Practical confidence states, avoiding fake precision."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNAVAILABLE = "Unavailable"


class DataFreshness(str, Enum):
    """Freshness states distinct from numeric zero."""

    LIVE = "live"
    RECENT = "recent"
    STALE = "stale"
    WAITING = "waiting"
    UNAVAILABLE = "unavailable"


class AnalysisAvailability(str, Enum):
    """Availability state for a complete factual analysis result."""

    READY = "ready"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class AnalysisContext:
    """Factual analysis context with no metric values."""

    mode: AnalysisMode
    source: SourceLabel
    confidence: ConfidenceState
    freshness: DataFreshness
    sample_rate: int | None = None
    duration_seconds: float | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_available_data(self) -> bool:
        """Return whether the context represents available data."""
        return self.freshness not in {DataFreshness.WAITING, DataFreshness.UNAVAILABLE}


AnalysisState = AnalysisContext


@dataclass(frozen=True)
class AnalysisMetricBundle:
    """Already-calculated metric outputs grouped without changing values."""

    level: object | None = None
    loudness: object | None = None
    stereo: object | None = None
    frequency: object | None = None
    tonal_balance: object | None = None
    dynamics: object | None = None
    transients: object | None = None
    compare: object | None = None
    reference: object | None = None


@dataclass(frozen=True)
class AnalysisResult:
    """End-to-end factual analysis assembly without interpretation."""

    context: AnalysisContext
    availability: AnalysisAvailability
    metrics: AnalysisMetricBundle
    limitations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


def _coerce_enum(enum_type: type[Enum], value: Any) -> Enum:
    if isinstance(value, enum_type):
        return value
    return enum_type(value)


def create_analysis_state(
    *,
    mode: AnalysisMode | str,
    source_label: SourceLabel | str,
    confidence: ConfidenceState | str = ConfidenceState.UNAVAILABLE,
    freshness: DataFreshness | str = DataFreshness.WAITING,
    sample_rate: int | None = None,
    duration_seconds: float | None = None,
    notes: tuple[str, ...] | list[str] = (),
) -> AnalysisState:
    """Create explicit analysis state for downstream factual processing."""
    return AnalysisContext(
        mode=_coerce_enum(AnalysisMode, mode),  # type: ignore[arg-type]
        source=_coerce_enum(SourceLabel, source_label),  # type: ignore[arg-type]
        confidence=_coerce_enum(ConfidenceState, confidence),  # type: ignore[arg-type]
        freshness=_coerce_enum(DataFreshness, freshness),  # type: ignore[arg-type]
        sample_rate=sample_rate,
        duration_seconds=duration_seconds,
        notes=tuple(notes),
    )


def create_analysis_context(
    mode: AnalysisMode | str,
    source: SourceLabel | str,
    confidence: ConfidenceState | str | None = None,
    freshness: DataFreshness | str | None = None,
    sample_rate: int | None = None,
    duration_seconds: float | None = None,
    notes: Sequence[str] = (),
) -> AnalysisContext:
    """Create explicit analysis context for end-to-end factual assembly."""
    return create_analysis_state(
        mode=mode,
        source_label=source,
        confidence=confidence or ConfidenceState.UNAVAILABLE,
        freshness=freshness or DataFreshness.WAITING,
        sample_rate=sample_rate,
        duration_seconds=duration_seconds,
        notes=tuple(notes),
    )


def mark_state_stale(state: AnalysisState, *, reason: str) -> AnalysisState:
    """Return state marked as stale with a factual reason."""
    notes = (*state.notes, reason)
    return replace(state, freshness=DataFreshness.STALE, confidence=ConfidenceState.LOW, notes=notes)


def _reject_fake_value(value: object) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) == -999.0:
        raise ValueError("Analysis assembly must not preserve fake placeholder metric values.")
    if isinstance(value, Mapping):
        for nested_value in value.values():
            _reject_fake_value(nested_value)
    elif is_dataclass(value) and not isinstance(value, type):
        for metric_field in fields(value):
            _reject_fake_value(getattr(value, metric_field.name))
    elif isinstance(value, (list, tuple)):
        for nested_value in value:
            _reject_fake_value(nested_value)


def _metric_output_available(metric_output: object | None) -> bool:
    if metric_output is None:
        return False
    _reject_fake_value(metric_output)

    if isinstance(metric_output, Mapping):
        if metric_output.get("available") is False:
            return False
        if metric_output.get("state") in {"unavailable", "stale"}:
            return False
        if metric_output.get("availability") in {"unavailable", "both_unavailable"}:
            return False
        return True

    available = getattr(metric_output, "available", None)
    if available is False:
        return False
    availability = getattr(metric_output, "availability", None)
    if isinstance(availability, Enum):
        availability = availability.value
    if availability in {"unavailable", "both_unavailable"}:
        return False
    return True


def _bundle_values(metrics: AnalysisMetricBundle) -> tuple[object | None, ...]:
    return tuple(getattr(metrics, metric_field.name) for metric_field in fields(metrics))


def create_analysis_metric_bundle(**metric_outputs: object) -> AnalysisMetricBundle:
    """Create a grouped metric bundle from already-calculated outputs."""
    allowed_fields = {metric_field.name for metric_field in fields(AnalysisMetricBundle)}
    unknown_fields = sorted(set(metric_outputs) - allowed_fields)
    if unknown_fields:
        raise ValueError(f"Unsupported analysis metric bundle fields: {', '.join(unknown_fields)}")
    for metric_output in metric_outputs.values():
        _reject_fake_value(metric_output)
    return AnalysisMetricBundle(**metric_outputs)


def determine_analysis_availability(
    metrics: AnalysisMetricBundle,
    limitations: Sequence[str] = (),
) -> AnalysisAvailability:
    """Determine factual result availability from included metrics."""
    limitation_tuple = tuple(str(limitation) for limitation in limitations)
    has_available_metrics = any(_metric_output_available(metric_output) for metric_output in _bundle_values(metrics))

    if not has_available_metrics:
        return AnalysisAvailability.LIMITED if limitation_tuple else AnalysisAvailability.UNAVAILABLE
    if limitation_tuple:
        return AnalysisAvailability.LIMITED
    return AnalysisAvailability.READY


def create_analysis_result(
    context: AnalysisContext,
    metrics: AnalysisMetricBundle,
    limitations: Sequence[str] = (),
    warnings: Sequence[str] = (),
    metadata: dict[str, object] | None = None,
) -> AnalysisResult:
    """Assemble available factual analysis outputs into one result object."""
    limitation_tuple = tuple(str(limitation) for limitation in limitations)
    return AnalysisResult(
        context=context,
        availability=determine_analysis_availability(metrics, limitation_tuple),
        metrics=metrics,
        limitations=limitation_tuple,
        warnings=tuple(str(warning) for warning in warnings),
        metadata=scrub_private_metadata(dict(metadata or {})),
    )


def _to_dict_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, AnalysisContext):
        return {
            "mode": value.mode.value,
            "source_label": value.source.value,
            "confidence": value.confidence.value,
            "freshness": value.freshness.value,
            "sample_rate": value.sample_rate,
            "duration_seconds": value.duration_seconds,
            "notes": list(value.notes),
        }
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _to_dict_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _to_dict_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_dict_value(item) for item in value]
    if isinstance(value, list):
        return [_to_dict_value(item) for item in value]
    return value


def analysis_result_to_dict(result: AnalysisResult) -> dict[str, object]:
    """Return a standard-library serializable factual result dictionary."""
    _reject_fake_value(result)
    return {
        "context": _to_dict_value(result.context),
        "availability": result.availability.value,
        "metrics": _to_dict_value(result.metrics),
        "limitations": list(result.limitations),
        "warnings": list(result.warnings),
        "metadata": _to_dict_value(result.metadata),
    }
