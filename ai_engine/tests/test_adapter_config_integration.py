import sys
import unittest
from dataclasses import asdict, is_dataclass

from ai_engine.adapters.base import AIAdapterStatus, AIAdapterType
from ai_engine.adapters.local_adapter import LocalAIAdapter
from ai_engine.adapters.no_ai_adapter import NoAIAdapter
from ai_engine.adapters.openai_adapter import OpenAIAdapter
from ai_engine.adapters.router import AdapterRouter
from ai_engine.config.adapter_config import AIAdapterConfig, PreferredAdapter
from ai_engine.config.local_config import (
    LocalAdapterSettings,
    LocalConfigStatus,
    LocalProviderType,
    check_local_config,
    create_default_lm_studio_settings,
    create_default_ollama_settings,
    safe_local_config_summary,
)
from ai_engine.config.openai_config import (
    OpenAIAdapterSettings,
    OpenAIConfigStatus,
    check_openai_config,
    safe_openai_config_summary,
)


FAKE_KEY = "sk-test-config-integration-value"
CREDENTIAL_ENDPOINT = "http://user:pass@127.0.0.1:11434"
ADVICE_TEXT = ("you should", "add saturation", "boost", "cut", "fix your mix", "your mix is too loud")
PROVIDER_MODULES = ("openai", "requests", "httpx", "aiohttp", "ollama")


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


def private_path_packet():
    packet = sample_packet()
    packet["source_label"] = r"C:\Users\North\Private Mixes\song.wav"
    packet["warnings"] = [r"Rendered from C:\Users\North\Private Mixes\song.wav"]
    packet["limitations"] = ["AI unavailable for this test."]
    return packet


def flatten_text(value):
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


