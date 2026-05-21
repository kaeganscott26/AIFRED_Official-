"""Factual stereo metrics for normalized interleaved sample arrays.

Responsibility:
    Calculate stereo, mid/side, balance, correlation, and mono-compatibility
    facts from verified sample arrays.

This module must not generate advice, infer creative intent, run FFT analysis,
or present unavailable stereo facts as valid measurements.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class StereoMetrics:
    """Factual stereo state without advice or interpretation text."""

    channels: int
    is_mono: bool
    left_peak: float
    right_peak: float | None
    left_rms: float
    right_rms: float | None
    mid_rms: float | None
    side_rms: float | None
    side_to_mid_ratio: float | None
    correlation: float | None
    balance_db: float | None
    mono_compatibility_risk: bool


def _is_finite_number(value: float) -> bool:
    return isinstance(value, (int, float)) and value == value and value not in (float("inf"), float("-inf"))


def _validate_samples(samples: Sequence[float]) -> None:
    for sample in samples:
        if not _is_finite_number(sample):
            raise ValueError("samples must contain finite numeric values only.")


def split_interleaved_stereo(samples: Sequence[float], channels: int) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Split normalized interleaved samples into left and right channels.

    Mono input returns all samples as the left channel and an empty right
    channel. Multichannel input uses the first two channels only.
    """
    if channels <= 0:
        raise ValueError("channels must be greater than zero.")
    _validate_samples(samples)

    if not samples:
        return (), ()
    if channels == 1:
        return tuple(float(sample) for sample in samples), ()

    left = tuple(float(samples[index]) for index in range(0, len(samples), channels))
    right = tuple(float(samples[index]) for index in range(1, len(samples), channels))
    return left, right


def calculate_channel_rms(samples: Sequence[float]) -> float:
    """Calculate RMS for one channel."""
    _validate_samples(samples)
    if not samples:
        return 0.0
    return math.sqrt(sum(float(sample) * float(sample) for sample in samples) / len(samples))


def calculate_channel_peak(samples: Sequence[float]) -> float:
    """Calculate absolute sample peak for one channel."""
    _validate_samples(samples)
    if not samples:
        return 0.0
    return max(abs(float(sample)) for sample in samples)


def calculate_mid_side(left: Sequence[float], right: Sequence[float]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Calculate factual mid and side sample arrays from stereo channels."""
    _validate_samples(left)
    _validate_samples(right)
    frame_count = min(len(left), len(right))
    mid = tuple((float(left[index]) + float(right[index])) * 0.5 for index in range(frame_count))
    side = tuple((float(left[index]) - float(right[index])) * 0.5 for index in range(frame_count))
    return mid, side


def calculate_stereo_correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    """Calculate normalized stereo correlation.

    Returns None when either channel has no measurable energy, because silence
    is unavailable for correlation rather than zero correlation.
    """
    _validate_samples(left)
    _validate_samples(right)
    frame_count = min(len(left), len(right))
    if frame_count == 0:
        return None

    left_values = [float(left[index]) for index in range(frame_count)]
    right_values = [float(right[index]) for index in range(frame_count)]
    left_energy = sum(sample * sample for sample in left_values)
    right_energy = sum(sample * sample for sample in right_values)
    if left_energy == 0.0 or right_energy == 0.0:
        return None

    correlation = sum(l * r for l, r in zip(left_values, right_values)) / math.sqrt(left_energy * right_energy)
    return max(-1.0, min(1.0, correlation))


def calculate_balance_db(left_rms: float, right_rms: float) -> float | None:
    """Calculate L/R RMS balance as left relative to right in dB."""
    if not _is_finite_number(left_rms) or not _is_finite_number(right_rms):
        raise ValueError("RMS values must be finite numbers.")
    if left_rms <= 0.0 or right_rms <= 0.0:
        return None
    return 20.0 * math.log10(left_rms / right_rms)


def calculate_side_to_mid_ratio(mid_rms: float, side_rms: float) -> float | None:
    """Calculate side-to-mid RMS ratio."""
    if not _is_finite_number(mid_rms) or not _is_finite_number(side_rms):
        raise ValueError("RMS values must be finite numbers.")
    if mid_rms <= 0.0:
        return None
    return side_rms / mid_rms


def assess_mono_safety(stereo_metrics: StereoMetrics) -> bool:
    """Return a factual mono-compatibility risk flag from correlation."""
    if stereo_metrics.is_mono or stereo_metrics.correlation is None:
        return False
    return stereo_metrics.correlation < -0.25


def calculate_stereo_metrics(samples: Sequence[float], channels: int) -> StereoMetrics:
    """Calculate factual stereo metrics from normalized interleaved samples."""
    left, right = split_interleaved_stereo(samples, channels)
    is_mono = channels == 1

    left_peak = calculate_channel_peak(left)
    left_rms = calculate_channel_rms(left)

    if is_mono:
        side_rms = 0.0 if left_rms > 0.0 else None
        side_to_mid = calculate_side_to_mid_ratio(left_rms, side_rms) if side_rms is not None else None
        metrics = StereoMetrics(
            channels=channels,
            is_mono=True,
            left_peak=left_peak,
            right_peak=None,
            left_rms=left_rms,
            right_rms=None,
            mid_rms=left_rms,
            side_rms=side_rms,
            side_to_mid_ratio=side_to_mid,
            correlation=None,
            balance_db=None,
            mono_compatibility_risk=False,
        )
        return metrics

    right_peak = calculate_channel_peak(right)
    right_rms = calculate_channel_rms(right)
    mid, side = calculate_mid_side(left, right)
    mid_rms = calculate_channel_rms(mid)
    side_rms = calculate_channel_rms(side)
    correlation = calculate_stereo_correlation(left, right)

    metrics = StereoMetrics(
        channels=channels,
        is_mono=False,
        left_peak=left_peak,
        right_peak=right_peak,
        left_rms=left_rms,
        right_rms=right_rms,
        mid_rms=mid_rms,
        side_rms=side_rms,
        side_to_mid_ratio=calculate_side_to_mid_ratio(mid_rms, side_rms),
        correlation=correlation,
        balance_db=calculate_balance_db(left_rms, right_rms),
        mono_compatibility_risk=False,
    )
    return StereoMetrics(
        channels=metrics.channels,
        is_mono=metrics.is_mono,
        left_peak=metrics.left_peak,
        right_peak=metrics.right_peak,
        left_rms=metrics.left_rms,
        right_rms=metrics.right_rms,
        mid_rms=metrics.mid_rms,
        side_rms=metrics.side_rms,
        side_to_mid_ratio=metrics.side_to_mid_ratio,
        correlation=metrics.correlation,
        balance_db=metrics.balance_db,
        mono_compatibility_risk=assess_mono_safety(metrics),
    )
