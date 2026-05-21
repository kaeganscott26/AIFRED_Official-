"""Frequency metric interface for factual band-energy evidence.

Responsibility:
    Define contracts for frequency-band energy, masking evidence, and band
    balance facts.

This module must not infer genre targets or reference deltas unless the active
mode and source state allow it.
"""

from __future__ import annotations

from typing import Any, Sequence


def calculate_frequency_metrics(audio: Any, *, bands: Sequence[tuple[float, float]] | None = None) -> dict[str, Any]:
    """Calculate frequency-band facts for approved audio input."""
    raise NotImplementedError("Frequency metric calculation is not implemented yet.")


def identify_band_flags(frequency_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """Create factual band-related flags from verified frequency metrics."""
    raise NotImplementedError("Frequency flag detection is not implemented yet.")

