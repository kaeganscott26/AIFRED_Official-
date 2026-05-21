"""Tests for `aifred_brain.level_metrics`.

- sample peak
- RMS
- headroom
- clipping/ceiling state
- unavailable data state distinct from zero
"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.level_metrics import (  # noqa: E402
    calculate_crest_factor_db,
    calculate_level_metrics,
    calculate_rms,
    calculate_sample_peak,
    linear_to_dbfs,
)


class LevelMetricsContractTests(unittest.TestCase):
    def test_silence_has_zero_linear_and_unavailable_db_values(self) -> None:
        metrics = calculate_level_metrics((0.0, 0.0, 0.0))
        self.assertEqual(metrics.sample_peak_linear, 0.0)
        self.assertEqual(metrics.rms_linear, 0.0)
        self.assertIsNone(metrics.sample_peak_dbfs)
        self.assertIsNone(metrics.rms_dbfs)
        self.assertIsNone(metrics.crest_factor_db)
        self.assertTrue(metrics.is_silent)
        self.assertIsNone(metrics.is_ceiling_safe)

    def test_full_scale_sample_is_zero_dbfs(self) -> None:
        self.assertEqual(calculate_sample_peak((0.0, 1.0, -0.25)), 1.0)
        self.assertEqual(linear_to_dbfs(1.0), 0.0)

    def test_half_scale_sample_is_about_minus_six_dbfs(self) -> None:
        self.assertAlmostEqual(linear_to_dbfs(0.5), -6.020599913, places=6)

    def test_rms_on_known_simple_array(self) -> None:
        self.assertAlmostEqual(calculate_rms((1.0, -1.0, 1.0, -1.0)), 1.0)
        self.assertAlmostEqual(calculate_rms((0.0, 1.0)), math.sqrt(0.5))

    def test_crest_factor_on_known_simple_array(self) -> None:
        peak = 1.0
        rms = math.sqrt(0.5)
        self.assertAlmostEqual(calculate_crest_factor_db(peak, rms), 3.010299956, places=6)

    def test_clipping_detection_works(self) -> None:
        clipped = calculate_level_metrics((0.0, 1.0, -0.2))
        unclipped = calculate_level_metrics((0.0, 0.999, -0.2))
        self.assertTrue(clipped.has_sample_clip)
        self.assertFalse(unclipped.has_sample_clip)

    def test_ceiling_safety_against_minus_one_dbfs(self) -> None:
        safe = calculate_level_metrics((0.5,), ceiling_dbfs=-1.0)
        unsafe = calculate_level_metrics((1.0,), ceiling_dbfs=-1.0)
        self.assertTrue(safe.is_ceiling_safe)
        self.assertGreater(safe.ceiling_margin_db or 0.0, 0.0)
        self.assertFalse(unsafe.is_ceiling_safe)
        self.assertAlmostEqual(unsafe.ceiling_margin_db or 0.0, -1.0)

    def test_no_fake_minus_999_values(self) -> None:
        metrics = calculate_level_metrics((0.0,))
        values = (
            metrics.sample_peak_dbfs,
            metrics.rms_dbfs,
            metrics.crest_factor_db,
            metrics.ceiling_margin_db,
        )
        self.assertNotIn(-999, values)
