"""Tests for factual stereo metrics.

The tests use direct synthetic sample arrays only. No private audio,
commercial audio, old repo audio, or DAW project audio is required.
"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.stereo_metrics import (  # noqa: E402
    calculate_balance_db,
    calculate_channel_peak,
    calculate_channel_rms,
    calculate_mid_side,
    calculate_side_to_mid_ratio,
    calculate_stereo_correlation,
    calculate_stereo_metrics,
    split_interleaved_stereo,
)


class StereoMetricsFoundationTests(unittest.TestCase):
    def test_mono_input_is_handled_safely(self) -> None:
        metrics = calculate_stereo_metrics((0.5, -0.5, 0.0), channels=1)
        self.assertTrue(metrics.is_mono)
        self.assertEqual(metrics.channels, 1)
        self.assertEqual(metrics.right_peak, None)
        self.assertEqual(metrics.correlation, None)
        self.assertFalse(metrics.mono_compatibility_risk)

    def test_stereo_interleaved_samples_split_correctly(self) -> None:
        left, right = split_interleaved_stereo((1.0, -1.0, 0.5, -0.5), channels=2)
        self.assertEqual(left, (1.0, 0.5))
        self.assertEqual(right, (-1.0, -0.5))

    def test_left_right_rms_works(self) -> None:
        left, right = split_interleaved_stereo((1.0, 0.5, -1.0, -0.5), channels=2)
        self.assertAlmostEqual(calculate_channel_rms(left), 1.0)
        self.assertAlmostEqual(calculate_channel_rms(right), 0.5)

    def test_left_right_peak_works(self) -> None:
        left, right = split_interleaved_stereo((0.25, -0.75, -0.5, 0.5), channels=2)
        self.assertEqual(calculate_channel_peak(left), 0.5)
        self.assertEqual(calculate_channel_peak(right), 0.75)

    def test_mid_side_conversion_works(self) -> None:
        mid, side = calculate_mid_side((1.0, 0.5), (-1.0, 0.5))
        self.assertEqual(mid, (0.0, 0.5))
        self.assertEqual(side, (1.0, 0.0))

    def test_identical_left_right_correlation_is_about_one(self) -> None:
        correlation = calculate_stereo_correlation((1.0, -0.5, 0.25), (1.0, -0.5, 0.25))
        self.assertAlmostEqual(correlation, 1.0)

    def test_inverted_left_right_correlation_is_about_minus_one(self) -> None:
        correlation = calculate_stereo_correlation((1.0, -0.5, 0.25), (-1.0, 0.5, -0.25))
        self.assertAlmostEqual(correlation, -1.0)

    def test_orthogonal_style_correlation_is_about_zero(self) -> None:
        correlation = calculate_stereo_correlation((1.0, 0.0), (0.0, 1.0))
        self.assertAlmostEqual(correlation, 0.0)

    def test_silence_correlation_returns_none(self) -> None:
        self.assertIsNone(calculate_stereo_correlation((0.0, 0.0), (0.0, 0.0)))

    def test_side_to_mid_ratio_works(self) -> None:
        self.assertEqual(calculate_side_to_mid_ratio(0.5, 0.25), 0.5)

    def test_balance_db_works(self) -> None:
        self.assertAlmostEqual(calculate_balance_db(1.0, 0.5), 20.0 * math.log10(2.0))

    def test_mono_compatibility_risk_triggers_for_negative_correlation(self) -> None:
        metrics = calculate_stereo_metrics((1.0, -1.0, -0.5, 0.5), channels=2)
        self.assertAlmostEqual(metrics.correlation, -1.0)
        self.assertTrue(metrics.mono_compatibility_risk)

    def test_empty_samples_do_not_crash(self) -> None:
        metrics = calculate_stereo_metrics((), channels=2)
        self.assertFalse(metrics.is_mono)
        self.assertEqual(metrics.left_peak, 0.0)
        self.assertEqual(metrics.right_peak, 0.0)
        self.assertEqual(metrics.left_rms, 0.0)
        self.assertEqual(metrics.right_rms, 0.0)
        self.assertIsNone(metrics.correlation)

    def test_no_fake_minus_999_values_appear(self) -> None:
        metrics = calculate_stereo_metrics((0.5, 0.5), channels=2)
        values = (
            metrics.left_peak,
            metrics.right_peak,
            metrics.left_rms,
            metrics.right_rms,
            metrics.mid_rms,
            metrics.side_rms,
            metrics.side_to_mid_ratio,
            metrics.correlation,
            metrics.balance_db,
        )
        self.assertNotIn(-999, values)

    def test_no_advice_text_appears_in_metric_outputs(self) -> None:
        metrics = calculate_stereo_metrics((1.0, -1.0), channels=2)
        text = repr(metrics).lower()
        self.assertNotIn("too wide", text)
        self.assertNotIn("fix", text)
        self.assertNotIn("advice", text)


class FutureStereoMetricsTests(unittest.TestCase):
    @unittest.skip("Future phase only; frequency-scoped stereo metrics are not implemented yet.")
    def test_low_end_mono_stability_when_frequency_scoped(self) -> None:
        """Future test: low-band stereo behavior requires frequency analysis."""
