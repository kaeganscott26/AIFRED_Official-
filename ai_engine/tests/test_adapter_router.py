import unittest
from dataclasses import asdict, is_dataclass

from ai_engine.adapters.base import AIAdapterStatus, AIAdapterType
from ai_engine.adapters.no_ai_adapter import NoAIAdapter
from ai_engine.adapters.router import AdapterRouter
from ai_engine.config.adapter_config import AIAdapterConfig, PreferredAdapter
from ai_engine.config.local_config import LocalAdapterSettings
from ai_engine.config.openai_config import OpenAIAdapterSettings

ADVICE_TEXT = ("you should", "do this", "add saturation", "boost", "cut", "fix your mix")


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


class AdapterRouterTests(unittest.TestCase):
    def test_auto_config_falls_back_to_no_ai_when_openai_and_local_unavailable(self):
        config = AIAdapterConfig(openai_enabled=True, local_enabled=True, no_ai_fallback_enabled=True)
        router = AdapterRouter(config)
        adapter = router.select_adapter()

        self.assertIsInstance(adapter, NoAIAdapter)

    def test_preferred_no_ai_selects_no_ai(self):
        config = AIAdapterConfig(preferred_adapter=PreferredAdapter.NO_AI, no_ai_fallback_enabled=True)
        router = AdapterRouter(config)

        self.assertIsInstance(router.select_adapter(), NoAIAdapter)

    def test_disabled_no_ai_fallback_returns_structured_unavailable_result(self):
        config = AIAdapterConfig(openai_enabled=False, local_enabled=False, no_ai_fallback_enabled=False)
        result = AdapterRouter(config).interpret(sample_packet())

        self.assertEqual(result.status, AIAdapterStatus.UNAVAILABLE)
        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertIn("No AI adapter is available.", result.limitations)

    def test_router_returns_structured_result(self):
        result = AdapterRouter(AIAdapterConfig()).interpret(sample_packet())

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertIn(result.status, {AIAdapterStatus.NO_AI_CONFIGURED, AIAdapterStatus.LIMITED})
        self.assertEqual(result.raw_response_available, False)

    def test_router_does_not_require_api_key(self):
        config = AIAdapterConfig(api_key_env_var="AIFRED_TEST_KEY_NAME_ONLY")
        result = AdapterRouter(config).interpret(sample_packet())

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)

    def test_router_does_not_expose_fake_injected_key_reference(self):
        config = AIAdapterConfig(
            openai_settings=OpenAIAdapterSettings(
                enabled=True,
                api_key_env_var="AIFRED_TEST_KEY_NAME_ONLY",
            )
        )
        result_text = flatten_text(AdapterRouter(config).interpret(sample_packet()))

        self.assertNotIn("sk-test", result_text)
        self.assertNotIn("AIFRED_TEST_KEY_NAME_ONLY", result_text)

    def test_router_does_not_require_local_endpoint(self):
        config = AIAdapterConfig(local_enabled=True, local_endpoint=None)
        result = AdapterRouter(config).interpret(sample_packet())

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)

    def test_router_does_not_expose_endpoint_credentials(self):
        config = AIAdapterConfig(
            local_settings=LocalAdapterSettings(
                enabled=True,
                model="local-test-model",
                endpoint="http://user:pass@127.0.0.1:11434",
            )
        )
        result_text = flatten_text(AdapterRouter(config).interpret(sample_packet()))

        self.assertNotIn("user:pass", result_text)
        self.assertNotIn("http://user:pass@127.0.0.1:11434", result_text)

    def test_router_does_not_call_network(self):
        config = AIAdapterConfig(openai_enabled=True, local_enabled=True)
        result = AdapterRouter(config).interpret(sample_packet())

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertIn("No AI adapter is configured", result.fallback_reason)

    def test_router_handles_missing_packet_fields_gracefully(self):
        result = AdapterRouter(AIAdapterConfig()).interpret({"mode": "analyze"})

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertEqual(result.status, AIAdapterStatus.LIMITED)
        self.assertTrue(any("Missing packet fields" in item for item in result.limitations))

    def test_router_result_contains_no_advice(self):
        result_text = flatten_text(AdapterRouter(AIAdapterConfig()).interpret(sample_packet())).lower()

        self.assertFalse(any(phrase in result_text for phrase in ADVICE_TEXT))

    def test_router_result_contains_no_fake_minus_999(self):
        result_text = flatten_text(AdapterRouter(AIAdapterConfig()).interpret(sample_packet()))

        self.assertNotIn("-999", result_text)


if __name__ == "__main__":
    unittest.main()
