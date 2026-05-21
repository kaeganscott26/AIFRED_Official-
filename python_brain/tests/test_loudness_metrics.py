"""Skipped contract tests for `aifred_brain.loudness_metrics`.

These tests document future coverage only. They must stay skipped until an
approved loudness implementation exists.
"""

import unittest


class LoudnessMetricsContractTests(unittest.TestCase):
    @unittest.skip("Phase 3C contract only; silence loudness behavior is not implemented yet.")
    def test_silence_returns_unavailable_without_fake_values(self) -> None:
        """Future test: silence returns None/unavailable, not fake LUFS values."""

    @unittest.skip("Phase 3C contract only; short-file handling is not implemented yet.")
    def test_short_file_reports_limited_or_unavailable_state(self) -> None:
        """Future test: insufficient duration is labeled honestly."""

    @unittest.skip("Phase 3C contract only; momentary loudness is not implemented yet.")
    def test_momentary_window_behavior(self) -> None:
        """Future test: approximately 400 ms windows behave consistently."""

    @unittest.skip("Phase 3C contract only; short-term loudness is not implemented yet.")
    def test_short_term_window_behavior(self) -> None:
        """Future test: approximately 3 second windows behave consistently."""

    @unittest.skip("Phase 3C contract only; integrated loudness gating is not implemented yet.")
    def test_integrated_loudness_gating(self) -> None:
        """Future test: integrated loudness uses approved gating behavior."""

    @unittest.skip("Phase 3C contract only; LUFS implementation is not implemented yet.")
    def test_lufs_is_not_rms(self) -> None:
        """Future test: LUFS and RMS are not confused or relabeled."""

    @unittest.skip("Phase 3C contract only; no fake loudness values should ever be emitted.")
    def test_no_fake_minus_999_values(self) -> None:
        """Future test: loudness unavailable state never uses fake -999 values."""

    @unittest.skip("Phase 3C contract only; advice generation belongs outside this module.")
    def test_no_advice_text(self) -> None:
        """Future test: loudness module emits facts only, no advice text."""
