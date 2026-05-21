"""Tests for factual interpretation packet assembly."""

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
)
from aifred_brain.interpretation_packet import (  # noqa: E402
    PacketAvailability,
    create_interpretation_packet,
    create_metric_fact,
    determine_packet_availability,
    packet_to_dict,
    sanitize_packet_metadata,
)
from aifred_brain.metric_relevance import MetricFamily, UserIntentCategory, select_relevant_metric_families  # noqa: E402


def _context():
    return create_analysis_state(
        mode=AnalysisMode.ANALYZE,
        source_label=SourceLabel.FILE_ANALYSIS,
        confidence=ConfidenceState.HIGH,
        freshness=DataFreshness.RECENT,
    )


def _relevance():
    return select_relevant_metric_families(UserIntentCategory.MASTERING, mode="analyze")


class InterpretationPacketFoundationTests(unittest.TestCase):
    def test_creates_metric_fact_with_factual_fields(self) -> None:
        fact = create_metric_fact(MetricFamily.LEVEL, "sample_peak", 0.5, unit="linear")
        self.assertEqual(fact.family, MetricFamily.LEVEL)
        self.assertEqual(fact.name, "sample_peak")
        self.assertEqual(fact.value, 0.5)
        self.assertEqual(fact.unit, "linear")
        self.assertTrue(fact.available)
        self.assertEqual(fact.limitations, ())

    def test_unavailable_metric_fact_is_represented_honestly(self) -> None:
        fact = create_metric_fact(MetricFamily.LOUDNESS, "integrated_lufs", None, unit="LUFS", available=False, limitations=("not implemented",))
        self.assertFalse(fact.available)
        self.assertIsNone(fact.value)
        self.assertEqual(fact.limitations, ("not implemented",))

    def test_packet_can_be_created_from_analysis_context_and_relevance_result(self) -> None:
        fact = create_metric_fact(MetricFamily.LEVEL, "sample_peak", 0.5)
        packet = create_interpretation_packet("Check levels", _context(), _relevance(), facts=(fact,))
        self.assertEqual(packet.question, "Check levels")
        self.assertEqual(packet.facts, (fact,))

    def test_packet_preserves_active_mode(self) -> None:
        packet = create_interpretation_packet("Check", _context(), _relevance())
        self.assertEqual(packet.mode, "analyze")

    def test_packet_preserves_source_label(self) -> None:
        packet = create_interpretation_packet("Check", _context(), _relevance())
        self.assertEqual(packet.source_label, "File Analysis")

    def test_packet_preserves_confidence_and_freshness(self) -> None:
        packet = create_interpretation_packet("Check", _context(), _relevance())
        self.assertEqual(packet.confidence, "High")
        self.assertEqual(packet.freshness, "recent")

    def test_packet_includes_selected_metric_families(self) -> None:
        packet = create_interpretation_packet("Check", _context(), _relevance())
        self.assertIn(MetricFamily.LEVEL, packet.metric_families)
        self.assertIn(MetricFamily.LOUDNESS, packet.metric_families)
        self.assertIn(MetricFamily.DYNAMICS, packet.metric_families)

    def test_packet_with_available_facts_becomes_ready(self) -> None:
        fact = create_metric_fact(MetricFamily.LEVEL, "sample_peak", 0.5)
        packet = create_interpretation_packet("Check", _context(), _relevance(), facts=(fact,))
        self.assertEqual(packet.availability, PacketAvailability.READY)

    def test_packet_with_no_facts_becomes_unavailable_or_limited(self) -> None:
        packet = create_interpretation_packet("Check", _context(), _relevance())
        self.assertIn(packet.availability, (PacketAvailability.UNAVAILABLE, PacketAvailability.LIMITED))
        self.assertEqual(packet.availability, determine_packet_availability(()))

    def test_limitations_affect_availability(self) -> None:
        fact = create_metric_fact(MetricFamily.LEVEL, "sample_peak", 0.5)
        packet = create_interpretation_packet("Check", _context(), _relevance(), facts=(fact,), limitations=("short capture",))
        self.assertEqual(packet.availability, PacketAvailability.LIMITED)
        self.assertEqual(packet.limitations, ("short capture",))

    def test_warnings_are_preserved(self) -> None:
        packet = create_interpretation_packet("Check", _context(), _relevance(), warnings=("stale snapshot",))
        self.assertEqual(packet.warnings, ("stale snapshot",))

    def test_metadata_is_privacy_sanitized(self) -> None:
        metadata = sanitize_packet_metadata({"file_path": r"C:\Users\North\Secret\Session.wav"})
        self.assertNotIn(r"C:\Users\North\Secret", metadata["file_path"])
        self.assertIn("Session.wav", metadata["file_path"])

    def test_local_paths_are_redacted_or_reduced_to_safe_display(self) -> None:
        packet = create_interpretation_packet(
            "Check",
            _context(),
            _relevance(),
            metadata={"path": r"C:\Users\North\Music\Private\Mix.wav"},
        )
        self.assertNotIn(r"C:\Users\North\Music\Private", packet.metadata["path"])
        self.assertIn("Mix.wav", packet.metadata["path"])

    def test_packet_to_dict_returns_serializable_structure(self) -> None:
        fact = create_metric_fact(MetricFamily.LEVEL, "sample_peak", 0.5, unit="linear")
        packet_dict = packet_to_dict(create_interpretation_packet("Check", _context(), _relevance(), facts=(fact,)))
        self.assertEqual(packet_dict["mode"], "analyze")
        self.assertEqual(packet_dict["availability"], "ready")
        self.assertEqual(packet_dict["metric_families"][0], "level")
        self.assertEqual(packet_dict["facts"][0]["family"], "level")

    def test_no_fake_minus_999_values_appear(self) -> None:
        with self.assertRaises(ValueError):
            create_metric_fact(MetricFamily.LEVEL, "placeholder", -999)
        fact = create_metric_fact(MetricFamily.LEVEL, "sample_peak", 0.5)
        packet_dict = packet_to_dict(create_interpretation_packet("Check", _context(), _relevance(), facts=(fact,)))
        self.assertNotIn(-999, packet_dict.values())
        self.assertNotIn(-999, packet_dict["facts"][0].values())

    def test_no_advice_text_appears(self) -> None:
        text = repr(create_interpretation_packet("Check", _context(), _relevance())).lower()
        for word in ("advice", "recommend", "fix", "should", "try"):
            self.assertNotIn(word, text)

    def test_no_canned_phrases_appear(self) -> None:
        text = repr(create_interpretation_packet("Check", _context(), _relevance())).lower()
        for phrase in ("your mix", "next move", "tradeoff", "make it", "sounds like"):
            self.assertNotIn(phrase, text)


class FutureInterpretationPacketTests(unittest.TestCase):
    @unittest.skip("Future phase only; AI response generation is not implemented yet.")
    def test_ai_response_generation_is_separate_from_packet_assembly(self) -> None:
        """Future test: packet assembly must remain separate from interpretation."""
