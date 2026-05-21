"""Loudness metric interfaces for future BS.1770-style evidence.

Responsibility:
    Define contracts for future momentary, short-term, integrated, and range
    loudness facts.

This module must not implement LUFS until `python_brain/LOUDNESS_ALGORITHM_CONTRACT.md`
is approved for the next implementation phase. It must not confuse RMS, dBFS,
LUFS, dBTP, sample peak, or true peak, and must not generate final user-facing
advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class LoudnessMetrics:
    """Future loudness result container.

    Values remain unavailable until a BS.1770-style implementation is approved.
    """

    momentary_lufs: float | None
    short_term_lufs: float | None
    integrated_lufs: float | None
    loudness_range_lu: float | None
    true_peak_dbtp: float | None
    availability: str
    limitations: tuple[str, ...] = ()


def calculate_momentary_loudness(samples: Sequence[float], sample_rate: int, *, window_seconds: float = 0.4) -> float | None:
    """Future momentary LUFS calculation over an approximately 400 ms window."""
    raise NotImplementedError("Momentary loudness is not implemented yet.")


def calculate_short_term_loudness(samples: Sequence[float], sample_rate: int, *, window_seconds: float = 3.0) -> float | None:
    """Future short-term LUFS calculation over an approximately 3 second window."""
    raise NotImplementedError("Short-term loudness is not implemented yet.")


def calculate_integrated_loudness(samples: Sequence[float], sample_rate: int, *, channels: int = 1) -> float | None:
    """Future integrated LUFS calculation with approved gating behavior."""
    raise NotImplementedError("Integrated loudness is not implemented yet.")


def calculate_loudness_metrics(audio: Any, *, window_seconds: float | None = None) -> LoudnessMetrics:
    """Future BS.1770-style loudness metrics for approved audio input."""
    _ = (audio, window_seconds)
    raise NotImplementedError("Loudness metric calculation is not implemented yet.")


def summarize_loudness_availability(metrics: dict[str, Any]) -> dict[str, Any]:
    """Summarize whether loudness evidence is available, limited, or unavailable."""
    _ = metrics
    raise NotImplementedError("Loudness availability summary is not implemented yet.")
