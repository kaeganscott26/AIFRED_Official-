"""Dynamics metric interface for factual dynamic-range evidence.

Responsibility:
    Define contracts for crest factor, dynamic range, loudness contrast, and
    compression-risk facts.

This module must not recommend compressor or limiter settings.
"""

from __future__ import annotations

from typing import Any


def calculate_dynamics_metrics(audio: Any, *, level_metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    """Calculate dynamics facts for approved audio input."""
    raise NotImplementedError("Dynamics metric calculation is not implemented yet.")


def identify_dynamics_flags(dynamics_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """Create factual dynamics flags from verified dynamics metrics."""
    raise NotImplementedError("Dynamics flag detection is not implemented yet.")

