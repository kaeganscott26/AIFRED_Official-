"""Analysis state interface for mode, source, confidence, and freshness.

Responsibility:
    Define contracts for explicit source-of-truth state and mode separation.

This module must not blur Analyze, Reference, and Compare contexts.
"""

from __future__ import annotations

from typing import Any, Literal

AnalysisMode = Literal["analyze", "reference", "compare"]
SourceLabel = Literal[
    "Live Buffer",
    "Last Snapshot",
    "File Analysis",
    "Compare A/B",
    "Reference Mode",
    "Export History",
    "Saved Report",
    "General Advice",
    "Meter-Only Fallback",
    "No-AI Fallback",
]
ConfidenceState = Literal["High", "Medium", "Low"]


class AnalysisState:
    """Contract placeholder for factual analysis state."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("AnalysisState data model is not implemented yet.")


def create_analysis_state(*, mode: AnalysisMode, source_label: SourceLabel) -> AnalysisState:
    """Create explicit analysis state for downstream factual processing."""
    raise NotImplementedError("Analysis state creation is not implemented yet.")


def mark_state_stale(state: AnalysisState, *, reason: str) -> AnalysisState:
    """Return state marked as stale with a factual reason."""
    raise NotImplementedError("Stale-state handling is not implemented yet.")

