"""Tests for factual transient metrics.

Tests use direct synthetic sample arrays only.
"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.transient_metrics import (  # noqa: E402
    calculate_absolute_envelope,
    calculate_level_deltas,
    calculate_transient_metrics,
    detect_transient_events,
    moving_average,
)
from aifred_brain.validation import InvalidAudioBufferError  # noqa: E402


class TransientMetricsFoundationTests(unittest.TestCase):
    def test_empty_samples_do_not_crash(self) -> None:
        metrics = calculate_transient_metrics((), sample_rate=10)
        self.assertFalse(metrics.available)
        self.assertEqual(metrics.sample_count, 0)
        self.assertEqual(metrics.event_count, 0)
        self.assertIsNone(metrics.events_per_second)
        self.assertIsNone(metrics.average_strength)
        self.assertIsNone(metrics.max_strength)

    def test_invalid_sample_rate_rejected(self) -> None:
        with self.assertRaises(InvalidAudioBufferError):
            calculate_transient_metrics((0.0, 1.0), sample_rate=0)

    def test_invalid_threshold_rejected(self) -> None:
        for threshold in (-0.1, math.inf, math.nan, "0.1"):
            with self.subTest(threshold=threshold):
                with self.assertRaises(InvalidAudioBufferError):
                    calculate_transient_metrics((0.0, 1.0), sample_rate=10, threshold=threshold)

    def test_invalid_smoothing_window_rejected(self) -> None:
        for smoothing_window in (0, -1, 1.5, "1"):
            with self.subTest(smoothing_window=smoothing_window):
                with self.assertRaises(InvalidAudioBufferError):
                    calculate_transient_metrics((0.0, 1.0), sample_rate=10, smoothing_window=smoothing_window)

    def test_invalid_samples_rejected(self) -> None:
        for sample in (math.inf, math.nan, "0.5"):
            with self.subTest(sample=sample):
                with self.assertRaises(InvalidAudioBufferError):
                    calculate_transient_metrics((0.0, sample), sample_rate=10)

    def test_absolute_envelope_works(self) -> None:
        self.assertEqual(calculate_absolute_envelope((-0.5, 0.25, 0.0, 1.0)), (0.5, 0.25, 0.0, 1.0))

    def test_moving_average_works_on_known_values(self) -> None:
        self.assertEqual(moving_average((1.0, 3.0, 5.0, 7.0), 2), (1.0, 2.0, 4.0, 6.0))
        self.assertEqual(moving_average((1.0, 3.0, 5.0), 3), (1.0, 2.0, 3.0))

    def test_level_deltas_work_on_known_values(self) -> None:
        self.assertEqual(calculate_level_deltas((0.0, 0.25, 1.0, 0.5)), (0.0, 0.25, 0.75, -0.5))

    def test_silence_produces_zero_transient_events(self) -> None:
        events = detect_transient_events((0.0, 0.0, 0.0, 0.0), sample_rate=10)
        metrics = calculate_transient_metrics((0.0, 0.0, 0.0, 0.0), sample_rate=10)
        self.assertEqual(events, ())
        self.assertEqual(metrics.event_count, 0)
        self.assertEqual(metrics.events_per_second, 0.0)
        self.assertIsNone(metrics.average_strength)
        self.assertIsNone(metrics.max_strength)

    def test_simple_impulse_produces_at_least_one_event(self) -> None:
        events = detect_transient_events((0.0, 0.0, 1.0, 0.0), sample_rate=10, threshold=0.5)
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0].sample_index, 2)
        self.assertEqual(events[0].previous_level, 0.0)
        self.assertEqual(events[0].current_level, 1.0)
        self.assertEqual(events[0].delta, 1.0)
        self.assertEqual(events[0].strength, 1.0)

    def test_event_time_is_calculated_from_sample_index_and_sample_rate(self) -> None:
        event = detect_transient_events((0.0, 0.0, 1.0, 0.0), sample_rate=10, threshold=0.5)[0]
        self.assertEqual(event.sample_index, 2)
        self.assertEqual(event.time_seconds, 0.2)

    def test_transient_density_works_from_known_event_count_and_duration(self) -> None:
        metrics = calculate_transient_metrics((0.0, 1.0, 0.0, 1.0), sample_rate=4, threshold=0.5)
        self.assertEqual(metrics.duration_seconds, 1.0)
        self.assertEqual(metrics.event_count, 2)
        self.assertEqual(metrics.events_per_second, 2.0)

    def test_average_strength_works(self) -> None:
        metrics = calculate_transient_metrics((0.0, 0.5, 0.0, 1.0), sample_rate=4, threshold=0.25)
        self.assertEqual(metrics.average_strength, 0.75)

    def test_max_strength_works(self) -> None:
        metrics = calculate_transient_metrics((0.0, 0.5, 0.0, 1.0), sample_rate=4, threshold=0.25)
        self.assertEqual(metrics.max_strength, 1.0)

    def test_full_transient_dataclass_returns_factual_fields(self) -> None:
        metrics = calculate_transient_metrics((0.0, 0.5, 0.0, 1.0), sample_rate=4, threshold=0.25)
        self.assertEqual(metrics.sample_rate, 4)
        self.assertEqual(metrics.sample_count, 4)
        self.assertEqual(metrics.duration_seconds, 1.0)
        self.assertEqual(metrics.event_count, 2)
        self.assertEqual(metrics.events_per_second, 2.0)
        self.assertEqual(metrics.average_strength, 0.75)
        self.assertEqual(metrics.max_strength, 1.0)
        self.assertTrue(metrics.available)

    def test_no_fake_minus_999_values_appear(self) -> None:
        metrics = calculate_transient_metrics((0.0, 0.0), sample_rate=10)
        values = (
            metrics.duration_seconds,
            metrics.event_count,
            metrics.events_per_second,
            metrics.average_strength,
            metrics.max_strength,
        )
        self.assertNotIn(-999, values)

    def test_no_advice_text_appears(self) -> None:
        text = repr(calculate_transient_metrics((0.0, 1.0), sample_rate=10)).lower()
        for word in ("advice", "compressor", "limiter", "setting", "fix", "recommend"):
            self.assertNotIn(word, text)

    def test_no_subjective_labels_appear(self) -> None:
        text = repr(calculate_transient_metrics((0.0, 1.0), sample_rate=10)).lower()
        forbidden = ("punchy", "weak", "snappy", "dull", "smashed", "overcompressed")
        for word in forbidden:
            self.assertNotIn(word, text)


class FutureTransientTests(unittest.TestCase):
    @unittest.skip("Future phase only; transient flags are not implemented yet.")
    def test_transient_flags_are_separate_from_factual_metrics(self) -> None:
        """Future test: factual flags need separate approval from metrics."""
