"""Tonal balance interface for factual tonal evidence.

Responsibility:
    Define contracts for tonal tilt, low-mid buildup, presence, harshness, and
    air-band factual summaries.

This module must not turn tonal facts into final advice.
"""

from __future__ import annotations

from typing import Any


def calculate_tonal_balance(frequency_metrics: dict[str, Any], *, mode: str) -> dict[str, Any]:
    """Calculate tonal-balance facts from verified frequency metrics."""
    raise NotImplementedError("Tonal balance calculation is not implemented yet.")


def summarize_tonal_flags(tonal_balance: dict[str, Any]) -> list[dict[str, Any]]:
    """Create factual tonal flags from verified tonal-balance facts."""
    raise NotImplementedError("Tonal flag summary is not implemented yet.")

