"""Tests for factual dynamics metrics.

Tests use direct synthetic sample arrays only.
"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.dynamics_metrics import (  # noqa: E402
    build_dynamics_windows,
    calculate_db_range,
    calculate_dynamic_range_db,
    calculate_dynamics_metrics,
    calculate_percentile,
)
from aifred_brain.validation import InvalidAudioBufferError  # noqa: E402


class DynamicsMetricsFoundationTests(unittest.TestCase):
    def test_empty_samples_do_not_crash(self) -> None:
        metrics = calculate_dynamics_metrics((), sample_rate=10, window_seconds=0.5)
        self.assertFalse(metrics.available)
        self.assertEqual(metrics.window_count, 0)
        self.assertIsNone(metrics.rms_min)
        self.assertIsNone(metrics.dynamic_range_db)

    def test_invalid_sample_rate_rejected(self) -> None:
        with self.assertRaises(InvalidAudioBufferError):
            calculate_dynamics_metrics((0.1, 0.2), sample_rate=0)

    def test_invalid_window_duration_rejected(self) -> None:
        with self.assertRaises(InvalidAudioBufferError):
            calculate_dynamics_metrics((0.1, 0.2), sample_rate=10, window_seconds=0.0)

    def test_invalid_samples_rejected(self) -> None:
        for sample in (math.inf, math.nan, "0.5"):
            with self.subTest(sample=sample):
                with self.assertRaises(InvalidAudioBufferError):
                    calculate_dynamics_metrics((0.1, sample), sample_rate=10)

    def test_dynamics_windows_are_built_with_expected_sample_counts(self) -> None:
        windows = build_dynamics_windows((0.1, 0.2, 0.3, 0.4), sample_rate=10, window_seconds=0.2)
        self.assertEqual(len(windows), 2)
        self.assertEqual(tuple(window.sample_count for window in windows), (2, 2))
        self.assertEqual(tuple(window.start_sample for window in windows), (0, 2))

    def test_incomplete_windows_excluded_by_default(self) -> None:
        windows = build_dynamics_windows((0.1, 0.2, 0.3, 0.4, 0.5), sample_rate=10, window_seconds=0.2)
        self.assertEqual(len(windows), 2)
        self.assertEqual(tuple(window.sample_count for window in windows), (2, 2))

    def test_incomplete_windows_included_when_requested(self) -> None:
        windows = build_dynamics_windows(
            (0.1, 0.2, 0.3, 0.4, 0.5),
            sample_rate=10,
            window_seconds=0.2,
            include_incomplete=True,
        )
        self.assertEqual(len(windows), 3)
        self.assertEqual(tuple(window.sample_count for window in windows), (2, 2, 1))

    def test_per_window_rms_works_on_known_values(self) -> None:
        windows = build_dynamics_windows((1.0, -1.0, 0.0, 1.0), sample_rate=10, window_seconds=0.2)
        self.assertAlmostEqual(windows[0].rms, 1.0)
        self.assertAlmostEqual(windows[1].rms, math.sqrt(0.5))

    def test_per_window_peak_works_on_known_values(self) -> None:
        windows = build_dynamics_windows((0.25, -0.5, 0.1, -1.0), sample_rate=10, window_seconds=0.2)
        self.assertEqual(windows[0].peak, 0.5)
        self.assertEqual(windows[1].peak, 1.0)

    def test_silence_produces_none_db_ranges_where_appropriate(self) -> None:
        metrics = calculate_dynamics_metrics((0.0, 0.0, 0.0, 0.0), sample_rate=10, window_seconds=0.2)
        self.assertTrue(metrics.available)
        self.assertEqual(metrics.rms_min, 0.0)
        self.assertEqual(metrics.peak_max, 0.0)
        self.assertIsNone(metrics.rms_range_db)
        self.assertIsNone(metrics.peak_range_db)
        self.assertIsNone(metrics.crest_factor_range_db)
        self.assertIsNone(metrics.dynamic_range_db)

    def test_db_range_works_for_known_linear_values(self) -> None:
        self.assertAlmostEqual(calculate_db_range(0.25, 1.0), 12.041199826, places=6)
        self.assertEqual(calculate_db_range(0.5, 0.5), 0.0)
        self.assertIsNone(calculate_db_range(0.0, 1.0))

    def test_percentile_helper_works(self) -> None:
        self.assertIsNone(calculate_percentile((), 50.0))
        self.assertEqual(calculate_percentile((1.0,), 50.0), 1.0)
        self.assertEqual(calculate_percentile((0.0, 10.0), 50.0), 5.0)
        self.assertEqual(calculate_percentile((4.0, 1.0, 2.0, 3.0), 25.0), 1.75)

    def test_dynamic_range_works_from_known_rms_windows(self) -> None:
        self.assertAlmostEqual(calculate_dynamic_range_db((0.25, 0.25, 1.0, 1.0)), 12.041199826, places=6)
        self.assertEqual(calculate_dynamic_range_db((0.5, 0.5)), 0.0)
        self.assertIsNone(calculate_dynamic_range_db((0.0, 0.0)))

    def test_full_dynamics_dataclass_returns_factual_fields(self) -> None:
        samples = (0.25, -0.25, 0.25, -0.25, 1.0, -1.0, 1.0, -1.0)
        metrics = calculate_dynamics_metrics(samples, sample_rate=10, window_seconds=0.2)
        self.assertTrue(metrics.available)
        self.assertEqual(metrics.window_count, 4)
        self.assertEqual(metrics.window_seconds, 0.2)
        self.assertAlmostEqual(metrics.rms_min or 0.0, 0.25)
        self.assertAlmostEqual(metrics.rms_max or 0.0, 1.0)
        self.assertAlmostEqual(metrics.rms_range_db or 0.0, 12.041199826, places=6)
        self.assertEqual(metrics.peak_min, 0.25)
        self.assertEqual(metrics.peak_max, 1.0)
        self.assertAlmostEqual(metrics.peak_range_db or 0.0, 12.041199826, places=6)
        self.assertAlmostEqual(metrics.crest_factor_min_db or 0.0, 0.0)
        self.assertAlmostEqual(metrics.crest_factor_max_db or 0.0, 0.0)
        self.assertAlmostEqual(metrics.crest_factor_range_db or 0.0, 0.0)
        self.assertAlmostEqual(metrics.dynamic_range_db or 0.0, 12.041199826, places=6)

    def test_no_fake_minus_999_values_appear(self) -> None:
        metrics = calculate_dynamics_metrics((0.0, 0.0), sample_rate=10, window_seconds=0.2)
        values = (
            metrics.rms_min,
            metrics.rms_max,
            metrics.rms_range_db,
            metrics.peak_min,
            metrics.peak_max,
            metrics.peak_range_db,
            metrics.crest_factor_min_db,
            metrics.crest_factor_max_db,
            metrics.crest_factor_range_db,
            metrics.dynamic_range_db,
        )
        self.assertNotIn(-999, values)

    def test_no_advice_text_appears(self) -> None:
        text = repr(calculate_dynamics_metrics((0.25, -0.25), sample_rate=10, window_seconds=0.2)).lower()
        for word in ("advice", "compressor", "limiter", "setting", "fix", "recommend"):
            self.assertNotIn(word, text)

    def test_no_subjective_labels_appear(self) -> None:
        text = repr(calculate_dynamics_metrics((0.25, -0.25), sample_rate=10, window_seconds=0.2)).lower()
        forbidden = ("overcompressed", "smashed", "punchy", "flat", "lifeless")
        for word in forbidden:
            self.assertNotIn(word, text)


class FutureDynamicsTests(unittest.TestCase):
    @unittest.skip("Future phase only; transient detection is not implemented yet.")
    def test_transient_detection_is_separate_from_windowed_dynamics(self) -> None:
        """Future test: transient detection needs separate approval."""

    @unittest.skip("Future phase only; dynamics flags are not implemented yet.")
    def test_dynamics_flags_are_separate_from_factual_metrics(self) -> None:
        """Future test: factual flags need separate approval from metrics."""
