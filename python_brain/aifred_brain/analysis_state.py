"""Analysis state objects for mode, source, confidence, and freshness.

Responsibility:
    Represent explicit source-of-truth state and mode separation.

This module must not blur Analyze, Reference, and Compare contexts or invent
metric values.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any


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


def mark_state_stale(state: AnalysisState, *, reason: str) -> AnalysisState:
    """Return state marked as stale with a factual reason."""
    notes = (*state.notes, reason)
    return replace(state, freshness=DataFreshness.STALE, confidence=ConfidenceState.LOW, notes=notes)
