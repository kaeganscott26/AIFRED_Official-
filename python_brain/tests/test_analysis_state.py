"""Tests for `aifred_brain.analysis_state`.

- Analyze, Reference, and Compare mode separation
- source-of-truth labels
- confidence labels
- stale/waiting/unavailable distinctions
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.analysis_state import (  # noqa: E402
    AnalysisMode,
    ConfidenceState,
    DataFreshness,
    SourceLabel,
    create_analysis_state,
    mark_state_stale,
)


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
