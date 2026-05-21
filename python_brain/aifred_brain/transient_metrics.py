"""Transient metrics for factual amplitude-change evidence.

Responsibility:
    Calculate absolute envelope values, smoothed level changes, transient
    events, event density, and event strength facts from normalized PCM samples.

This module must not generate processing advice, subjective labels, reference
comparison, report text, or fake metric values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

from .validation import InvalidAudioBufferError


@dataclass(frozen=True)
class TransientEvent:
    """Factual transient event derived from a positive amplitude change."""

    sample_index: int
    time_seconds: float
    previous_level: float
    current_level: float
    delta: float
    strength: float


@dataclass(frozen=True)
class TransientMetrics:
    """Factual transient summary with unavailable strength values as `None`."""

    sample_rate: int
    sample_count: int
    duration_seconds: float
    event_count: int
    events_per_second: float | None
    average_strength: float | None
    max_strength: float | None
    available: bool


def _validate_samples(samples: Sequence[float]) -> None:
    for sample in samples:
        if not isinstance(sample, (int, float)):
            raise InvalidAudioBufferError("Audio samples must be numeric.")
        if math.isnan(float(sample)) or math.isinf(float(sample)):
            raise InvalidAudioBufferError("Audio samples must be finite.")


def _validate_sample_rate(sample_rate: int) -> None:
    if not isinstance(sample_rate, int) or sample_rate <= 0:
        raise InvalidAudioBufferError("Sample rate must be a positive integer.")


def _validate_threshold(threshold: float) -> None:
    if not isinstance(threshold, (int, float)):
        raise InvalidAudioBufferError("Transient threshold must be numeric.")
    threshold_value = float(threshold)
    if math.isnan(threshold_value) or math.isinf(threshold_value) or threshold_value < 0:
        raise InvalidAudioBufferError("Transient threshold must be a non-negative finite value.")


def _validate_smoothing_window(smoothing_window: int) -> None:
    if not isinstance(smoothing_window, int) or smoothing_window <= 0:
        raise InvalidAudioBufferError("Smoothing window must be a positive integer.")


def calculate_absolute_envelope(samples: Sequence[float]) -> tuple[float, ...]:
    """Return absolute sample levels from normalized samples."""
    _validate_samples(samples)
    return tuple(abs(float(sample)) for sample in samples)


def moving_average(values: Sequence[float], window_size: int) -> tuple[float, ...]:
    """Return trailing moving-average values with output length preserved."""
    _validate_smoothing_window(window_size)
    cleaned: list[float] = []
    for value in values:
        if not isinstance(value, (int, float)):
            raise InvalidAudioBufferError("Moving-average values must be numeric.")
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            raise InvalidAudioBufferError("Moving-average values must be finite.")
        cleaned.append(numeric)

    averaged: list[float] = []
    for index in range(len(cleaned)):
        start = max(0, index - window_size + 1)
        window = cleaned[start : index + 1]
        averaged.append(sum(window) / len(window))
    return tuple(averaged)


def calculate_level_deltas(values: Sequence[float]) -> tuple[float, ...]:
    """Return level changes between adjacent values with a zero first delta."""
    cleaned: list[float] = []
    for value in values:
        if not isinstance(value, (int, float)):
            raise InvalidAudioBufferError("Level values must be numeric.")
        numeric = float(value)
        if math.isnan(numeric) or math.isinf(numeric):
            raise InvalidAudioBufferError("Level values must be finite.")
        cleaned.append(numeric)

    if not cleaned:
        return ()

    deltas = [0.0]
    for index in range(1, len(cleaned)):
        deltas.append(cleaned[index] - cleaned[index - 1])
    return tuple(deltas)


def detect_transient_events(
    samples: Sequence[float],
    sample_rate: int,
    threshold: float = 0.25,
    smoothing_window: int = 1,
) -> tuple[TransientEvent, ...]:
    """Detect factual positive amplitude-change events above a threshold."""
    _validate_sample_rate(sample_rate)
    _validate_threshold(threshold)
    _validate_smoothing_window(smoothing_window)
    envelope = calculate_absolute_envelope(samples)
    if not envelope:
        return ()

    smoothed = moving_average(envelope, smoothing_window)
    deltas = calculate_level_deltas(smoothed)
    events: list[TransientEvent] = []
    for index, delta in enumerate(deltas):
        if delta >= float(threshold) and delta > 0:
            events.append(
                TransientEvent(
                    sample_index=index,
                    time_seconds=index / sample_rate,
                    previous_level=smoothed[index - 1] if index > 0 else 0.0,
                    current_level=smoothed[index],
                    delta=delta,
                    strength=delta,
                )
            )
    return tuple(events)


def _average(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def calculate_transient_metrics(
    samples: Sequence[float],
    sample_rate: int,
    threshold: float = 0.25,
    smoothing_window: int = 1,
) -> TransientMetrics:
    """Calculate factual transient metrics from normalized samples."""
    _validate_sample_rate(sample_rate)
    _validate_threshold(threshold)
    _validate_smoothing_window(smoothing_window)
    _validate_samples(samples)

    sample_count = len(samples)
    duration_seconds = sample_count / sample_rate
    events = detect_transient_events(samples, sample_rate, threshold, smoothing_window)
    strengths = tuple(event.strength for event in events)

    return TransientMetrics(
        sample_rate=sample_rate,
        sample_count=sample_count,
        duration_seconds=duration_seconds,
        event_count=len(events),
        events_per_second=None if duration_seconds == 0 else len(events) / duration_seconds,
        average_strength=_average(strengths),
        max_strength=None if not strengths else max(strengths),
        available=sample_count > 0,
    )


def identify_transient_flags(transient_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """Transient flag detection is intentionally outside Phase 3M."""
    raise NotImplementedError("Transient flag detection is not implemented in Phase 3M.")
