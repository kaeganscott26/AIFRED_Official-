import sys
import unittest
from dataclasses import asdict, is_dataclass

from ai_engine.adapters.base import AIAdapterStatus, AIInterpretationResult
from ai_engine.adapters.local_adapter import LocalAIAdapter
from ai_engine.config.local_config import (
    LocalAdapterSettings,
    LocalProviderType,
    check_local_config,
    create_default_lm_studio_settings,
    create_default_ollama_settings,
)


CREDENTIAL_ENDPOINT = "http://user:pass@127.0.0.1:11434"
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
PROVIDER_MODULES = ("requests", "httpx", "aiohttp", "ollama", "openai")


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


def adapter_for(settings):
    return LocalAIAdapter(
        settings,
        config_check=check_local_config(settings),
    )


class LocalAdapterTests(unittest.TestCase):
    def test_capability_is_unavailable_when_disabled(self):
        adapter = adapter_for(LocalAdapterSettings(enabled=False))
        capability = adapter.get_capability()

        self.assertFalse(capability.available)
        self.assertTrue(capability.supports_local)
        self.assertIn("disabled", capability.reason.lower())

    def test_capability_is_unavailable_when_enabled_but_missing_model(self):
        adapter = adapter_for(LocalAdapterSettings(enabled=True, model="", endpoint="http://127.0.0.1:11434"))
        capability = adapter.get_capability()

        self.assertFalse(capability.available)
        self.assertIn("configuration is incomplete", capability.reason)

    def test_capability_is_unavailable_when_enabled_but_missing_endpoint(self):
        adapter = adapter_for(LocalAdapterSettings(enabled=True, model="llama-test", endpoint=""))
        capability = adapter.get_capability()

        self.assertFalse(capability.available)
        self.assertIn("configuration is incomplete", capability.reason)

    def test_recognizes_valid_structural_ollama_settings_without_calling_endpoint(self):
        defaults = create_default_ollama_settings()
        settings = LocalAdapterSettings(
            enabled=True,
            provider=defaults.provider,
            model="llama-test",
            endpoint=defaults.endpoint,
        )
        adapter = adapter_for(settings)
        capability = adapter.get_capability()
        result = adapter.interpret(sample_packet())

        self.assertFalse(capability.available)
        self.assertIn("configured structurally", capability.reason)
        self.assertIn("provider calls are not implemented", capability.reason)
        self.assertEqual(result.status, AIAdapterStatus.LIMITED)

    def test_recognizes_valid_structural_lm_studio_settings_without_calling_endpoint(self):
        defaults = create_default_lm_studio_settings()
        settings = LocalAdapterSettings(
            enabled=True,
            provider=defaults.provider,
            model="local-test-model",
            endpoint=defaults.endpoint,
        )
        adapter = adapter_for(settings)
        capability = adapter.get_capability()
        result = adapter.interpret(sample_packet())

        self.assertFalse(capability.available)
        self.assertIn("configured structurally", capability.reason)
        self.assertIn("provider calls are not implemented", flatten_text(result))
        self.assertEqual(result.status, AIAdapterStatus.LIMITED)

    def test_adapter_does_not_expose_endpoint_credentials(self):
        adapter = adapter_for(LocalAdapterSettings(enabled=True, model="llama-test", endpoint=CREDENTIAL_ENDPOINT))
        combined_text = flatten_text((adapter.get_capability(), adapter.interpret(sample_packet())))

        self.assertNotIn("user:pass", combined_text)
        self.assertNotIn(CREDENTIAL_ENDPOINT, combined_text)

    def test_adapter_does_not_import_or_require_http_provider_dependencies(self):
        adapter = LocalAIAdapter()
        adapter.get_capability()
        adapter.interpret(sample_packet())

        self.assertFalse(any(module in set(sys.modules) for module in PROVIDER_MODULES))

    def test_adapter_does_not_call_network_or_expose_raw_response(self):
        result = LocalAIAdapter().interpret(sample_packet())

        self.assertFalse(any(module in set(sys.modules) for module in PROVIDER_MODULES))
        self.assertFalse(result.raw_response_available)

    def test_interpret_returns_structured_unavailable_or_limited_result(self):
        result = LocalAIAdapter().interpret(sample_packet())

        self.assertIsInstance(result, AIInterpretationResult)
        self.assertIn(result.status, {AIAdapterStatus.UNAVAILABLE, AIAdapterStatus.LIMITED})
        self.assertFalse(result.raw_response_available)

    def test_interpret_preserves_mode_source_and_metric_families(self):
        settings = LocalAdapterSettings(
            enabled=True,
            provider=LocalProviderType.OLLAMA,
            model="llama-test",
            endpoint="http://127.0.0.1:11434",
        )
        result = adapter_for(settings).interpret(sample_packet())

        self.assertEqual(result.mode, "analyze")
        self.assertEqual(result.source_label, "File Analysis")
        self.assertEqual(result.used_metric_families, ("level", "tonal_balance"))

    def test_structurally_ready_result_says_provider_calls_not_implemented(self):
        settings = LocalAdapterSettings(enabled=True, model="llama-test", endpoint="http://127.0.0.1:11434")
        result = adapter_for(settings).interpret(sample_packet())
        result_text = flatten_text(result)

        self.assertEqual(result.status, AIAdapterStatus.LIMITED)
        self.assertIn("provider calls are not implemented", result_text)

    def test_incomplete_config_result_says_config_incomplete(self):
        result = adapter_for(LocalAdapterSettings(enabled=True, model="", endpoint="")).interpret(sample_packet())
        result_text = flatten_text(result)

        self.assertEqual(result.status, AIAdapterStatus.UNAVAILABLE)
        self.assertIn("configuration is incomplete", result_text)

    def test_result_contains_no_advice_or_subjective_labels(self):
        settings = LocalAdapterSettings(enabled=True, model="llama-test", endpoint="http://127.0.0.1:11434")
        result_text = flatten_text(adapter_for(settings).interpret(sample_packet())).lower()

        self.assertFalse(any(phrase in result_text for phrase in ADVICE_TEXT))
        self.assertFalse(any(phrase in result_text for phrase in SUBJECTIVE_TEXT))

    def test_result_contains_no_fake_minus_999_and_does_not_claim_ready(self):
        packet = sample_packet()
        packet["warnings"] = ["placeholder -999 should stay unavailable"]
        settings = LocalAdapterSettings(enabled=True, model="llama-test", endpoint="http://127.0.0.1:11434")
        result = adapter_for(settings).interpret(packet)
        result_text = flatten_text(result)

        self.assertNotIn("-999", result_text)
        self.assertNotEqual(result.status, AIAdapterStatus.READY)
        self.assertNotIn("READY", result_text)

    def test_result_does_not_expose_private_paths(self):
        packet = sample_packet()
        packet["source_label"] = r"C:\Users\North\Private Mixes\song.wav"
        packet["limitations"] = [r"Rendered from C:\Users\North\Private Mixes\song.wav"]
        result_text = flatten_text(LocalAIAdapter().interpret(packet))

        self.assertNotIn(r"C:\Users\North", result_text)
        self.assertNotIn(r"C:\Users\North\Private Mixes\song.wav", result_text)


if __name__ == "__main__":
    unittest.main()
