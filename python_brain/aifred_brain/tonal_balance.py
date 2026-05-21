"""Factual tonal-balance summary metrics.

Responsibility:
    Summarize neutral grouped frequency-band ratios and numerical relationships
    from verified frequency metrics.

This module must not generate EQ advice, subjective mix labels, reference
comparisons, report text, or AI interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .frequency_metrics import BandEnergy, FrequencyMetrics


LOW_GROUP_BANDS = ("sub", "bass")
MID_GROUP_BANDS = ("low_mid", "mid")
HIGH_GROUP_BANDS = ("upper_mid", "presence", "air")


@dataclass(frozen=True)
class TonalBalanceMetrics:
    """Factual grouped frequency-ratio summary."""

    low_energy_ratio: float | None
    mid_energy_ratio: float | None
    high_energy_ratio: float | None
    low_to_mid_ratio: float | None
    high_to_mid_ratio: float | None
    spectral_centroid_hz: float | None
    tilt_value: float | None
    available: bool


def extract_band_ratios(frequency_metrics: FrequencyMetrics | Mapping[str, Any]) -> dict[str, float | None]:
    """Extract band energy ratios by band name from supported metric shapes."""
    if isinstance(frequency_metrics, FrequencyMetrics):
        return {result.band.name: result.energy_ratio for result in frequency_metrics.bands}

    raw_bands = frequency_metrics.get("bands", ())
    ratios: dict[str, float | None] = {}
    if isinstance(raw_bands, Mapping):
        for name, value in raw_bands.items():
            ratios[str(name)] = None if value is None else float(value)
        return ratios

    for item in raw_bands:
        if isinstance(item, BandEnergy):
            ratios[item.band.name] = item.energy_ratio
        elif isinstance(item, Mapping):
            name = item.get("name")
            if name is None and isinstance(item.get("band"), Mapping):
                name = item["band"].get("name")
            if name is not None:
                value = item.get("energy_ratio")
                ratios[str(name)] = None if value is None else float(value)
    return ratios


def calculate_group_energy_ratio(
    band_ratios: Mapping[str, float | None],
    band_names: Sequence[str],
) -> float | None:
    """Sum available ratios for a neutral band group.

    Returns None when every requested band is unavailable.
    """
    available_values = [band_ratios[name] for name in band_names if band_ratios.get(name) is not None]
    if not available_values:
        return None
    return sum(float(value) for value in available_values)


def calculate_ratio(numerator: float | None, denominator: float | None) -> float | None:
    """Calculate a numeric ratio while preserving unavailable states."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0.0:
        return None
    return numerator / denominator


def calculate_spectral_centroid(magnitudes: Sequence[tuple[float, float]]) -> float | None:
    """Calculate spectral centroid in Hz from `(frequency_hz, magnitude)` pairs."""
    weighted_sum = 0.0
    total_magnitude = 0.0
    for frequency_hz, magnitude in magnitudes:
        frequency = float(frequency_hz)
        value = float(magnitude)
        if value < 0.0:
            raise ValueError("magnitudes must be non-negative.")
        weighted_sum += frequency * value
        total_magnitude += value
    if total_magnitude == 0.0:
        return None
    return weighted_sum / total_magnitude


def calculate_tilt_value(low_ratio: float | None, high_ratio: float | None) -> float | None:
    """Calculate neutral numerical tilt as high ratio minus low ratio."""
    if low_ratio is None or high_ratio is None:
        return None
    return high_ratio - low_ratio


def calculate_tonal_balance_metrics(
    frequency_metrics: FrequencyMetrics | Mapping[str, Any],
    magnitudes: Sequence[tuple[float, float]] | None = None,
) -> TonalBalanceMetrics:
    """Calculate factual tonal-balance summary metrics from band ratios."""
    band_ratios = extract_band_ratios(frequency_metrics)
    low_ratio = calculate_group_energy_ratio(band_ratios, LOW_GROUP_BANDS)
    mid_ratio = calculate_group_energy_ratio(band_ratios, MID_GROUP_BANDS)
    high_ratio = calculate_group_energy_ratio(band_ratios, HIGH_GROUP_BANDS)
    centroid = calculate_spectral_centroid(magnitudes or ())
    available = any(value is not None for value in (low_ratio, mid_ratio, high_ratio, centroid))

    return TonalBalanceMetrics(
        low_energy_ratio=low_ratio,
        mid_energy_ratio=mid_ratio,
        high_energy_ratio=high_ratio,
        low_to_mid_ratio=calculate_ratio(low_ratio, mid_ratio),
        high_to_mid_ratio=calculate_ratio(high_ratio, mid_ratio),
        spectral_centroid_hz=centroid,
        tilt_value=calculate_tilt_value(low_ratio, high_ratio),
        available=available,
    )


def calculate_tonal_balance(
    frequency_metrics: FrequencyMetrics | Mapping[str, Any],
    *,
    magnitudes: Sequence[tuple[float, float]] | None = None,
) -> TonalBalanceMetrics:
    """Compatibility wrapper for factual tonal-balance metrics."""
    return calculate_tonal_balance_metrics(frequency_metrics, magnitudes=magnitudes)
