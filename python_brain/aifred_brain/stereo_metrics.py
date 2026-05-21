"""Stereo metric interface for factual stereo and mono-safety evidence.

Responsibility:
    Define contracts for correlation, mid/side balance, stereo width, L/R
    balance, and mono-safety facts.

This module must not imply stereo safety from unavailable or stale data.
"""

from __future__ import annotations

from typing import Any


def calculate_stereo_metrics(audio: Any, *, frequency_band: tuple[float, float] | None = None) -> dict[str, Any]:
    """Calculate stereo facts for approved audio input."""
    raise NotImplementedError("Stereo metric calculation is not implemented yet.")


def assess_mono_safety(stereo_metrics: dict[str, Any]) -> dict[str, Any]:
    """Create factual mono-safety flags from verified stereo metrics."""
    raise NotImplementedError("Mono-safety assessment is not implemented yet.")

