"""Dynamics metrics for factual dynamic-range evidence.

Responsibility:
    Calculate windowed RMS, peak, crest factor, and dynamic range facts from
    normalized PCM samples.

This module must not generate processor advice, transient detection,
subjective labels, reference comparison, or fake metric values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

from .level_metrics import calculate_crest_factor_db, calculate_rms, calculate_sample_peak
from .validation import InvalidAudioBufferError


@dataclass(frozen=True)
class DynamicsWindow:
    """Factual dynamics values for one sample window."""

    start_sample: int
    sample_count: int
    rms: float
    peak: float
    crest_factor_db: float | None


@dataclass(frozen=True)
class DynamicsMetrics:
    """Factual dynamics summary with unavailable dB ranges as `None`."""

    window_count: int
    window_seconds: float
    rms_min: float | None
    rms_max: float | None
    rms_range_db: float | None
    peak_min: float | None
    peak_max: float | None
    peak_range_db: float | None
    crest_factor_min_db: float | None
    crest_factor_max_db: float | None
    crest_factor_range_db: float | None
    dynamic_range_db: float | None
    available: bool


def _validate_sample_rate(sample_rate: int) -> None:
    if not isinstance(sample_rate, int) or sample_rate <= 0:
        raise InvalidAudioBufferError("Sample rate must be a positive integer.")


def _validate_window_seconds(window_seconds: float) -> None:
    if not isinstance(window_seconds, (int, float)):
        raise InvalidAudioBufferError("Window duration must be numeric.")
    if math.isnan(float(window_seconds)) or math.isinf(float(window_seconds)) or float(window_seconds) <= 0:
        raise InvalidAudioBufferError("Window duration must be a positive finite value.")


def _validate_samples(samples: Sequence[float]) -> None:
    for sample in samples:
        if not isinstance(sample, (int, float)):
            raise InvalidAudioBufferError("Audio samples must be numeric.")
        if math.isnan(float(sample)) or math.isinf(float(sample)):
            raise InvalidAudioBufferError("Audio samples must be finite.")


def build_dynamics_windows(
    samples: Sequence[float],
    sample_rate: int,
    window_seconds: float = 0.100,
    include_incomplete: bool = False,
) -> tuple[DynamicsWindow, ...]:
    """Split normalized samples into windows and calculate per-window facts."""
    _validate_sample_rate(sample_rate)
    _validate_window_seconds(window_seconds)
    _validate_samples(samples)

    window_sample_count = int(sample_rate * float(window_seconds))
    if window_sample_count <= 0:
        raise InvalidAudioBufferError("Window duration is too short for the sample rate.")
    if not samples:
        return ()

    windows: list[DynamicsWindow] = []
    for start_sample in range(0, len(samples), window_sample_count):
        sample_window = samples[start_sample : start_sample + window_sample_count]
        if len(sample_window) < window_sample_count and not include_incomplete:
            continue
        rms = calculate_rms(sample_window)
        peak = calculate_sample_peak(sample_window)
        windows.append(
            DynamicsWindow(
                start_sample=start_sample,
                sample_count=len(sample_window),
                rms=rms,
                peak=peak,
                crest_factor_db=calculate_crest_factor_db(peak, rms),
            )
        )
    return tuple(windows)


def calculate_db_range(min_linear: float, max_linear: float) -> float | None:
    """Calculate a dB range between positive linear values."""
    if not isinstance(min_linear, (int, float)) or not isinstance(max_linear, (int, float)):
        raise ValueError("Linear values must be numeric.")
    min_value = float(min_linear)
    max_value = float(max_linear)
    if math.isnan(min_value) or math.isinf(min_value) or math.isnan(max_value) or math.isinf(max_value):
        raise ValueError("Linear values must be finite.")
    if min_value < 0 or max_value < 0:
        raise ValueError("Linear values must be non-negative.")
    if max_value < min_value:
        raise ValueError("Maximum linear value must be greater than or equal to minimum.")
    if min_value == 0 or max_value == 0:
        return None
    return 20.0 * math.log10(max_value / min_value)


def calculate_percentile(values: Sequence[float], percentile: float) -> float | None:
    """Calculate a linear-interpolated percentile from finite numeric values."""
    if not isinstance(percentile, (int, float)):
        raise ValueError("Percentile must be numeric.")
    percentile_value = float(percentile)
    if math.isnan(percentile_value) or math.isinf(percentile_value):
        raise ValueError("Percentile must be finite.")
    if percentile_value < 0 or percentile_value > 100:
        raise ValueError("Percentile must be between 0 and 100.")

    cleaned: list[float] = []
    for value in values:
        if not isinstance(value, (int, float)):
            raise ValueError("Percentile values must be numeric.")
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            raise ValueError("Percentile values must be finite.")
        cleaned.append(numeric)
    if not cleaned:
        return None

    ordered = sorted(cleaned)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * (percentile_value / 100.0)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return ordered[int(position)]
    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]
    fraction = position - lower_index
    return lower_value + (upper_value - lower_value) * fraction


def calculate_dynamic_range_db(window_rms_values: Sequence[float]) -> float | None:
    """Calculate dynamic range between quiet and loud positive RMS windows."""
    positive_values: list[float] = []
    for value in window_rms_values:
        if not isinstance(value, (int, float)):
            raise ValueError("RMS values must be numeric.")
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            raise ValueError("RMS values must be finite.")
        if numeric < 0:
            raise ValueError("RMS values must be non-negative.")
        if numeric > 0:
            positive_values.append(numeric)

    if not positive_values:
        return None

    quiet_rms = calculate_percentile(positive_values, 10.0)
    loud_rms = calculate_percentile(positive_values, 95.0)
    if quiet_rms is None or loud_rms is None:
        return None
    return calculate_db_range(quiet_rms, loud_rms)


def _range_from_values(values: Sequence[float]) -> tuple[float | None, float | None, float | None]:
    if not values:
        return None, None, None
    minimum = min(values)
    maximum = max(values)
    return minimum, maximum, calculate_db_range(minimum, maximum)


def _linear_range_from_windows(windows: Sequence[DynamicsWindow], field_name: str) -> tuple[float | None, float | None, float | None]:
    return _range_from_values(tuple(float(getattr(window, field_name)) for window in windows))


def _crest_range_from_windows(windows: Sequence[DynamicsWindow]) -> tuple[float | None, float | None, float | None]:
    values = tuple(window.crest_factor_db for window in windows if window.crest_factor_db is not None)
    if not values:
        return None, None, None
    minimum = min(values)
    maximum = max(values)
    return minimum, maximum, maximum - minimum


def calculate_dynamics_metrics(
    samples: Sequence[float],
    sample_rate: int,
    window_seconds: float = 0.100,
) -> DynamicsMetrics:
    """Calculate factual windowed dynamics metrics from normalized samples."""
    windows = build_dynamics_windows(samples, sample_rate, window_seconds)
    rms_min, rms_max, rms_range_db = _linear_range_from_windows(windows, "rms")
    peak_min, peak_max, peak_range_db = _linear_range_from_windows(windows, "peak")
    crest_min, crest_max, crest_range = _crest_range_from_windows(windows)

    return DynamicsMetrics(
        window_count=len(windows),
        window_seconds=float(window_seconds),
        rms_min=rms_min,
        rms_max=rms_max,
        rms_range_db=rms_range_db,
        peak_min=peak_min,
        peak_max=peak_max,
        peak_range_db=peak_range_db,
        crest_factor_min_db=crest_min,
        crest_factor_max_db=crest_max,
        crest_factor_range_db=crest_range,
        dynamic_range_db=calculate_dynamic_range_db(tuple(window.rms for window in windows)),
        available=bool(windows),
    )


def identify_dynamics_flags(dynamics_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """Dynamics flag detection is intentionally outside Phase 3L."""
    raise NotImplementedError("Dynamics flag detection is not implemented in Phase 3L.")
