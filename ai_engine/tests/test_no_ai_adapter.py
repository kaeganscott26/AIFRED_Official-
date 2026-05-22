import unittest
from dataclasses import asdict, is_dataclass

from ai_engine.adapters.base import AIAdapterStatus, AIAdapterType
from ai_engine.adapters.no_ai_adapter import NoAIAdapter


ADVICE_TEXT = ("you should", "do this", "add saturation", "boost", "cut", "fix your mix")
CANNED_ANALYSIS = ("analysis says", "based on your lufs", "better mix", "professional")


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
    def test_no_ai_adapter_reports_capability_correctly(self):
        adapter = NoAIAdapter(fallback_enabled=True)
        capability = adapter.get_capability()

        self.assertTrue(capability.available)
        self.assertEqual(capability.adapter_type, AIAdapterType.NO_AI)
        self.assertFalse(capability.requires_api_key)

    def test_no_ai_interpret_returns_structured_fallback_result(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertIn(result.status, {AIAdapterStatus.NO_AI_CONFIGURED, AIAdapterStatus.LIMITED})
        self.assertEqual(result.raw_response_available, False)
        self.assertTrue(result.fallback_reason)

    def test_no_ai_result_does_not_pretend_to_be_ai_ready(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertNotEqual(result.status, AIAdapterStatus.READY)

    def test_no_ai_result_preserves_mode_and_source_from_packet_like_dict(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertEqual(result.mode, "analyze")
        self.assertEqual(result.source_label, "File Analysis")

    def test_no_ai_result_contains_limitation_about_unavailable_ai_interpretation(self):
        result = NoAIAdapter().interpret(sample_packet())

        self.assertIn("AI interpretation is unavailable.", result.limitations)

    def test_no_ai_result_contains_no_advice_text(self):
        result_text = flatten_text(NoAIAdapter().interpret(sample_packet())).lower()

        self.assertFalse(any(phrase in result_text for phrase in ADVICE_TEXT))

    def test_no_ai_result_contains_no_canned_analysis_phrases(self):
        result_text = flatten_text(NoAIAdapter().interpret(sample_packet())).lower()

        self.assertFalse(any(phrase in result_text for phrase in CANNED_ANALYSIS))

    def test_no_ai_result_contains_no_fake_metrics(self):
        result_text = flatten_text(NoAIAdapter().interpret(sample_packet()))

        self.assertNotIn("-999", result_text)


if __name__ == "__main__":
    unittest.main()
