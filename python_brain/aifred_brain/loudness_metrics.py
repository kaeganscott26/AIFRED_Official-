"""Loudness metric interface for factual loudness evidence.

Responsibility:
    Define contracts for integrated, short-term, momentary, and range loudness
    facts.

This module must not confuse LUFS, RMS, dBFS, or dBTP, and must not generate
final user-facing advice.
"""

from __future__ import annotations

from typing import Any


def calculate_loudness_metrics(audio: Any, *, window_seconds: float | None = None) -> dict[str, Any]:
    """Calculate loudness facts for approved audio input."""
    raise NotImplementedError("Loudness metric calculation is not implemented yet.")


def summarize_loudness_availability(metrics: dict[str, Any]) -> dict[str, Any]:
    """Summarize whether loudness evidence is available, limited, or unavailable."""
    raise NotImplementedError("Loudness availability summary is not implemented yet.")

