"""Level metrics for factual sample-level evidence.

Responsibility:
    Calculate sample peak, RMS, crest factor, and ceiling-state facts from
    normalized PCM samples.

This module must not generate advice, loudness interpretation, LUFS, true peak
oversampling, or fake meter values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

from .validation import InvalidAudioBufferError


@dataclass(frozen=True)
class LevelMetrics:
    """Factual level metrics with explicit unavailable states as `None`."""

    sample_peak_linear: float
    sample_peak_dbfs: float | None
    rms_linear: float
    rms_dbfs: float | None
    crest_factor_db: float | None
    is_silent: bool
    has_sample_clip: bool
    ceiling_dbfs: float
    ceiling_margin_db: float | None
    is_ceiling_safe: bool | None


def linear_to_dbfs(value: float) -> float | None:
    """Convert a positive normalized linear value to dBFS."""
    if value < 0:
        raise ValueError("Linear amplitude cannot be negative.")
    if value == 0:
        return None
    return 20.0 * math.log10(value)


def _validate_samples(samples: Sequence[float]) -> None:
    for sample in samples:
        if not isinstance(sample, (int, float)):
            raise InvalidAudioBufferError("Audio samples must be numeric.")
        if math.isnan(float(sample)) or math.isinf(float(sample)):
            raise InvalidAudioBufferError("Audio samples must be finite.")


def calculate_sample_peak(samples: Sequence[float]) -> float:
    """Calculate absolute sample peak from normalized samples."""
    _validate_samples(samples)
    if not samples:
        return 0.0
    return max(abs(float(sample)) for sample in samples)


def calculate_rms(samples: Sequence[float]) -> float:
    """Calculate RMS from normalized samples."""
    _validate_samples(samples)
    if not samples:
        return 0.0
    mean_square = sum(float(sample) * float(sample) for sample in samples) / len(samples)
    return math.sqrt(mean_square)


def calculate_crest_factor_db(peak_linear: float, rms_linear: float) -> float | None:
    """Calculate crest factor in dB when both peak and RMS are available."""
    if peak_linear < 0 or rms_linear < 0:
        raise ValueError("Peak and RMS must be non-negative.")
    if peak_linear == 0 or rms_linear == 0:
        return None
    return 20.0 * math.log10(peak_linear / rms_linear)


def calculate_level_metrics(samples: Sequence[float], ceiling_dbfs: float = -1.0) -> LevelMetrics:
    """Calculate factual level metrics from normalized PCM samples."""
    peak = calculate_sample_peak(samples)
    rms = calculate_rms(samples)
    peak_dbfs = linear_to_dbfs(peak)
    rms_dbfs = linear_to_dbfs(rms)
    crest = calculate_crest_factor_db(peak, rms)
    is_silent = peak == 0 and rms == 0
    has_sample_clip = any(abs(float(sample)) >= 1.0 for sample in samples)
    ceiling_margin = None if peak_dbfs is None else ceiling_dbfs - peak_dbfs
    is_ceiling_safe = None if peak_dbfs is None else peak_dbfs <= ceiling_dbfs

    return LevelMetrics(
        sample_peak_linear=peak,
        sample_peak_dbfs=peak_dbfs,
        rms_linear=rms,
        rms_dbfs=rms_dbfs,
        crest_factor_db=crest,
        is_silent=is_silent,
        has_sample_clip=has_sample_clip,
        ceiling_dbfs=ceiling_dbfs,
        ceiling_margin_db=ceiling_margin,
        is_ceiling_safe=is_ceiling_safe,
    )


def detect_ceiling_state(level_metrics: dict[str, Any]) -> dict[str, Any]:
    """Derive factual ceiling/clipping flags from verified level metrics."""
    peak_dbfs = level_metrics.get("sample_peak_dbfs")
    ceiling_dbfs = level_metrics.get("ceiling_dbfs", -1.0)
    if peak_dbfs is None:
        return {
            "is_ceiling_safe": None,
            "ceiling_margin_db": None,
            "has_sample_clip": bool(level_metrics.get("has_sample_clip", False)),
        }
    return {
        "is_ceiling_safe": peak_dbfs <= ceiling_dbfs,
        "ceiling_margin_db": ceiling_dbfs - peak_dbfs,
        "has_sample_clip": bool(level_metrics.get("has_sample_clip", False)),
    }