class AdapterConfigIntegrationTests(unittest.TestCase):
    def test_openai_config_can_use_injected_fake_key_without_exposing_it(self):
        settings = OpenAIAdapterSettings(enabled=True, model="gpt-test-model")
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})
        summary_text = flatten_text(safe_openai_config_summary(check))

        self.assertEqual(check.status, OpenAIConfigStatus.READY)
        self.assertTrue(check.api_key_present)
        self.assertNotIn(FAKE_KEY, summary_text)

    def test_local_ollama_config_can_be_checked_without_calling_endpoint(self):
        settings = create_default_ollama_settings()
        settings = LocalAdapterSettings(
            enabled=True,
            provider=settings.provider,
            model="llama-test",
            endpoint=settings.endpoint,
        )
        check = check_local_config(settings)

        self.assertEqual(check.status, LocalConfigStatus.READY)
        self.assertEqual(check.provider, LocalProviderType.OLLAMA)

    def test_local_lm_studio_config_can_be_checked_without_calling_endpoint(self):
        settings = create_default_lm_studio_settings()
        settings = LocalAdapterSettings(
            enabled=True,
            provider=settings.provider,
            model="local-test-model",
            endpoint=settings.endpoint,
        )
        check = check_local_config(settings)

        self.assertEqual(check.status, LocalConfigStatus.READY)
        self.assertEqual(check.provider, LocalProviderType.LM_STUDIO)

    def test_router_falls_back_to_no_ai_when_provider_implementations_unavailable(self):
        config = AIAdapterConfig(
            openai_enabled=True,
            local_enabled=True,
            openai_settings=OpenAIAdapterSettings(enabled=True, model="gpt-test-model"),
            local_settings=LocalAdapterSettings(enabled=True, model="llama-test"),
        )
        adapter = AdapterRouter(config).select_adapter()

        self.assertIsInstance(adapter, NoAIAdapter)

    def test_router_does_not_become_ready_when_configs_are_structurally_ready(self):
        config = AIAdapterConfig(
            openai_enabled=True,
            local_enabled=True,
            openai_settings=OpenAIAdapterSettings(enabled=True, model="gpt-test-model"),
            local_settings=LocalAdapterSettings(enabled=True, model="llama-test"),
        )
        result = AdapterRouter(config).interpret(sample_packet())

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertNotEqual(result.status, AIAdapterStatus.READY)

    def test_router_does_not_require_real_api_key(self):
        config = AIAdapterConfig(
            openai_enabled=True,
            openai_settings=OpenAIAdapterSettings(
                enabled=True,
                api_key_env_var="AIFRED_TEST_KEY_NAME_ONLY",
            ),
        )
        result = AdapterRouter(config).interpret(sample_packet())

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)

    def test_router_does_not_require_real_local_endpoint_connection(self):
        config = AIAdapterConfig(
            local_enabled=True,
            local_settings=LocalAdapterSettings(
                enabled=True,
                model="llama-test",
                endpoint="http://127.0.0.1:11434",
            ),
        )
        result = AdapterRouter(config).interpret(sample_packet())

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)

    def test_router_does_not_call_network(self):
        result = AdapterRouter(AIAdapterConfig(openai_enabled=True, local_enabled=True)).interpret(sample_packet())

        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertFalse(result.raw_response_available)
        self.assertIn("No AI adapter is configured", result.fallback_reason)

    def test_safe_openai_summary_does_not_include_secret_value(self):
        check = check_openai_config(
            OpenAIAdapterSettings(enabled=True),
            environ={"OPENAI_API_KEY": FAKE_KEY},
        )
        summary_text = flatten_text(safe_openai_config_summary(check))

        self.assertNotIn(FAKE_KEY, summary_text)

    def test_safe_local_summary_does_not_include_endpoint_credentials(self):
        settings = LocalAdapterSettings(enabled=True, model="llama-test", endpoint=CREDENTIAL_ENDPOINT)
        summary_text = flatten_text(safe_local_config_summary(check_local_config(settings)))

        self.assertNotIn("user:pass", summary_text)
        self.assertNotIn(CREDENTIAL_ENDPOINT, summary_text)

    def test_credential_embedded_local_endpoint_is_rejected(self):
        check = check_local_config(
            LocalAdapterSettings(enabled=True, model="llama-test", endpoint=CREDENTIAL_ENDPOINT)
        )

        self.assertEqual(check.status, LocalConfigStatus.INVALID_CONFIG)

    def test_disabled_openai_config_does_not_require_key(self):
        check = check_openai_config(OpenAIAdapterSettings(enabled=False), environ={})

        self.assertEqual(check.status, OpenAIConfigStatus.DISABLED)

    def test_disabled_local_config_does_not_require_endpoint_or_model(self):
        check = check_local_config(LocalAdapterSettings(enabled=False, model="", endpoint=""))

        self.assertEqual(check.status, LocalConfigStatus.DISABLED)

    def test_invalid_timeout_fails_safely_for_openai_and_local_configs(self):
        openai_check = check_openai_config(
            OpenAIAdapterSettings(enabled=True, timeout_seconds=0),
            environ={"OPENAI_API_KEY": FAKE_KEY},
        )
        local_check = check_local_config(LocalAdapterSettings(enabled=True, model="llama-test", timeout_seconds=0))

        self.assertEqual(openai_check.status, OpenAIConfigStatus.INVALID_CONFIG)
        self.assertEqual(local_check.status, LocalConfigStatus.INVALID_CONFIG)

    def test_empty_model_fails_safely_when_enabled(self):
        openai_check = check_openai_config(
            OpenAIAdapterSettings(enabled=True, model=" "),
            environ={"OPENAI_API_KEY": FAKE_KEY},
        )
        local_check = check_local_config(LocalAdapterSettings(enabled=True, model=" "))

        self.assertEqual(openai_check.status, OpenAIConfigStatus.INVALID_CONFIG)
        self.assertEqual(local_check.status, LocalConfigStatus.MISSING_MODEL)

    def test_auto_mode_returns_no_ai_fallback_when_provider_adapters_unavailable(self):
        adapter = AdapterRouter(AIAdapterConfig(preferred_adapter=PreferredAdapter.AUTO)).select_adapter()

        self.assertIsInstance(adapter, NoAIAdapter)

    def test_preferred_no_ai_returns_no_ai_fallback(self):
        adapter = AdapterRouter(AIAdapterConfig(preferred_adapter=PreferredAdapter.NO_AI)).select_adapter()

        self.assertIsInstance(adapter, NoAIAdapter)

    def test_disabled_no_ai_fallback_returns_structured_unavailable_result(self):
        result = AdapterRouter(AIAdapterConfig(no_ai_fallback_enabled=False)).interpret(sample_packet())

        self.assertEqual(result.status, AIAdapterStatus.UNAVAILABLE)
        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertIn("No AI adapter is available.", result.limitations)

    def test_no_ai_fallback_result_contains_status_only_text_not_advice(self):
        result = AdapterRouter(AIAdapterConfig()).interpret(sample_packet())
        result_text = flatten_text(result).lower()

        self.assertEqual(
            result.response_text,
            "AI interpretation is unavailable. Factual metrics and reports remain available.",
        )
        self.assertFalse(any(phrase in result_text for phrase in ADVICE_TEXT))

    def test_no_ai_fallback_does_not_expose_private_paths(self):
        result_text = flatten_text(AdapterRouter(AIAdapterConfig()).interpret(private_path_packet()))

        self.assertNotIn(r"C:\Users\North", result_text)
        self.assertNotIn(r"C:\Users\North\Private Mixes\song.wav", result_text)

    def test_no_ai_fallback_does_not_contain_fake_minus_999(self):
        packet = sample_packet()
        packet["warnings"] = ["placeholder -999 should be unavailable"]
        result_text = flatten_text(AdapterRouter(AIAdapterConfig()).interpret(packet))

        self.assertNotIn("-999", result_text)

    def test_openai_adapter_remains_stub_unavailable(self):
        capability = OpenAIAdapter().get_capability()
        result = OpenAIAdapter().interpret(sample_packet())

        self.assertFalse(capability.available)
        self.assertEqual(result.status, AIAdapterStatus.UNAVAILABLE)

    def test_local_adapter_remains_stub_unavailable(self):
        capability = LocalAIAdapter().get_capability()
        result = LocalAIAdapter().interpret(sample_packet())

        self.assertFalse(capability.available)
        self.assertEqual(result.status, AIAdapterStatus.UNAVAILABLE)

    def test_no_openai_sdk_or_provider_http_modules_are_required(self):
        loaded_modules = set(sys.modules)

        self.assertFalse(any(module in loaded_modules for module in PROVIDER_MODULES))

    def test_no_environment_secret_value_is_returned(self):
        config = AIAdapterConfig(
            openai_settings=OpenAIAdapterSettings(enabled=True, api_key_env_var="AIFRED_TEST_KEY_NAME_ONLY"),
            local_settings=LocalAdapterSettings(enabled=True, model="llama-test", endpoint=CREDENTIAL_ENDPOINT),
        )
        openai_summary = safe_openai_config_summary(
            check_openai_config(config.openai_settings, environ={"AIFRED_TEST_KEY_NAME_ONLY": FAKE_KEY})
        )
        local_summary = safe_local_config_summary(check_local_config(config.local_settings))
        router_result = AdapterRouter(config).interpret(sample_packet())
        combined_text = flatten_text((openai_summary, local_summary, router_result))

        self.assertNotIn(FAKE_KEY, combined_text)
        self.assertNotIn("user:pass", combined_text)
        self.assertNotIn("AIFRED_TEST_KEY_NAME_ONLY", flatten_text(router_result))


if __name__ == "__main__":
    unittest.main()
