"""Level metric interface for factual sample-level evidence.

Responsibility:
    Define contracts for sample peak, RMS, headroom, and ceiling-state facts.

This module must not generate advice, loudness interpretation, or fake meter
values.
"""

from __future__ import annotations

from typing import Any


def calculate_level_metrics(audio: Any, *, window_seconds: float | None = None) -> dict[str, Any]:
    """Calculate level facts for approved audio input."""
    raise NotImplementedError("Level metric calculation is not implemented yet.")


def detect_ceiling_state(level_metrics: dict[str, Any]) -> dict[str, Any]:
    """Derive factual ceiling/clipping flags from verified level metrics."""
    raise NotImplementedError("Ceiling-state detection is not implemented yet.")

