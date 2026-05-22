import unittest
from dataclasses import asdict, is_dataclass
from types import SimpleNamespace

from ai_engine.adapters.base import AIAdapterStatus, AIAdapterType
from ai_engine.adapters.no_ai_adapter import NoAIAdapter


ADVICE_TEXT = ("you should", "do this", "add saturation", "boost", "cut", "fix your mix")
CANNED_ANALYSIS = ("analysis says", "based on your lufs", "better mix", "professional")
SUBJECTIVE_LABELS = ("too loud", "harsh", "sounds professional", "mix a is better", "vocals are harsh")


def sample_packet():
    return {
        "question": "Should I add saturation?",
        "mode": "analyze",
        "source_label": "File Analysis",
        "confidence": "High",
        "freshness": "recent",
        "availability": "ready",
        "metric_families": ["level", "tonal_balance"],
        "facts": [{"family": "level", "name": "sample_peak_dbfs", "value": -6.0, "available": True}],
        "limitations": [],
        "warnings": [],
        "metadata": {"input": "safe.wav"},
        "session_label": "safe",
    }


def flatten_text(value):
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


class NoAIAdapterTests(unittest.TestCase):
    def test_fallback_enabled_capability_is_available(self):
        adapter = NoAIAdapter(fallback_enabled=True)
        capability = adapter.get_capability()

        self.assertTrue(capability.available)
        self.assertEqual(capability.adapter_type, AIAdapterType.NO_AI)
        self.assertFalse(capability.requires_api_key)

    def test_fallback_disabled_capability_is_unavailable(self):
        adapter = NoAIAdapter(fallback_enabled=False)
        capability = adapter.get_capability()

        self.assertFalse(capability.available)
        self.assertEqual(capability.reason, "No-AI fallback is disabled.")

    def test_no_ai_interpret_returns_structured_fallback_result(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertIn(result.status, {AIAdapterStatus.NO_AI_CONFIGURED, AIAdapterStatus.LIMITED})
        self.assertEqual(result.raw_response_available, False)
        self.assertTrue(result.fallback_reason)

    def test_no_ai_result_does_not_pretend_to_be_ai_ready(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertNotEqual(result.status, AIAdapterStatus.READY)

    def test_interpret_preserves_mode_from_dict_packet(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertEqual(result.mode, "analyze")

    def test_interpret_preserves_source_label_from_dict_packet(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertEqual(result.source_label, "File Analysis")

    def test_interpret_preserves_selected_metric_families(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertEqual(result.used_metric_families, ("level", "tonal_balance"))

    def test_interpret_preserves_warnings(self):
        packet = sample_packet()
        packet["warnings"] = ["short analysis window"]
        result = NoAIAdapter().interpret(packet)

        self.assertEqual(result.warnings, ("short analysis window",))

    def test_interpret_preserves_limitations_and_adds_ai_unavailable_limitation(self):
        packet = sample_packet()
        packet["limitations"] = ["short analysis window"]
        result = NoAIAdapter().interpret(packet)

        self.assertIn("short analysis window", result.limitations)
        self.assertIn("AI interpretation is unavailable.", result.limitations)

    def test_interpret_handles_missing_packet_fields_gracefully(self):
        result = NoAIAdapter().interpret({"mode": "analyze"})

        self.assertEqual(result.status, AIAdapterStatus.LIMITED)
        self.assertEqual(result.mode, "analyze")
        self.assertTrue(any("Missing packet fields" in item for item in result.limitations))

    def test_interpret_handles_dataclass_like_packet_objects(self):
        packet = SimpleNamespace(**sample_packet())
        result = NoAIAdapter().interpret(packet)

        self.assertEqual(result.mode, "analyze")
        self.assertEqual(result.source_label, "File Analysis")
        self.assertEqual(result.used_metric_families, ("level", "tonal_balance"))

    def test_disabled_fallback_interpret_returns_unavailable(self):
        result = NoAIAdapter(fallback_enabled=False).interpret(sample_packet())

        self.assertEqual(result.status, AIAdapterStatus.UNAVAILABLE)
        self.assertEqual(result.response_text, "")
        self.assertIn("No-AI fallback is disabled.", result.limitations)

    def test_no_ai_result_contains_limitation_about_unavailable_ai_interpretation(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertIn("AI interpretation is unavailable.", result.limitations)

    def test_response_text_is_status_only(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertEqual(
            result.response_text,
            "AI interpretation is unavailable. Factual metrics and reports remain available.",
        )

    def test_no_ai_result_contains_no_advice_text(self):
        result_text = flatten_text(NoAIAdapter().interpret(sample_packet())).lower()

        self.assertFalse(any(phrase in result_text for phrase in ADVICE_TEXT))

    def test_no_ai_result_contains_no_canned_analysis_phrases(self):
        result_text = flatten_text(NoAIAdapter().interpret(sample_packet())).lower()

        self.assertFalse(any(phrase in result_text for phrase in CANNED_ANALYSIS))

    def test_no_ai_result_contains_no_subjective_labels(self):
        result_text = flatten_text(NoAIAdapter().interpret(sample_packet())).lower()

        self.assertFalse(any(phrase in result_text for phrase in SUBJECTIVE_LABELS))

    def test_no_ai_result_contains_no_fake_metrics(self):
        result_text = flatten_text(NoAIAdapter().interpret(sample_packet()))

        self.assertNotIn("-999", result_text)

    def test_local_private_paths_are_not_exposed(self):
        packet = sample_packet()
        packet["source_label"] = r"C:\Users\North\Secret Session\mix.wav"
        packet["warnings"] = [r"Loaded from C:\Users\North\Secret Session\mix.wav"]
        packet["limitations"] = ["/Users/north/private/mix.wav unavailable"]
        result_text = flatten_text(NoAIAdapter().interpret(packet))

        self.assertNotIn(r"C:\Users\North\Secret Session", result_text)
        self.assertNotIn("/Users/north/private", result_text)
        self.assertIn("[redacted path]/mix.wav", result_text)


if __name__ == "__main__":
    unittest.main()
