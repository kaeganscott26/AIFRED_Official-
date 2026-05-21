"""Tests for factual tonal-balance summary metrics.

Tests use synthetic `FrequencyMetrics` objects and dictionaries only.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.frequency_metrics import BandEnergy, FrequencyBand, FrequencyMetrics  # noqa: E402
from aifred_brain.tonal_balance import (  # noqa: E402
    HIGH_GROUP_BANDS,
    LOW_GROUP_BANDS,
    MID_GROUP_BANDS,
    calculate_group_energy_ratio,
    calculate_ratio,
    calculate_spectral_centroid,
    calculate_tilt_value,
    calculate_tonal_balance_metrics,
    extract_band_ratios,
)


def _band_energy(name: str, ratio: float | None) -> BandEnergy:
    return BandEnergy(FrequencyBand(name, 0.0, 1.0), energy=0.0, energy_ratio=ratio)


def _frequency_metrics() -> FrequencyMetrics:
    return FrequencyMetrics(
        sample_rate=48000,
        sample_count=128,
        frequency_resolution_hz=375.0,
        total_energy=1.0,
        bands=(
            _band_energy("sub", 0.05),
            _band_energy("bass", 0.10),
            _band_energy("low_mid", 0.20),
            _band_energy("mid", 0.25),
            _band_energy("upper_mid", 0.15),
            _band_energy("presence", 0.15),
            _band_energy("air", 0.10),
        ),
    )


class TonalBalanceFoundationTests(unittest.TestCase):
    def test_extracts_band_ratios_by_band_name(self) -> None:
        ratios = extract_band_ratios(_frequency_metrics())
        self.assertEqual(ratios["sub"], 0.05)
        self.assertEqual(ratios["mid"], 0.25)
        self.assertEqual(ratios["air"], 0.10)

    def test_extracts_band_ratios_from_direct_dictionary(self) -> None:
        ratios = extract_band_ratios({"bands": {"sub": 0.1, "mid": None}})
        self.assertEqual(ratios, {"sub": 0.1, "mid": None})

    def test_calculates_low_group_ratio(self) -> None:
        ratios = extract_band_ratios(_frequency_metrics())
        self.assertAlmostEqual(calculate_group_energy_ratio(ratios, LOW_GROUP_BANDS), 0.15)

    def test_calculates_mid_group_ratio(self) -> None:
        ratios = extract_band_ratios(_frequency_metrics())
        self.assertAlmostEqual(calculate_group_energy_ratio(ratios, MID_GROUP_BANDS), 0.45)

    def test_calculates_high_group_ratio(self) -> None:
        ratios = extract_band_ratios(_frequency_metrics())
        self.assertAlmostEqual(calculate_group_energy_ratio(ratios, HIGH_GROUP_BANDS), 0.40)

    def test_calculates_low_to_mid_ratio(self) -> None:
        self.assertAlmostEqual(calculate_ratio(0.15, 0.45), 1.0 / 3.0)

    def test_calculates_high_to_mid_ratio(self) -> None:
        self.assertAlmostEqual(calculate_ratio(0.40, 0.45), 0.40 / 0.45)

    def test_handles_denominator_zero_by_returning_none(self) -> None:
        self.assertIsNone(calculate_ratio(0.25, 0.0))

    def test_handles_unavailable_band_ratios_safely(self) -> None:
        ratios = {"sub": None, "bass": None}
        self.assertIsNone(calculate_group_energy_ratio(ratios, LOW_GROUP_BANDS))
        self.assertIsNone(calculate_ratio(None, 0.5))

    def test_spectral_centroid_works_on_known_simple_magnitudes(self) -> None:
        centroid = calculate_spectral_centroid(((100.0, 1.0), (300.0, 3.0)))
        self.assertEqual(centroid, 250.0)

    def test_spectral_centroid_returns_none_for_zero_total_magnitude(self) -> None:
        self.assertIsNone(calculate_spectral_centroid(((100.0, 0.0), (300.0, 0.0))))

    def test_tilt_value_is_high_minus_low(self) -> None:
        self.assertAlmostEqual(calculate_tilt_value(0.15, 0.40), 0.25)

    def test_full_tonal_balance_dataclass_returns_factual_fields(self) -> None:
        metrics = calculate_tonal_balance_metrics(
            _frequency_metrics(),
            magnitudes=((100.0, 1.0), (300.0, 3.0)),
        )
        self.assertAlmostEqual(metrics.low_energy_ratio, 0.15)
        self.assertAlmostEqual(metrics.mid_energy_ratio, 0.45)
        self.assertAlmostEqual(metrics.high_energy_ratio, 0.40)
        self.assertAlmostEqual(metrics.low_to_mid_ratio, 1.0 / 3.0)
        self.assertAlmostEqual(metrics.high_to_mid_ratio, 0.40 / 0.45)
        self.assertEqual(metrics.spectral_centroid_hz, 250.0)
        self.assertAlmostEqual(metrics.tilt_value, 0.25)
        self.assertTrue(metrics.available)

    def test_no_fake_minus_999_values_appear(self) -> None:
        metrics = calculate_tonal_balance_metrics(_frequency_metrics())
        values = (
            metrics.low_energy_ratio,
            metrics.mid_energy_ratio,
            metrics.high_energy_ratio,
            metrics.low_to_mid_ratio,
            metrics.high_to_mid_ratio,
            metrics.spectral_centroid_hz,
            metrics.tilt_value,
        )
        self.assertNotIn(-999, values)

    def test_no_advice_text_appears_in_metric_output(self) -> None:
        text = repr(calculate_tonal_balance_metrics(_frequency_metrics())).lower()
        for word in ("advice", "fix", "cut", "boost", "eq"):
            self.assertNotIn(word, text)

    def test_no_subjective_labels_appear_in_metric_output(self) -> None:
        text = repr(calculate_tonal_balance_metrics(_frequency_metrics())).lower()
        forbidden = ("muddy", "harsh", "warm", "thin", "bright", "dark", "pro", "professional")
        for word in forbidden:
            self.assertNotIn(word, text)


class FutureTonalBalanceTests(unittest.TestCase):
    @unittest.skip("Future phase only; tonal flags are not implemented yet.")
    def test_tonal_flags_are_separate_from_factual_summary(self) -> None:
        """Future test: tonal flags need separate approval from factual summaries."""
