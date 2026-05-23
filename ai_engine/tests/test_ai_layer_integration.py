import json
import re
import sys
import unittest
from dataclasses import asdict, is_dataclass

from ai_engine.adapters.base import AIAdapterStatus, AIAdapterType, AIInterpretationResult
from ai_engine.adapters.local_adapter import LocalAIAdapter
from ai_engine.adapters.no_ai_adapter import NoAIAdapter
from ai_engine.adapters.openai_adapter import OpenAIAdapter
from ai_engine.adapters.router import AdapterRouter
from ai_engine.config.adapter_config import AIAdapterConfig, PreferredAdapter
from ai_engine.config.local_config import (
    LocalAdapterSettings,
    LocalConfigStatus,
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
from ai_engine.prompts.prompt_builder import (
    build_prompt_context,
    extract_prompt_packet_context,
    prompt_context_to_dict,
)
from ai_engine.response_validation import validate_ai_interpretation_result


FAKE_KEY = "sk-test-ai-layer-integration-value"
FALLBACK_TEXT = "AI interpretation is unavailable. Factual metrics and reports remain available."
PROVIDER_MODULES = ("openai", "requests", "httpx", "aiohttp", "ollama")
ADVICE_TEXT = (
    "your mix is too loud",
    "you should reduce compression",
    "this sounds professional",
    "mix a is better",
    "add saturation",
    "the vocals are harsh",
    "boost",
    "fix your mix",
)
CANNED_DIAGNOSIS_TEXT = (
    "if lufs",
    "say exactly",
    "fixed sentence",
    "generic repeated",
    "metric-threshold",
)
PRIVATE_PATH_PATTERN = re.compile(r"[A-Za-z]:\\|/(?:Users|home|var|tmp|mnt|Volumes)/")


def synthetic_packet():
    return {
        "question": "What is the current balance state?",
        "mode": "analyze",
        "source_label": "File Analysis",
        "confidence": "High",
        "freshness": "recent",
        "availability": "ready",
        "metric_families": ["level", "tonal_balance", "dynamics"],
        "facts": [
            {
                "family": "level",
                "name": "sample_peak_dbfs",
                "value": -6.0,
                "unit": "dBFS",
                "available": True,
                "limitations": [],
            },
            {
                "family": "tonal_balance",
                "name": "low_to_mid_ratio",
                "value": 0.82,
                "unit": None,
                "available": True,
                "limitations": [],
            },
        ],
        "limitations": ["Synthetic packet for AI layer smoke testing."],
        "warnings": ["Synthetic data only; no provider call should occur."],
        "metadata": {
            "render_label": "synthetic_mix.wav",
            "project_label": "AI layer smoke test",
        },
        "session_label": "Smoke Test Session",
    }


def flatten_text(value):
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


def assert_no_fake_minus_999(test_case, value):
    test_case.assertNotIn("-999", flatten_text(value))


def assert_no_private_path(test_case, value):
    text = flatten_text(value)
    test_case.assertIsNone(PRIVATE_PATH_PATTERN.search(text), text)


def assert_no_advice_text(test_case, value):
    text = flatten_text(value).lower()
    test_case.assertFalse(any(phrase in text for phrase in ADVICE_TEXT), text)


def assert_no_canned_diagnosis(test_case, value):
    text = flatten_text(value).lower()
    test_case.assertFalse(any(phrase in text for phrase in CANNED_DIAGNOSIS_TEXT), text)


def assert_json_serializable(test_case, value):
    try:
        json.dumps(value)
    except TypeError as exc:
        test_case.fail(f"Value should be JSON-serializable: {exc}")


def structurally_ready_openai_adapter():
    settings = OpenAIAdapterSettings(enabled=True, model="gpt-test-model")
    return OpenAIAdapter(
        settings,
        config_check=check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY}),
    )


def structurally_ready_local_adapter(settings):
    return LocalAIAdapter(
        settings,
        config_check=check_local_config(settings),
    )


