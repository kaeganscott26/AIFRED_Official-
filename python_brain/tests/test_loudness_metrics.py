"""Tests for `aifred_brain.loudness_metrics` window infrastructure.

Only windowing and availability helpers are implemented in Phase 3D. LUFS
algorithm tests remain skipped until an approved implementation exists.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.loudness_metrics import (  # noqa: E402
    BiquadCoefficients,
    MOMENTARY_WINDOW_SECONDS,
    SHORT_TERM_WINDOW_SECONDS,
    LoudnessAvailability,
    LoudnessWindowKind,
    apply_k_weighting,
    apply_loudness_filter_chain,
    build_loudness_windows,
    calculate_integrated_loudness,
    calculate_loudness_metrics,
    calculate_momentary_loudness,
    calculate_short_term_loudness,
    calculate_duration_seconds,
    calculate_mean_square,
    calculate_window_frame_count,
    get_k_weighting_filter_description,
    identity_biquad_coefficients,
    process_biquad_interleaved,
    process_biquad_samples,
    summarize_loudness_availability,
    validate_biquad_coefficients,
    validate_loudness_inputs,
    validate_supported_loudness_sample_rate,
)


class LoudnessWindowInfrastructureTests(unittest.TestCase):
    def test_duration_calculation_from_interleaved_samples(self) -> None:
        self.assertEqual(calculate_duration_seconds(96_000, sample_rate=48_000, channels=2), 1.0)

    def test_invalid_sample_rate_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_loudness_inputs((0.0,), sample_rate=0, channels=1)

    def test_invalid_channel_count_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_loudness_inputs((0.0,), sample_rate=48_000, channels=0)

    def test_empty_sample_sequence_handled_safely(self) -> None:
        windows = build_loudness_windows(
            (),
            sample_rate=48_000,
            channels=1,
            window_seconds=MOMENTARY_WINDOW_SECONDS,
            kind=LoudnessWindowKind.MOMENTARY,
        )
        self.assertEqual(windows, ())
        self.assertEqual(calculate_duration_seconds(0, sample_rate=48_000, channels=1), 0.0)

    def test_mean_square_for_silence_is_zero(self) -> None:
        self.assertEqual(calculate_mean_square((0.0, 0.0, 0.0)), 0.0)

    def test_mean_square_for_known_values(self) -> None:
        self.assertAlmostEqual(calculate_mean_square((1.0, -1.0, 0.0, 0.0)), 0.5)

    def test_momentary_window_frame_count_at_48000(self) -> None:
        self.assertEqual(calculate_window_frame_count(48_000, MOMENTARY_WINDOW_SECONDS), 19_200)

    def test_short_term_window_frame_count_at_48000(self) -> None:
        self.assertEqual(calculate_window_frame_count(48_000, SHORT_TERM_WINDOW_SECONDS), 144_000)

    def test_momentary_windows_from_synthetic_samples(self) -> None:
        samples = (0.25,) * 19_200
        windows = build_loudness_windows(
            samples,
            sample_rate=48_000,
            channels=1,
            window_seconds=MOMENTARY_WINDOW_SECONDS,
            kind=LoudnessWindowKind.MOMENTARY,
        )
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0].kind, LoudnessWindowKind.MOMENTARY)
        self.assertTrue(windows[0].is_complete)
        self.assertAlmostEqual(windows[0].mean_square, 0.0625)

    def test_short_term_windows_from_synthetic_samples(self) -> None:
        samples = (0.5,) * 144_000
        windows = build_loudness_windows(
            samples,
            sample_rate=48_000,
            channels=1,
            window_seconds=SHORT_TERM_WINDOW_SECONDS,
            kind=LoudnessWindowKind.SHORT_TERM,
        )
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0].frame_count, 144_000)
        self.assertAlmostEqual(windows[0].duration_seconds, 3.0)
        self.assertAlmostEqual(windows[0].mean_square, 0.25)

    def test_incomplete_windows_excluded_by_default(self) -> None:
        samples = (0.5,) * 10_000
        windows = build_loudness_windows(
            samples,
            sample_rate=48_000,
            channels=1,
            window_seconds=MOMENTARY_WINDOW_SECONDS,
            kind=LoudnessWindowKind.MOMENTARY,
        )
        self.assertEqual(windows, ())

    def test_incomplete_windows_included_when_requested(self) -> None:
        samples = (0.5,) * 10_000
        windows = build_loudness_windows(
            samples,
            sample_rate=48_000,
            channels=1,
            window_seconds=MOMENTARY_WINDOW_SECONDS,
            kind=LoudnessWindowKind.MOMENTARY,
            include_incomplete=True,
        )
        self.assertEqual(len(windows), 1)
        self.assertFalse(windows[0].is_complete)
        self.assertEqual(windows[0].frame_count, 10_000)

    def test_availability_states(self) -> None:
        self.assertEqual(summarize_loudness_availability(0.0, 0.4), LoudnessAvailability.UNAVAILABLE)
        self.assertEqual(summarize_loudness_availability(0.2, 0.4), LoudnessAvailability.LIMITED)
        self.assertEqual(summarize_loudness_availability(0.4, 0.4), LoudnessAvailability.AVAILABLE)

    def test_no_fake_minus_999_values_in_window_helpers(self) -> None:
        samples = (0.0,) * 19_200
        windows = build_loudness_windows(
            samples,
            sample_rate=48_000,
            channels=1,
            window_seconds=MOMENTARY_WINDOW_SECONDS,
            kind=LoudnessWindowKind.MOMENTARY,
        )
        values = [windows[0].mean_square, windows[0].duration_seconds, windows[0].frame_count]
        self.assertNotIn(-999, values)


class GenericBiquadPrimitiveTests(unittest.TestCase):
    def test_identity_filter_returns_input_unchanged(self) -> None:
        samples = (0.0, 0.25, -0.5, 1.0, -1.0)
        self.assertEqual(process_biquad_samples(samples, identity_biquad_coefficients()), samples)

    def test_silence_remains_silence_under_identity_filter(self) -> None:
        output = process_biquad_samples((0.0, 0.0, 0.0), identity_biquad_coefficients())
        self.assertEqual(output, (0.0, 0.0, 0.0))

    def test_output_length_matches_input_length(self) -> None:
        samples = (0.1, 0.2, 0.3, 0.4)
        output = process_biquad_samples(samples, BiquadCoefficients(0.5, 0.25, 0.0, 1.0, 0.0, 0.0))
        self.assertEqual(len(output), len(samples))

    def test_invalid_a0_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_biquad_coefficients(BiquadCoefficients(1.0, 0.0, 0.0, 0.0, 0.0, 0.0))

    def test_non_finite_coefficient_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_biquad_coefficients(BiquadCoefficients(float("inf"), 0.0, 0.0, 1.0, 0.0, 0.0))

    def test_non_finite_sample_rejected(self) -> None:
        with self.assertRaises(ValueError):
            process_biquad_samples((0.0, float("nan")), identity_biquad_coefficients())

    def test_interleaved_stereo_processing_preserves_length(self) -> None:
        samples = (1.0, 0.0, 0.5, 0.0, 0.25, 0.0)
        output = process_biquad_interleaved(samples, identity_biquad_coefficients(), channels=2)
        self.assertEqual(len(output), len(samples))

    def test_interleaved_stereo_processing_uses_independent_channel_state(self) -> None:
        samples = (1.0, 0.0, 0.0, 0.0)
        coefficients = BiquadCoefficients(b0=1.0, b1=0.5, b2=0.0, a0=1.0, a1=0.0, a2=0.0)
        output = process_biquad_interleaved(samples, coefficients, channels=2)
        self.assertEqual(output, (1.0, 0.0, 0.5, 0.0))

    def test_repeated_calls_do_not_share_hidden_state(self) -> None:
        coefficients = BiquadCoefficients(b0=1.0, b1=0.5, b2=0.0, a0=1.0, a1=0.0, a2=0.0)
        first = process_biquad_samples((1.0, 0.0), coefficients)
        second = process_biquad_samples((1.0, 0.0), coefficients)
        self.assertEqual(first, second)

    def test_no_fake_minus_999_values_in_biquad_primitives(self) -> None:
        output = process_biquad_samples((0.0, 1.0), identity_biquad_coefficients())
        self.assertNotIn(-999, output)

    def test_k_weighting_placeholders_still_raise_not_implemented(self) -> None:
        with self.assertRaises(NotImplementedError):
            validate_supported_loudness_sample_rate(48_000)
        with self.assertRaises(NotImplementedError):
            get_k_weighting_filter_description(48_000)
        with self.assertRaises(NotImplementedError):
            apply_k_weighting((0.0,), 48_000)
        with self.assertRaises(NotImplementedError):
            apply_loudness_filter_chain((0.0,), 48_000)

    def test_lufs_facing_functions_still_raise_not_implemented(self) -> None:
        with self.assertRaises(NotImplementedError):
            calculate_momentary_loudness((0.0,), 48_000)
        with self.assertRaises(NotImplementedError):
            calculate_short_term_loudness((0.0,), 48_000)
        with self.assertRaises(NotImplementedError):
            calculate_integrated_loudness((0.0,), 48_000)
        with self.assertRaises(NotImplementedError):
            calculate_loudness_metrics(object())


class FutureLoudnessAlgorithmTests(unittest.TestCase):
    @unittest.skip("Future phase only; K-weighting is not implemented yet.")
    def test_k_weighting_behavior(self) -> None:
        """Future test: K-weighting filter behavior is standards-aware."""

    @unittest.skip("Phase 3E contract only; K-weighting silence behavior is not implemented yet.")
    def test_k_weighting_silence_behavior(self) -> None:
        """Future test: silence remains silence through K-weighting."""

    @unittest.skip("Phase 3E contract only; filter processing is not implemented yet.")
    def test_filter_output_length_preservation(self) -> None:
        """Future test: filter output length matches input length."""

    @unittest.skip("Phase 3E contract only; sample-rate support is not implemented yet.")
    def test_unsupported_sample_rate_rejection(self) -> None:
        """Future test: unsupported sample rates are rejected clearly."""

    @unittest.skip("Phase 3E contract only; filter input validation is not implemented yet.")
    def test_invalid_sample_rejection(self) -> None:
        """Future test: invalid samples are rejected before filtering."""

    @unittest.skip("Phase 3E contract only; mono filter behavior is not implemented yet.")
    def test_mono_filter_behavior(self) -> None:
        """Future test: mono input can be filtered safely."""

    @unittest.skip("Phase 3E contract only; stereo/interleaved filter behavior is not implemented yet.")
    def test_stereo_interleaved_filter_behavior(self) -> None:
        """Future test: stereo/interleaved input is handled safely."""

    @unittest.skip("Phase 3E contract only; coefficient documentation is not implemented yet.")
    def test_coefficient_documentation_requirement(self) -> None:
        """Future test: coefficients include documented source and tolerance."""

    @unittest.skip("Phase 3E contract only; filter stage must not produce LUFS.")
    def test_no_fake_lufs_from_filter_stage(self) -> None:
        """Future test: filter stage does not create fake LUFS values."""

    @unittest.skip("Phase 3E contract only; advice generation belongs outside filter code.")
    def test_no_advice_text_from_filter_stage(self) -> None:
        """Future test: filter stage emits no advice text."""

    @unittest.skip("Future phase only; BS.1770 filtering is not implemented yet.")
    def test_bs1770_filter_behavior(self) -> None:
        """Future test: BS.1770-style filter behavior is verified."""

    @unittest.skip("Future phase only; integrated loudness gating is not implemented yet.")
    def test_integrated_loudness_gating(self) -> None:
        """Future test: integrated loudness uses approved gating behavior."""

    @unittest.skip("Future phase only; LUFS calculation is not implemented yet.")
    def test_lufs_tolerance(self) -> None:
        """Future test: LUFS values match proof tones within documented tolerance."""

    @unittest.skip("Future phase only; LUFS calculation is not implemented yet.")
    def test_lufs_is_not_rms(self) -> None:
        """Future test: LUFS and RMS are not confused or relabeled."""

    @unittest.skip("Future phase only; silence loudness behavior is not implemented yet.")
    def test_silence_returns_unavailable_without_fake_values(self) -> None:
        """Future test: silence returns None/unavailable, not fake LUFS values."""

    @unittest.skip("Future phase only; short-file loudness handling is not implemented yet.")
    def test_short_file_reports_limited_or_unavailable_state(self) -> None:
        """Future test: insufficient duration is labeled honestly."""

    @unittest.skip("Future phase only; momentary loudness is not implemented yet.")
    def test_momentary_window_behavior(self) -> None:
        """Future test: approximately 400 ms windows behave consistently."""

    @unittest.skip("Future phase only; short-term loudness is not implemented yet.")
    def test_short_term_window_behavior(self) -> None:
        """Future test: approximately 3 second windows behave consistently."""

    @unittest.skip("Future phase only; advice generation belongs outside this module.")
    def test_no_advice_text(self) -> None:
        """Future test: loudness module emits facts only, no advice text."""
