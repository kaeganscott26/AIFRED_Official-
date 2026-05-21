"""Tests for `aifred_brain.compare_ab`."""

from __future__ import annotations

import unittest

from aifred_brain.compare_ab import (
    ComparisonAvailability,
    calculate_delta,
    calculate_percent_delta,
    compare_metric_collections,
    compare_metric_fact,
    compare_packet_facts,
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


class CompareABFoundationTests(unittest.TestCase):
    def test_numeric_delta_works(self) -> None:
        self.assertEqual(calculate_delta(1.0, 1.5), 0.5)

    def test_absolute_delta_works(self) -> None:
        comparison = compare_metric_fact(_fact(value=2.0), _fact(value=0.5))
        self.assertEqual(comparison.absolute_delta, 1.5)

    def test_percent_delta_works(self) -> None:
        self.assertEqual(calculate_percent_delta(2.0, 3.0), 50.0)

    def test_percent_delta_with_zero_denominator_returns_none(self) -> None:
        self.assertIsNone(calculate_percent_delta(0.0, 1.0))

    def test_zero_value_is_treated_as_valid(self) -> None:
        comparison = compare_metric_fact(_fact(value=0.0), _fact(value=0.25))
        self.assertEqual(comparison.availability, ComparisonAvailability.AVAILABLE)
        self.assertEqual(comparison.delta, 0.25)
        self.assertIsNone(comparison.percent_delta)

    def test_missing_metric_is_represented_honestly(self) -> None:
        comparison = compare_metric_fact(_fact(), None)
        self.assertEqual(comparison.availability, ComparisonAvailability.MISSING)
        self.assertIsNone(comparison.delta)

    def test_a_unavailable_is_represented_honestly(self) -> None:
        comparison = compare_metric_fact(_fact(value=None, available=False), _fact(value=0.5))
        self.assertEqual(comparison.availability, ComparisonAvailability.A_UNAVAILABLE)
        self.assertIsNone(comparison.delta)

    def test_b_unavailable_is_represented_honestly(self) -> None:
        comparison = compare_metric_fact(_fact(value=0.5), _fact(value=None, available=False))
        self.assertEqual(comparison.availability, ComparisonAvailability.B_UNAVAILABLE)
        self.assertIsNone(comparison.delta)

    def test_both_unavailable_is_represented_honestly(self) -> None:
        comparison = compare_metric_fact(_fact(value=None, available=False), _fact(value=None, available=False))
        self.assertEqual(comparison.availability, ComparisonAvailability.BOTH_UNAVAILABLE)
        self.assertIsNone(comparison.delta)

    def test_non_numeric_values_do_not_produce_fake_numeric_delta(self) -> None:
        comparison = compare_metric_fact(_fact(value="available"), _fact(value="unavailable"))
        self.assertEqual(comparison.availability, ComparisonAvailability.NON_NUMERIC)
        self.assertIsNone(comparison.delta)
        self.assertIsNone(comparison.absolute_delta)
        self.assertIsNone(comparison.percent_delta)

    def test_units_are_preserved(self) -> None:
        comparison = compare_metric_fact(_fact(unit="dBFS"), _fact(value=0.25, unit="dBFS"))
        self.assertEqual(comparison.unit, "dBFS")

    def test_family_and_name_are_preserved(self) -> None:
        comparison = compare_metric_fact(_fact("rms", 0.2, family="level"), _fact("rms", 0.3, family="level"))
        self.assertEqual(comparison.family, "level")
        self.assertEqual(comparison.name, "rms")

    def test_collection_comparison_aligns_metrics_by_name_and_family(self) -> None:
        result = compare_metric_collections(
            (_fact("sample_peak", 0.5, family="level"), _fact("correlation", 0.1, family="stereo")),
            (_fact("correlation", 0.3, family="stereo"), _fact("sample_peak", 0.75, family="level")),
        )
        comparisons = {(comparison.family, comparison.name): comparison for comparison in result.comparisons}
        self.assertEqual(comparisons[("level", "sample_peak")].delta, 0.25)
        self.assertEqual(comparisons[("stereo", "correlation")].delta, 0.19999999999999998)

    def test_packet_comparison_can_compare_facts_from_packet_like_dictionaries(self) -> None:
        result = compare_packet_facts(
            {"facts": (_fact("rms", 0.2),)},
            {"facts": (_fact("rms", 0.3),)},
            a_label="A Render",
            b_label="B Render",
        )
        self.assertEqual(result.a_label, "A Render")
        self.assertEqual(result.b_label, "B Render")
        self.assertEqual(result.comparisons[0].delta, 0.09999999999999998)

    def test_result_mode_is_compare_ab_not_reference(self) -> None:
        result = compare_metric_collections((_fact(),), (_fact(value=0.75),))
        self.assertEqual(result.mode, "Compare A/B")
        self.assertNotIn("Reference", result.mode)

    def test_no_reference_pool_language_appears(self) -> None:
        result = compare_metric_collections((_fact(),), (_fact(value=0.75),))
        text = repr(result).lower()
        self.assertNotIn("reference", text)
        self.assertNotIn("pool", text)
        self.assertNotIn("target", text)

    def test_no_better_mix_language_appears(self) -> None:
        result = compare_metric_collections((_fact(),), (_fact(value=0.75),))
        text = repr(result).lower()
        self.assertNotIn("better", text)
        self.assertNotIn("winner", text)

    def test_no_fake_minus_999_values_appear(self) -> None:
        with self.assertRaises(ValueError):
            compare_metric_fact(_fact(value=-999), _fact(value=0.1))

    def test_no_advice_text_appears(self) -> None:
        result = compare_metric_collections((_fact(),), (_fact(value=0.75),))
        text = repr(result).lower()
        for phrase in ("advice", "recommend", "you should", "try ", "fix your"):
            self.assertNotIn(phrase, text)

    def test_no_canned_phrases_appear(self) -> None:
        result = compare_metric_collections((_fact(),), (_fact(value=0.75),))
        text = repr(result).lower()
        for phrase in ("next practical move", "make it sound more professional", "your mix needs"):
            self.assertNotIn(phrase, text)


@unittest.skip("Future phase only; compare interpretation is not implemented yet.")
class FutureCompareABTests(unittest.TestCase):
    def test_goal_based_compare_conclusion_is_separate_from_factual_deltas(self) -> None:
        """Future test: goal-based conclusions belong outside factual comparison."""


if __name__ == "__main__":
    unittest.main()
