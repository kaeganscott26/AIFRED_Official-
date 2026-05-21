"""Tests for `aifred_brain.analysis_state`.

- Analyze, Reference, and Compare mode separation
- source-of-truth labels
- confidence labels
- stale/waiting/unavailable distinctions
"""

import sys
import unittest
import json
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.analysis_state import (  # noqa: E402
    AnalysisAvailability,
    AnalysisMetricBundle,
    AnalysisMode,
    ConfidenceState,
    DataFreshness,
    SourceLabel,
    analysis_result_to_dict,
    create_analysis_context,
    create_analysis_metric_bundle,
    create_analysis_result,
    create_analysis_state,
    determine_analysis_availability,
    mark_state_stale,
)


@dataclass(frozen=True)
class SyntheticMetric:
    value: float
    unit: str
    available: bool = True


class AnalysisStateContractTests(unittest.TestCase):
    def test_create_analysis_state_with_enums(self) -> None:
        state = create_analysis_state(
            mode=AnalysisMode.ANALYZE,
            source_label=SourceLabel.FILE_ANALYSIS,
            confidence=ConfidenceState.MEDIUM,
            freshness=DataFreshness.RECENT,
            sample_rate=44100,
            duration_seconds=1.0,
        )
        self.assertEqual(state.mode, AnalysisMode.ANALYZE)
        self.assertEqual(state.source, SourceLabel.FILE_ANALYSIS)
        self.assertTrue(state.has_available_data)

    def test_waiting_is_not_available_data(self) -> None:
        state = create_analysis_state(mode="analyze", source_label="File Analysis")
        self.assertEqual(state.freshness, DataFreshness.WAITING)
        self.assertFalse(state.has_available_data)

    def test_unavailable_is_distinct_from_zero_duration(self) -> None:
        zero_duration = create_analysis_state(
            mode="analyze",
            source_label="File Analysis",
            confidence="High",
            freshness="live",
            duration_seconds=0.0,
        )
        unavailable = create_analysis_state(
            mode="analyze",
            source_label="File Analysis",
            confidence="Unavailable",
            freshness="unavailable",
        )
        self.assertTrue(zero_duration.has_available_data)
        self.assertFalse(unavailable.has_available_data)

    def test_mark_state_stale_lowers_confidence_and_keeps_reason(self) -> None:
        state = create_analysis_state(mode="compare", source_label="Compare A/B", confidence="High", freshness="live")
        stale = mark_state_stale(state, reason="No current buffer data.")
        self.assertEqual(stale.freshness, DataFreshness.STALE)
        self.assertEqual(stale.confidence, ConfidenceState.LOW)
        self.assertIn("No current buffer data.", stale.notes)

    def test_create_analysis_context_preserves_mode(self) -> None:
        context = create_analysis_context("reference", "Reference Mode")
        self.assertEqual(context.mode, AnalysisMode.REFERENCE)

    def test_create_analysis_context_preserves_source_label(self) -> None:
        context = create_analysis_context("analyze", "File Analysis")
        self.assertEqual(context.source, SourceLabel.FILE_ANALYSIS)

    def test_create_analysis_context_preserves_confidence_and_freshness(self) -> None:
        context = create_analysis_context(
            "analyze",
            "File Analysis",
            confidence="High",
            freshness="recent",
        )
        self.assertEqual(context.confidence, ConfidenceState.HIGH)
        self.assertEqual(context.freshness, DataFreshness.RECENT)

    def test_empty_metric_bundle_has_all_fields_unavailable(self) -> None:
        bundle = create_analysis_metric_bundle()
        self.assertIsNone(bundle.level)
        self.assertIsNone(bundle.loudness)
        self.assertIsNone(bundle.stereo)
        self.assertIsNone(bundle.frequency)
        self.assertIsNone(bundle.tonal_balance)
        self.assertIsNone(bundle.dynamics)
        self.assertIsNone(bundle.transients)
        self.assertIsNone(bundle.compare)
        self.assertIsNone(bundle.reference)

    def test_metric_bundle_preserves_provided_level_metrics(self) -> None:
        level = {"sample_peak_dbfs": -1.0, "available": True}
        bundle = create_analysis_metric_bundle(level=level)
        self.assertIs(bundle.level, level)

    def test_metric_bundle_preserves_provided_stereo_metrics(self) -> None:
        stereo = SyntheticMetric(value=0.5, unit="correlation")
        bundle = create_analysis_metric_bundle(stereo=stereo)
        self.assertEqual(bundle.stereo, stereo)

    def test_metric_bundle_preserves_provided_frequency_metrics(self) -> None:
        frequency = {"bands": [{"name": "mid", "energy_ratio": 0.25}]}
        bundle = create_analysis_metric_bundle(frequency=frequency)
        self.assertEqual(bundle.frequency, frequency)

    def test_analysis_with_no_metrics_is_unavailable_or_limited(self) -> None:
        bundle = AnalysisMetricBundle()
        self.assertEqual(determine_analysis_availability(bundle), AnalysisAvailability.UNAVAILABLE)
        self.assertEqual(
            determine_analysis_availability(bundle, limitations=("analysis window unavailable",)),
            AnalysisAvailability.LIMITED,
        )

    def test_analysis_with_metric_bundle_is_ready_without_limitations(self) -> None:
        bundle = create_analysis_metric_bundle(level={"sample_peak_dbfs": -3.0, "available": True})
        self.assertEqual(determine_analysis_availability(bundle), AnalysisAvailability.READY)

    def test_limitations_reduce_availability_to_limited(self) -> None:
        bundle = create_analysis_metric_bundle(level={"sample_peak_dbfs": -3.0, "available": True})
        self.assertEqual(
            determine_analysis_availability(bundle, limitations=("short analysis window",)),
            AnalysisAvailability.LIMITED,
        )

    def test_warnings_are_preserved(self) -> None:
        context = create_analysis_context("analyze", "File Analysis")
        result = create_analysis_result(
            context,
            create_analysis_metric_bundle(level={"sample_peak_dbfs": -3.0}),
            warnings=("short file",),
        )
        self.assertEqual(result.warnings, ("short file",))

    def test_metadata_is_included_safely(self) -> None:
        context = create_analysis_context("analyze", "File Analysis")
        result = create_analysis_result(
            context,
            create_analysis_metric_bundle(level={"sample_peak_dbfs": -3.0}),
            metadata={"path": r"C:\Users\North\Secret\Session\mix.wav", "take": "A"},
        )
        self.assertIn("<private-path>", str(result.metadata["path"]))
        self.assertIn("mix.wav", str(result.metadata["path"]))
        self.assertNotIn(r"C:\Users\North", str(result.metadata["path"]))
        self.assertEqual(result.metadata["take"], "A")

    def test_result_to_dict_is_serializable(self) -> None:
        context = create_analysis_context("analyze", "File Analysis", confidence="Medium", freshness="recent")
        result = create_analysis_result(
            context,
            create_analysis_metric_bundle(stereo=SyntheticMetric(value=0.75, unit="correlation")),
            metadata={"session": "synthetic"},
        )
        payload = analysis_result_to_dict(result)
        encoded = json.dumps(payload, sort_keys=True)
        self.assertIn('"availability": "ready"', encoded)
        self.assertEqual(payload["context"]["source_label"], "File Analysis")

    def test_no_fake_negative_999_values_appear(self) -> None:
        with self.assertRaises(ValueError):
            create_analysis_metric_bundle(level={"sample_peak_dbfs": -999})

    def test_no_advice_text_appears(self) -> None:
        context = create_analysis_context("analyze", "File Analysis")
        result = create_analysis_result(
            context,
            create_analysis_metric_bundle(level={"sample_peak_dbfs": -3.0}),
        )
        payload_text = json.dumps(analysis_result_to_dict(result)).lower()
        forbidden = ("you should", "try ", "fix ", "recommend", "advice")
        self.assertFalse(any(phrase in payload_text for phrase in forbidden))

    def test_no_canned_phrases_appear(self) -> None:
        context = create_analysis_context("compare", "Compare A/B")
        result = create_analysis_result(
            context,
            create_analysis_metric_bundle(compare={"delta": 1.5, "available": True}),
        )
        payload_text = json.dumps(analysis_result_to_dict(result)).lower()
        forbidden = ("your mix", "next practical move", "too loud", "smashed", "make it sound")
        self.assertFalse(any(phrase in payload_text for phrase in forbidden))
