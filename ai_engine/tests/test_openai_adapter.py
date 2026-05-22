import sys
import unittest
from dataclasses import asdict, is_dataclass

from ai_engine.adapters.base import AIAdapterStatus, AIInterpretationResult
from ai_engine.adapters.openai_adapter import OpenAIAdapter
from ai_engine.config.openai_config import OpenAIAdapterSettings, check_openai_config


FAKE_KEY = "sk-test-openai-adapter-value"
ADVICE_TEXT = (
    "your mix is too loud",
    "you should reduce compression",
    "add saturation",
    "you should",
)
SUBJECTIVE_TEXT = (
    "this sounds professional",
    "mix a is better",
    "the vocals are harsh",
)
PROVIDER_MODULES = ("openai", "requests", "httpx", "aiohttp")


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
    }


def flatten_text(value):
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


def adapter_for(settings, environ):
    return OpenAIAdapter(
        settings,
        config_check=check_openai_config(settings, environ=environ),
    )


class OpenAIAdapterTests(unittest.TestCase):
    def test_capability_is_unavailable_when_disabled(self):
        adapter = adapter_for(OpenAIAdapterSettings(enabled=False), {})
        capability = adapter.get_capability()

        self.assertFalse(capability.available)
        self.assertTrue(capability.requires_api_key)
        self.assertIn("disabled", capability.reason.lower())

    def test_capability_is_unavailable_when_enabled_but_missing_key(self):
        adapter = adapter_for(OpenAIAdapterSettings(enabled=True), {})
        capability = adapter.get_capability()

        self.assertFalse(capability.available)
        self.assertTrue(capability.requires_api_key)
        self.assertIn("configuration is incomplete", capability.reason)

    def test_structurally_ready_capability_remains_stub_not_provider_ready(self):
        settings = OpenAIAdapterSettings(enabled=True)
        adapter = adapter_for(settings, {"OPENAI_API_KEY": FAKE_KEY})
        capability = adapter.get_capability()

        self.assertFalse(capability.available)
        self.assertIn("configured structurally", capability.reason)
        self.assertIn("provider calls are not implemented", capability.reason)

    def test_adapter_does_not_expose_fake_injected_key(self):
        settings = OpenAIAdapterSettings(enabled=True)
        adapter = adapter_for(settings, {"OPENAI_API_KEY": FAKE_KEY})
        combined_text = flatten_text((adapter.get_capability(), adapter.interpret(sample_packet())))

        self.assertNotIn(FAKE_KEY, combined_text)
        self.assertNotIn("sk-test-openai-adapter-value", combined_text)

    def test_adapter_does_not_import_or_require_openai_sdk(self):
        adapter = OpenAIAdapter()
        adapter.get_capability()
        adapter.interpret(sample_packet())

        self.assertNotIn("openai", set(sys.modules))

    def test_adapter_does_not_call_network_or_provider_modules(self):
        adapter = OpenAIAdapter()
        result = adapter.interpret(sample_packet())

        self.assertFalse(any(module in set(sys.modules) for module in PROVIDER_MODULES))
        self.assertFalse(result.raw_response_available)

    def test_interpret_returns_structured_unavailable_or_limited_result(self):
        result = OpenAIAdapter().interpret(sample_packet())

        self.assertIsInstance(result, AIInterpretationResult)
        self.assertIn(result.status, {AIAdapterStatus.UNAVAILABLE, AIAdapterStatus.LIMITED})
        self.assertFalse(result.raw_response_available)

    def test_interpret_preserves_mode_source_and_metric_families(self):
        settings = OpenAIAdapterSettings(enabled=True)
        result = adapter_for(settings, {"OPENAI_API_KEY": FAKE_KEY}).interpret(sample_packet())

        self.assertEqual(result.mode, "analyze")
        self.assertEqual(result.source_label, "File Analysis")
        self.assertEqual(result.used_metric_families, ("level", "tonal_balance"))

    def test_structurally_ready_result_says_provider_calls_not_implemented(self):
        settings = OpenAIAdapterSettings(enabled=True)
        result = adapter_for(settings, {"OPENAI_API_KEY": FAKE_KEY}).interpret(sample_packet())
        result_text = flatten_text(result)

        self.assertEqual(result.status, AIAdapterStatus.LIMITED)
        self.assertIn("provider calls are not implemented", result_text)

    def test_incomplete_config_result_says_config_incomplete(self):
        result = adapter_for(OpenAIAdapterSettings(enabled=True), {}).interpret(sample_packet())
        result_text = flatten_text(result)

        self.assertEqual(result.status, AIAdapterStatus.UNAVAILABLE)
        self.assertIn("configuration is incomplete", result_text)

    def test_result_contains_no_advice_or_subjective_labels(self):
        settings = OpenAIAdapterSettings(enabled=True)
        result_text = flatten_text(adapter_for(settings, {"OPENAI_API_KEY": FAKE_KEY}).interpret(sample_packet())).lower()

        self.assertFalse(any(phrase in result_text for phrase in ADVICE_TEXT))
        self.assertFalse(any(phrase in result_text for phrase in SUBJECTIVE_TEXT))

    def test_result_contains_no_fake_minus_999_and_does_not_claim_ready(self):
        packet = sample_packet()
        packet["warnings"] = ["placeholder -999 should stay unavailable"]
        settings = OpenAIAdapterSettings(enabled=True)
        result = adapter_for(settings, {"OPENAI_API_KEY": FAKE_KEY}).interpret(packet)
        result_text = flatten_text(result)

        self.assertNotIn("-999", result_text)
        self.assertNotEqual(result.status, AIAdapterStatus.READY)
        self.assertNotIn("READY", result_text)

    def test_result_does_not_expose_private_paths(self):
        packet = sample_packet()
        packet["source_label"] = r"C:\Users\North\Private Mixes\song.wav"
        packet["limitations"] = [r"Rendered from C:\Users\North\Private Mixes\song.wav"]
        result_text = flatten_text(OpenAIAdapter().interpret(packet))

        self.assertNotIn(r"C:\Users\North", result_text)
        self.assertNotIn(r"C:\Users\North\Private Mixes\song.wav", result_text)


if __name__ == "__main__":
    unittest.main()
