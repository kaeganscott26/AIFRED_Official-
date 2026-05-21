"""Tests for `aifred_brain.reference_compare`."""

from __future__ import annotations

import unittest

from aifred_brain.reference_compare import (
    ReferenceComparisonAvailability,
    calculate_delta_from_target,
    calculate_percent_delta_from_target,
    compare_packet_to_reference,
    compare_reference_collections,
    compare_reference_metric,
)


def _fact(
    name: str = "sample_peak",
    value: object = 0.5,
    *,
    family: str = "level",
    unit: str = "linear",
    available: bool = True,
) -> dict[str, object]:
    return {
        "family": family,
        "name": name,
        "value": value,
        "unit": unit,
        "available": available,
    }


class ReferenceCompareFoundationTests(unittest.TestCase):
    def test_numeric_delta_from_target_works(self) -> None:
        self.assertEqual(calculate_delta_from_target(1.5, 1.0), 0.5)

    def test_absolute_delta_works(self) -> None:
        comparison = compare_reference_metric(_fact(value=0.5), _fact(value=2.0))
        self.assertEqual(comparison.absolute_delta, 1.5)

    def test_percent_delta_from_target_works(self) -> None:
        self.assertEqual(calculate_percent_delta_from_target(3.0, 2.0), 50.0)

    def test_percent_delta_with_zero_target_denominator_returns_none(self) -> None:
        self.assertIsNone(calculate_percent_delta_from_target(1.0, 0.0))

    def test_zero_current_value_is_treated_as_valid(self) -> None:
        comparison = compare_reference_metric(_fact(value=0.0), _fact(value=0.25))
        self.assertEqual(comparison.availability, ReferenceComparisonAvailability.AVAILABLE)
        self.assertEqual(comparison.delta_from_target, -0.25)
        self.assertEqual(comparison.percent_delta_from_target, -100.0)

    def test_zero_target_value_is_valid_for_delta_but_not_percent_denominator(self) -> None:
        comparison = compare_reference_metric(_fact(value=0.25), _fact(value=0.0))
        self.assertEqual(comparison.availability, ReferenceComparisonAvailability.AVAILABLE)
        self.assertEqual(comparison.delta_from_target, 0.25)
        self.assertIsNone(comparison.percent_delta_from_target)

    def test_missing_current_metric_is_represented_honestly(self) -> None:
        comparison = compare_reference_metric(None, _fact())
        self.assertEqual(comparison.availability, ReferenceComparisonAvailability.MISSING)
        self.assertIsNone(comparison.delta_from_target)

    def test_missing_target_metric_is_represented_honestly(self) -> None:
        comparison = compare_reference_metric(_fact(), None)
        self.assertEqual(comparison.availability, ReferenceComparisonAvailability.MISSING)
        self.assertIsNone(comparison.delta_from_target)

    def test_current_unavailable_is_represented_honestly(self) -> None:
        comparison = compare_reference_metric(_fact(value=None, available=False), _fact(value=0.5))
        self.assertEqual(comparison.availability, ReferenceComparisonAvailability.CURRENT_UNAVAILABLE)
        self.assertIsNone(comparison.delta_from_target)

    def test_target_unavailable_is_represented_honestly(self) -> None:
        comparison = compare_reference_metric(_fact(value=0.5), _fact(value=None, available=False))
        self.assertEqual(comparison.availability, ReferenceComparisonAvailability.TARGET_UNAVAILABLE)
        self.assertIsNone(comparison.delta_from_target)

    def test_both_unavailable_is_represented_honestly(self) -> None:
        comparison = compare_reference_metric(_fact(value=None, available=False), _fact(value=None, available=False))
        self.assertEqual(comparison.availability, ReferenceComparisonAvailability.BOTH_UNAVAILABLE)
        self.assertIsNone(comparison.delta_from_target)

    def test_non_numeric_values_do_not_produce_fake_numeric_delta(self) -> None:
        comparison = compare_reference_metric(_fact(value="current"), _fact(value="target"))
        self.assertEqual(comparison.availability, ReferenceComparisonAvailability.NON_NUMERIC)
        self.assertIsNone(comparison.delta_from_target)
        self.assertIsNone(comparison.absolute_delta)
        self.assertIsNone(comparison.percent_delta_from_target)

    def test_units_are_preserved(self) -> None:
        comparison = compare_reference_metric(_fact(unit="dBFS"), _fact(value=0.25, unit="dBFS"))
        self.assertEqual(comparison.unit, "dBFS")

    def test_family_and_name_are_preserved(self) -> None:
        comparison = compare_reference_metric(_fact("rms", 0.2, family="level"), _fact("rms", 0.3, family="level"))
        self.assertEqual(comparison.family, "level")
        self.assertEqual(comparison.name, "rms")

    def test_collection_comparison_aligns_metrics_by_name_and_family(self) -> None:
        result = compare_reference_collections(
            (_fact("sample_peak", 0.5, family="level"), _fact("correlation", 0.1, family="stereo")),
            (_fact("correlation", 0.3, family="stereo"), _fact("sample_peak", 0.75, family="level")),
        )
        comparisons = {(comparison.family, comparison.name): comparison for comparison in result.comparisons}
        self.assertEqual(comparisons[("level", "sample_peak")].delta_from_target, -0.25)
        self.assertEqual(comparisons[("stereo", "correlation")].delta_from_target, -0.19999999999999998)

    def test_packet_comparison_can_compare_facts_from_packet_like_dictionaries(self) -> None:
        result = compare_packet_to_reference(
            {"facts": (_fact("rms", 0.2),)},
            {"facts": (_fact("rms", 0.3),)},
            current_label="Current Render",
            target_label="Selected Target",
        )
        self.assertEqual(result.current_label, "Current Render")
        self.assertEqual(result.target_label, "Selected Target")
        self.assertEqual(result.comparisons[0].delta_from_target, -0.09999999999999998)

    def test_result_mode_is_reference_not_compare_ab(self) -> None:
        result = compare_reference_collections((_fact(),), (_fact(value=0.75),))
        self.assertEqual(result.mode, "Reference")
        self.assertNotIn("Compare A/B", result.mode)

    def test_selected_target_label_is_preserved_safely(self) -> None:
        result = compare_reference_collections(
            (_fact(),),
            (_fact(value=0.75),),
            target_label=r"C:\Users\North\Refs\target.wav",
        )
        self.assertIn("<private-path>/target.wav", result.target_label)
        self.assertNotIn(r"C:\Users\North\Refs", result.target_label)

    def test_no_global_reference_pool_language_appears_by_default(self) -> None:
        result = compare_reference_collections((_fact(),), (_fact(value=0.75),))
        text = repr(result).lower()
        self.assertNotIn("pool", text)
        self.assertNotIn("global", text)
        self.assertNotIn("professional", text)

    def test_no_better_mix_language_appears(self) -> None:
        result = compare_reference_collections((_fact(),), (_fact(value=0.75),))
        text = repr(result).lower()
        self.assertNotIn("better", text)
        self.assertNotIn("worse", text)
        self.assertNotIn("winner", text)

    def test_no_fake_minus_999_values_appear(self) -> None:
        with self.assertRaises(ValueError):
            compare_reference_metric(_fact(value=-999), _fact(value=0.1))

    def test_no_advice_text_appears(self) -> None:
        result = compare_reference_collections((_fact(),), (_fact(value=0.75),))
        text = repr(result).lower()
        for phrase in ("advice", "recommend", "you should", "try ", "fix your"):
            self.assertNotIn(phrase, text)

    def test_no_canned_phrases_appear(self) -> None:
        result = compare_reference_collections((_fact(),), (_fact(value=0.75),))
        text = repr(result).lower()
        for phrase in ("next practical move", "make it sound more professional", "your mix needs"):
            self.assertNotIn(phrase, text)


@unittest.skip("Future phase only; reference-pool profile comparison is not implemented yet.")
class FutureReferenceCompareTests(unittest.TestCase):
    def test_reference_pool_profile_requires_explicit_profile_object(self) -> None:
        """Future test: pool-style targets require explicit approved profile data."""


if __name__ == "__main__":
    unittest.main()
