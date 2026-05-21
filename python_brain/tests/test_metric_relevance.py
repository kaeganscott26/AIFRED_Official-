"""Tests for factual metric relevance routing."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.metric_relevance import (  # noqa: E402
    MetricFamily,
    UserIntentCategory,
    classify_user_intent,
    filter_available_metrics,
    mode_allows_compare,
    mode_allows_reference,
    select_relevant_metric_families,
)


class MetricRelevanceFoundationTests(unittest.TestCase):
    def test_classifies_saturation_intent(self) -> None:
        self.assertEqual(classify_user_intent("Is saturation changing the tone?"), UserIntentCategory.SATURATION)

    def test_classifies_compression_intent(self) -> None:
        self.assertEqual(classify_user_intent("Check the compressor attack"), UserIntentCategory.COMPRESSION)

    def test_classifies_limiting_intent(self) -> None:
        self.assertEqual(classify_user_intent("Limiter ceiling and loudness"), UserIntentCategory.LIMITING)

    def test_classifies_eq_intent(self) -> None:
        self.assertEqual(classify_user_intent("Need EQ frequency evidence"), UserIntentCategory.EQ)

    def test_classifies_stereo_width_intent(self) -> None:
        self.assertEqual(classify_user_intent("How is the stereo width?"), UserIntentCategory.STEREO_WIDTH)

    def test_classifies_vocal_intent(self) -> None:
        self.assertEqual(classify_user_intent("Check the vocal"), UserIntentCategory.VOCAL)

    def test_classifies_mastering_intent(self) -> None:
        self.assertEqual(classify_user_intent("Mastering loudness check"), UserIntentCategory.MASTERING)

    def test_classifies_compare_intent(self) -> None:
        self.assertEqual(classify_user_intent("Compare mix A vs mix B"), UserIntentCategory.COMPARE)

    def test_classifies_reference_target_intent(self) -> None:
        self.assertEqual(classify_user_intent("Match the reference target"), UserIntentCategory.REFERENCE_TARGET)

    def test_unknown_intent_falls_back_safely(self) -> None:
        result = select_relevant_metric_families(classify_user_intent(""), mode="analyze")
        self.assertEqual(result.intent, UserIntentCategory.UNKNOWN)
        self.assertIn(MetricFamily.LEVEL, result.primary_metrics)
        self.assertIn(MetricFamily.DYNAMICS, result.primary_metrics)

    def test_analyze_mode_does_not_require_reference_context_by_default(self) -> None:
        result = select_relevant_metric_families(UserIntentCategory.GENERAL_ANALYZE, mode="analyze")
        self.assertFalse(result.requires_reference_context)
        self.assertTrue(mode_allows_reference("analyze", UserIntentCategory.GENERAL_ANALYZE) is False)

    def test_reference_mode_requires_reference_context_for_reference_intent(self) -> None:
        result = select_relevant_metric_families(UserIntentCategory.REFERENCE_TARGET, mode="reference")
        self.assertTrue(result.requires_reference_context)
        self.assertIn(MetricFamily.REFERENCE, result.primary_metrics)
        self.assertTrue(mode_allows_reference("reference", UserIntentCategory.REFERENCE_TARGET))

    def test_compare_mode_requires_compare_context_and_not_global_reference(self) -> None:
        result = select_relevant_metric_families(UserIntentCategory.COMPARE, mode="compare")
        self.assertTrue(result.requires_compare_context)
        self.assertFalse(result.requires_reference_context)
        self.assertIn(MetricFamily.COMPARE, result.primary_metrics)
        self.assertNotIn(MetricFamily.REFERENCE, result.primary_metrics)
        self.assertTrue(mode_allows_compare("compare", UserIntentCategory.COMPARE))

    def test_saturation_selection_includes_tonal_frequency_level_style_families(self) -> None:
        result = select_relevant_metric_families(UserIntentCategory.SATURATION)
        self.assertIn(MetricFamily.TONAL_BALANCE, result.primary_metrics)
        self.assertIn(MetricFamily.FREQUENCY, result.primary_metrics)
        self.assertIn(MetricFamily.LEVEL, result.primary_metrics)
        self.assertIn(MetricFamily.LOUDNESS, result.primary_metrics)

    def test_compression_selection_includes_dynamics_and_transients(self) -> None:
        result = select_relevant_metric_families(UserIntentCategory.COMPRESSION)
        self.assertIn(MetricFamily.DYNAMICS, result.primary_metrics)
        self.assertIn(MetricFamily.TRANSIENTS, result.primary_metrics)

    def test_limiting_selection_includes_level_loudness_dynamics(self) -> None:
        result = select_relevant_metric_families(UserIntentCategory.LIMITING)
        self.assertIn(MetricFamily.LEVEL, result.primary_metrics)
        self.assertIn(MetricFamily.LOUDNESS, result.primary_metrics)
        self.assertIn(MetricFamily.DYNAMICS, result.primary_metrics)

    def test_eq_selection_includes_frequency_and_tonal_balance(self) -> None:
        result = select_relevant_metric_families(UserIntentCategory.EQ)
        self.assertEqual(result.primary_metrics, (MetricFamily.FREQUENCY, MetricFamily.TONAL_BALANCE))

    def test_stereo_width_selection_includes_stereo(self) -> None:
        result = select_relevant_metric_families(UserIntentCategory.STEREO_WIDTH)
        self.assertIn(MetricFamily.STEREO, result.primary_metrics)

    def test_available_metrics_filter_removes_unavailable_families(self) -> None:
        selected = (MetricFamily.LEVEL, MetricFamily.LOUDNESS, MetricFamily.DYNAMICS)
        available = (MetricFamily.LEVEL, MetricFamily.DYNAMICS)
        self.assertEqual(filter_available_metrics(selected, available), (MetricFamily.LEVEL, MetricFamily.DYNAMICS))
        result = select_relevant_metric_families(UserIntentCategory.LIMITING, available_metrics=available)
        self.assertNotIn(MetricFamily.LOUDNESS, result.primary_metrics)
        self.assertIn(MetricFamily.LOUDNESS, result.excluded_metrics)

    def test_no_advice_text_appears_in_result_repr(self) -> None:
        text = repr(select_relevant_metric_families(UserIntentCategory.COMPRESSION)).lower()
        for word in ("advice", "recommend", "fix", "should", "try", "use this"):
            self.assertNotIn(word, text)

    def test_no_canned_phrases_appear_in_result_repr(self) -> None:
        text = repr(select_relevant_metric_families(UserIntentCategory.MASTERING)).lower()
        phrases = ("your mix", "next move", "tradeoff", "make it", "sounds like")
        for phrase in phrases:
            self.assertNotIn(phrase, text)


class FutureMetricRelevanceTests(unittest.TestCase):
    @unittest.skip("Future phase only; relevance scoring is not implemented yet.")
    def test_metric_relevance_scores_are_separate_from_family_routing(self) -> None:
        """Future test: numeric scoring needs separate approval."""
