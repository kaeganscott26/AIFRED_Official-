"""Tests for factual frequency-band metrics.

Tests use generated sample arrays only. No private audio, commercial audio,
old repo audio, or DAW project audio is required.
"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.frequency_metrics import (  # noqa: E402
    PREDEFINED_FREQUENCY_BANDS,
    FrequencyBand,
    calculate_band_energy,
    calculate_band_energy_ratio,
    calculate_dft_magnitudes,
    calculate_frequency_metrics,
    calculate_frequency_resolution,
    calculate_total_energy,
)


def _sine_samples(frequency_hz: float, sample_rate: int, sample_count: int) -> tuple[float, ...]:
    return tuple(math.sin(2.0 * math.pi * frequency_hz * index / sample_rate) for index in range(sample_count))


class FrequencyMetricsFoundationTests(unittest.TestCase):
    def test_frequency_resolution_calculation_works(self) -> None:
        self.assertEqual(calculate_frequency_resolution(sample_rate=1024, sample_count=64), 16.0)

    def test_invalid_sample_rate_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate_frequency_resolution(sample_rate=0, sample_count=64)
        with self.assertRaises(ValueError):
            calculate_dft_magnitudes((0.0,), sample_rate=0)

    def test_invalid_samples_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate_dft_magnitudes((0.0, float("nan")), sample_rate=1024)
        with self.assertRaises(ValueError):
            calculate_dft_magnitudes((0.0, float("inf")), sample_rate=1024)

    def test_empty_samples_handled_safely(self) -> None:
        metrics = calculate_frequency_metrics((), sample_rate=1024)
        self.assertEqual(metrics.sample_count, 0)
        self.assertIsNone(metrics.frequency_resolution_hz)
        self.assertEqual(metrics.total_energy, 0.0)

    def test_silence_total_energy_is_zero(self) -> None:
        magnitudes = calculate_dft_magnitudes((0.0, 0.0, 0.0, 0.0), sample_rate=1024)
        self.assertEqual(calculate_total_energy(magnitudes), 0.0)

    def test_silence_band_ratios_are_none(self) -> None:
        metrics = calculate_frequency_metrics((0.0,) * 16, sample_rate=1024)
        self.assertTrue(metrics.bands)
        self.assertTrue(all(result.energy_ratio is None for result in metrics.bands))

    def test_simple_sine_places_strongest_energy_near_expected_frequency(self) -> None:
        samples = _sine_samples(128.0, sample_rate=1024, sample_count=64)
        magnitudes = calculate_dft_magnitudes(samples, sample_rate=1024)
        strongest_frequency, _ = max(magnitudes, key=lambda item: item[1])
        self.assertAlmostEqual(strongest_frequency, 128.0)

    def test_band_energy_detects_energy_inside_target_band(self) -> None:
        samples = _sine_samples(128.0, sample_rate=1024, sample_count=64)
        magnitudes = calculate_dft_magnitudes(samples, sample_rate=1024)
        target_band = FrequencyBand("target", 120.0, 140.0)
        outside_band = FrequencyBand("outside", 300.0, 340.0)
        self.assertGreater(calculate_band_energy(magnitudes, target_band), 0.0)
        self.assertGreater(
            calculate_band_energy(magnitudes, target_band),
            calculate_band_energy(magnitudes, outside_band),
        )

    def test_band_energy_ratio_works_for_nonzero_total_energy(self) -> None:
        self.assertEqual(calculate_band_energy_ratio(2.0, 8.0), 0.25)

    def test_predefined_bands_exist_and_are_ordered(self) -> None:
        self.assertGreaterEqual(len(PREDEFINED_FREQUENCY_BANDS), 7)
        previous_high = 0.0
        for band in PREDEFINED_FREQUENCY_BANDS:
            self.assertGreaterEqual(band.low_hz, previous_high)
            self.assertGreater(band.high_hz, band.low_hz)
            previous_high = band.high_hz

    def test_no_fake_minus_999_values_appear(self) -> None:
        metrics = calculate_frequency_metrics(_sine_samples(128.0, 1024, 64), sample_rate=1024)
        values = [metrics.total_energy, metrics.frequency_resolution_hz]
        values.extend(result.energy for result in metrics.bands)
        values.extend(result.energy_ratio for result in metrics.bands if result.energy_ratio is not None)
        self.assertNotIn(-999, values)

    def test_no_advice_text_appears_in_metric_outputs(self) -> None:
        metrics = calculate_frequency_metrics(_sine_samples(128.0, 1024, 64), sample_rate=1024)
        text = repr(metrics).lower()
        forbidden = ("advice", "fix", "too much", "cut", "boost", "professional")
        for word in forbidden:
            self.assertNotIn(word, text)

    def test_no_subjective_tonal_labels_beyond_neutral_band_names(self) -> None:
        allowed_names = {"sub", "bass", "low_mid", "mid", "upper_mid", "presence", "air"}
        names = {band.name for band in PREDEFINED_FREQUENCY_BANDS}
        self.assertLessEqual(names, allowed_names)
        forbidden = {"mud", "muddy", "harsh", "harshness", "warmth", "bright", "thin", "professional"}
        self.assertTrue(names.isdisjoint(forbidden))


class FutureFrequencyMetricsTests(unittest.TestCase):
    @unittest.skip("Future phase only; tonal balance interpretation is not implemented yet.")
    def test_tonal_balance_interpretation(self) -> None:
        """Future test: tonal interpretation is separate from raw band facts."""
