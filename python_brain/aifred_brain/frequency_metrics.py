"""Factual frequency-band energy metrics.

Responsibility:
    Calculate simple frequency-bin magnitudes and neutral band-energy facts
    from normalized sample arrays.

This module is correctness-first foundation code. It must not generate tonal
interpretation, EQ advice, subjective mix labels, reference comparisons, or AI
interpretation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class FrequencyBand:
    """Neutral numeric frequency band definition."""

    name: str
    low_hz: float
    high_hz: float


@dataclass(frozen=True)
class BandEnergy:
    """Factual energy for one frequency band."""

    band: FrequencyBand
    energy: float
    energy_ratio: float | None


@dataclass(frozen=True)
class FrequencyMetrics:
    """Factual frequency metrics without interpretation."""

    sample_rate: int
    sample_count: int
    frequency_resolution_hz: float | None
    total_energy: float
    bands: tuple[BandEnergy, ...]


PREDEFINED_FREQUENCY_BANDS: tuple[FrequencyBand, ...] = (
    FrequencyBand("sub", 20.0, 60.0),
    FrequencyBand("bass", 60.0, 120.0),
    FrequencyBand("low_mid", 120.0, 400.0),
    FrequencyBand("mid", 400.0, 2000.0),
    FrequencyBand("upper_mid", 2000.0, 5000.0),
    FrequencyBand("presence", 5000.0, 8000.0),
    FrequencyBand("air", 8000.0, 20000.0),
)


def _validate_sample_rate(sample_rate: int) -> None:
    if sample_rate <= 0:
        raise ValueError("sample_rate must be greater than zero.")


def _validate_samples(samples: Sequence[float]) -> None:
    for sample in samples:
        if not isinstance(sample, (int, float)):
            raise ValueError("samples must contain numeric values only.")
        if math.isnan(float(sample)) or math.isinf(float(sample)):
            raise ValueError("samples must contain finite values only.")


def calculate_frequency_resolution(sample_rate: int, sample_count: int) -> float | None:
    """Calculate frequency-bin spacing in Hz."""
    _validate_sample_rate(sample_rate)
    if sample_count <= 0:
        return None
    return sample_rate / sample_count


def calculate_dft_magnitudes(samples: Sequence[float], sample_rate: int) -> tuple[tuple[float, float], ...]:
    """Calculate one-sided DFT magnitudes for small sample arrays.

    This standard-library DFT is intentionally simple and not realtime
    optimized. It returns `(frequency_hz, magnitude)` pairs through Nyquist.
    """
    _validate_sample_rate(sample_rate)
    _validate_samples(samples)
    sample_count = len(samples)
    if sample_count == 0:
        return ()

    magnitudes: list[tuple[float, float]] = []
    max_bin = sample_count // 2
    for bin_index in range(max_bin + 1):
        real = 0.0
        imag = 0.0
        for sample_index, sample in enumerate(samples):
            angle = -2.0 * math.pi * bin_index * sample_index / sample_count
            value = float(sample)
            real += value * math.cos(angle)
            imag += value * math.sin(angle)
        frequency_hz = bin_index * sample_rate / sample_count
        magnitude = math.sqrt(real * real + imag * imag)
        magnitudes.append((frequency_hz, magnitude))
    return tuple(magnitudes)


def calculate_band_energy(magnitudes: Sequence[tuple[float, float]], band: FrequencyBand) -> float:
    """Calculate squared-magnitude energy inside a frequency band."""
    energy = 0.0
    for frequency_hz, magnitude in magnitudes:
        if not isinstance(frequency_hz, (int, float)) or not isinstance(magnitude, (int, float)):
            raise ValueError("magnitudes must contain numeric frequency and magnitude values.")
        if math.isnan(float(frequency_hz)) or math.isinf(float(frequency_hz)):
            raise ValueError("frequency values must be finite.")
        if math.isnan(float(magnitude)) or math.isinf(float(magnitude)):
            raise ValueError("magnitude values must be finite.")
        if band.low_hz <= float(frequency_hz) < band.high_hz:
            energy += float(magnitude) * float(magnitude)
    return energy


def calculate_total_energy(magnitudes: Sequence[tuple[float, float]]) -> float:
    """Calculate total squared-magnitude energy across all bins."""
    total = 0.0
    for frequency_hz, magnitude in magnitudes:
        if not isinstance(frequency_hz, (int, float)) or not isinstance(magnitude, (int, float)):
            raise ValueError("magnitudes must contain numeric frequency and magnitude values.")
        if math.isnan(float(magnitude)) or math.isinf(float(magnitude)):
            raise ValueError("magnitude values must be finite.")
        total += float(magnitude) * float(magnitude)
    return total


def calculate_band_energy_ratio(band_energy: float, total_energy: float) -> float | None:
    """Calculate a band-energy ratio when total energy is available."""
    if not isinstance(band_energy, (int, float)) or not isinstance(total_energy, (int, float)):
        raise ValueError("energy values must be numeric.")
    if math.isnan(float(band_energy)) or math.isinf(float(band_energy)):
        raise ValueError("band_energy must be finite.")
    if math.isnan(float(total_energy)) or math.isinf(float(total_energy)):
        raise ValueError("total_energy must be finite.")
    if total_energy <= 0.0:
        return None
    return float(band_energy) / float(total_energy)


def calculate_frequency_metrics(
    samples: Sequence[float],
    sample_rate: int,
    bands: Sequence[FrequencyBand] | None = None,
) -> FrequencyMetrics:
    """Calculate factual frequency-band metrics from normalized samples."""
    selected_bands = tuple(bands) if bands is not None else PREDEFINED_FREQUENCY_BANDS
    magnitudes = calculate_dft_magnitudes(samples, sample_rate)
    total_energy = calculate_total_energy(magnitudes)
    band_results = tuple(
        BandEnergy(
            band=band,
            energy=calculate_band_energy(magnitudes, band),
            energy_ratio=calculate_band_energy_ratio(calculate_band_energy(magnitudes, band), total_energy),
        )
        for band in selected_bands
    )
    return FrequencyMetrics(
        sample_rate=sample_rate,
        sample_count=len(samples),
        frequency_resolution_hz=calculate_frequency_resolution(sample_rate, len(samples)),
        total_energy=total_energy,
        bands=band_results,
    )


def identify_band_flags(frequency_metrics: FrequencyMetrics) -> list[dict[str, float | str]]:
    """Future factual flag extraction placeholder.

    Band flags require separate approval to avoid turning raw facts into
    subjective interpretation too early.
    """
    _ = frequency_metrics
    raise NotImplementedError("Frequency flag detection is not implemented yet.")