class AILayerIntegrationSmokeTests(unittest.TestCase):
    def test_packet_to_prompt_context_smoke_preserves_safe_packet_structure(self):
        packet = synthetic_packet()

        extracted = extract_prompt_packet_context(packet)
        context = build_prompt_context(packet)
        context_dict = prompt_context_to_dict(context)

        self.assertEqual(extracted["question"], packet["question"])
        self.assertEqual(context.user_question, packet["question"])
        self.assertEqual(context_dict["user_question"], packet["question"])
        self.assertEqual(extracted["mode"], "analyze")
        self.assertEqual(context.mode, "analyze")
        self.assertEqual(context_dict["mode"], "analyze")
        self.assertEqual(extracted["source_label"], "File Analysis")
        self.assertEqual(context.source_label, "File Analysis")
        self.assertEqual(context_dict["source_label"], "File Analysis")
        self.assertEqual(extracted["selected_metric_families"], tuple(packet["metric_families"]))
        self.assertEqual(context.selected_metric_families, tuple(packet["metric_families"]))
        self.assertEqual(context_dict["selected_metric_families"], packet["metric_families"])
        self.assertEqual(extracted["facts"], packet["facts"])
        self.assertEqual(context.packet_context["facts"], packet["facts"])
        self.assertEqual(extracted["limitations"], tuple(packet["limitations"]))
        self.assertEqual(context.limitations, tuple(packet["limitations"]))
        self.assertEqual(extracted["warnings"], tuple(packet["warnings"]))
        self.assertEqual(context.warnings, tuple(packet["warnings"]))
        self.assertEqual(extracted["session_label"], "Smoke Test Session")

        assert_json_serializable(self, context_dict)
        assert_no_private_path(self, (extracted, context_dict))
        assert_no_fake_minus_999(self, (extracted, context_dict))
        assert_no_advice_text(self, (extracted, context_dict))
        assert_no_canned_diagnosis(self, (extracted, context_dict))

    def test_prompt_context_to_no_ai_router_path_smoke(self):
        packet = synthetic_packet()
        config = AIAdapterConfig(
            preferred_adapter=PreferredAdapter.AUTO,
            openai_enabled=False,
            local_enabled=False,
            no_ai_fallback_enabled=True,
        )
        router = AdapterRouter(config)

        selected = router.select_adapter()
        result = router.interpret(packet)

        self.assertIsInstance(selected, NoAIAdapter)
        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertNotEqual(result.status, AIAdapterStatus.READY)
        self.assertIn(result.status, {AIAdapterStatus.NO_AI_CONFIGURED, AIAdapterStatus.LIMITED})
        self.assertEqual(result.response_text, FALLBACK_TEXT)
        self.assertFalse(result.raw_response_available)
        self.assertEqual(result.mode, packet["mode"])
        self.assertEqual(result.source_label, packet["source_label"])
        self.assertEqual(result.used_metric_families, tuple(packet["metric_families"]))
        self.assertTrue(any("AI interpretation is unavailable" in item for item in result.limitations))
        self.assertIn("No AI adapter is configured", result.fallback_reason)
        assert_no_advice_text(self, result)
        assert_no_fake_minus_999(self, result)
        assert_no_private_path(self, result)

    def test_openai_and_local_stubs_remain_non_provider_with_structural_config(self):
        packet = synthetic_packet()
        ollama_defaults = create_default_ollama_settings()
        lm_studio_defaults = create_default_lm_studio_settings()
        adapters = (
            structurally_ready_openai_adapter(),
            structurally_ready_local_adapter(
                LocalAdapterSettings(
                    enabled=True,
                    provider=ollama_defaults.provider,
                    model="llama-test",
                    endpoint=ollama_defaults.endpoint,
                )
            ),
            structurally_ready_local_adapter(
                LocalAdapterSettings(
                    enabled=True,
                    provider=lm_studio_defaults.provider,
                    model="local-test-model",
                    endpoint=lm_studio_defaults.endpoint,
                )
            ),
        )

        for adapter in adapters:
            with self.subTest(adapter=adapter.adapter_name):
                capability = adapter.get_capability()
                result = adapter.interpret(packet)
                combined_text = flatten_text((capability, result))

                self.assertFalse(capability.available)
                self.assertIn(result.status, {AIAdapterStatus.UNAVAILABLE, AIAdapterStatus.LIMITED})
                self.assertNotEqual(result.status, AIAdapterStatus.READY)
                self.assertFalse(result.raw_response_available)
                self.assertIn("provider calls are not implemented", combined_text)
                self.assertFalse(any(module in set(sys.modules) for module in PROVIDER_MODULES))
                assert_no_advice_text(self, (capability, result))
                assert_no_fake_minus_999(self, (capability, result))
                assert_no_private_path(self, (capability, result))

    def test_response_validation_smoke_catches_contract_violations(self):
        packet = synthetic_packet()
        valid_no_ai = AIInterpretationResult(
            adapter_name="NoAIAdapter",
            adapter_type=AIAdapterType.NO_AI,
            status=AIAdapterStatus.NO_AI_CONFIGURED,
            response_text=FALLBACK_TEXT,
            used_metric_families=tuple(packet["metric_families"]),
            source_label=packet["source_label"],
            mode=packet["mode"],
            limitations=("AI interpretation is unavailable.",),
            raw_response_available=False,
        )
        self.assertTrue(validate_ai_interpretation_result(valid_no_ai, packet).is_valid)

        invalid_results = (
            AIInterpretationResult(
                adapter_name="OpenAIAdapter",
                adapter_type=AIAdapterType.OPENAI,
                status=AIAdapterStatus.READY,
                response_text="",
                source_label=packet["source_label"],
                mode=packet["mode"],
            ),
            AIInterpretationResult(
                adapter_name="OpenAIAdapter",
                adapter_type=AIAdapterType.OPENAI,
                status=AIAdapterStatus.READY,
                response_text="Status text only.",
                source_label=packet["source_label"],
                mode="reference",
            ),
            AIInterpretationResult(
                adapter_name="OpenAIAdapter",
                adapter_type=AIAdapterType.OPENAI,
                status=AIAdapterStatus.READY,
                response_text="Status text only.",
                source_label="Live Buffer",
                mode=packet["mode"],
            ),
            AIInterpretationResult(
                adapter_name="OpenAIAdapter",
                adapter_type=AIAdapterType.OPENAI,
                status=AIAdapterStatus.READY,
                response_text="The reference pool indicates a mismatch.",
                source_label=packet["source_label"],
                mode="analyze",
            ),
            AIInterpretationResult(
                adapter_name="OpenAIAdapter",
                adapter_type=AIAdapterType.OPENAI,
                status=AIAdapterStatus.READY,
                response_text="Mix B is a reference here.",
                source_label=packet["source_label"],
                mode="compare",
            ),
            AIInterpretationResult(
                adapter_name="OpenAIAdapter",
                adapter_type=AIAdapterType.OPENAI,
                status=AIAdapterStatus.READY,
                response_text="LUFS is present.",
                source_label=packet["source_label"],
                mode=packet["mode"],
            ),
            AIInterpretationResult(
                adapter_name="OpenAIAdapter",
                adapter_type=AIAdapterType.OPENAI,
                status=AIAdapterStatus.READY,
                response_text="True peak is present.",
                source_label=packet["source_label"],
                mode=packet["mode"],
            ),
            AIInterpretationResult(
                adapter_name="OpenAIAdapter",
                adapter_type=AIAdapterType.OPENAI,
                status=AIAdapterStatus.UNAVAILABLE,
                response_text="",
                source_label=r"C:\Users\North\Private Mixes\song.wav",
                mode=packet["mode"],
            ),
            AIInterpretationResult(
                adapter_name="OpenAIAdapter",
                adapter_type=AIAdapterType.OPENAI,
                status=AIAdapterStatus.UNAVAILABLE,
                response_text="placeholder -999",
                source_label=packet["source_label"],
                mode=packet["mode"],
            ),
        )

        for invalid_result in invalid_results:
            with self.subTest(result=invalid_result):
                self.assertFalse(validate_ai_interpretation_result(invalid_result, packet).is_valid)

    def test_config_boundary_smoke_keeps_stubs_out_of_provider_ready_path(self):
        packet = synthetic_packet()
        openai_settings = OpenAIAdapterSettings(enabled=True, model="gpt-test-model")
        openai_check = check_openai_config(openai_settings, environ={"OPENAI_API_KEY": FAKE_KEY})
        openai_summary = safe_openai_config_summary(openai_check)

        ollama_defaults = create_default_ollama_settings()
        ollama_settings = LocalAdapterSettings(
            enabled=True,
            provider=ollama_defaults.provider,
            model="llama-test",
            endpoint=ollama_defaults.endpoint,
        )
        ollama_check = check_local_config(ollama_settings)
        ollama_summary = safe_local_config_summary(ollama_check)

        lm_studio_defaults = create_default_lm_studio_settings()
        lm_studio_settings = LocalAdapterSettings(
            enabled=True,
            provider=lm_studio_defaults.provider,
            model="local-test-model",
            endpoint=lm_studio_defaults.endpoint,
        )
        lm_studio_check = check_local_config(lm_studio_settings)
        lm_studio_summary = safe_local_config_summary(lm_studio_check)

        config = AIAdapterConfig(
            preferred_adapter=PreferredAdapter.AUTO,
            openai_enabled=True,
            local_enabled=True,
            no_ai_fallback_enabled=True,
            openai_settings=openai_settings,
            local_settings=ollama_settings,
        )
        router = AdapterRouter(
            config,
            openai_adapter=OpenAIAdapter(openai_settings, config_check=openai_check),
            local_adapter=LocalAIAdapter(ollama_settings, config_check=ollama_check),
        )
        selected = router.select_adapter()
        result = router.interpret(packet)

        self.assertEqual(openai_check.status, OpenAIConfigStatus.READY)
        self.assertEqual(ollama_check.status, LocalConfigStatus.READY)
        self.assertEqual(lm_studio_check.status, LocalConfigStatus.READY)
        self.assertNotIn(FAKE_KEY, flatten_text(openai_summary))
        self.assertFalse(any(module in set(sys.modules) for module in PROVIDER_MODULES))
        self.assertIsInstance(selected, NoAIAdapter)
        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertNotEqual(result.status, AIAdapterStatus.READY)
        self.assertEqual(result.response_text, FALLBACK_TEXT)
        assert_no_fake_minus_999(self, (openai_summary, ollama_summary, lm_studio_summary, result))
        assert_no_advice_text(self, (openai_summary, ollama_summary, lm_studio_summary, result))
        assert_no_private_path(self, (openai_summary, ollama_summary, lm_studio_summary, result))


if __name__ == "__main__":
    unittest.main()
