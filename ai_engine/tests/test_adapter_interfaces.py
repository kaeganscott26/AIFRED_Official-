import unittest

from ai_engine.adapters.base import AIAdapterCapability, AIAdapterStatus, AIAdapterType, AIInterpretationResult
from ai_engine.adapters.local_adapter import LocalAIAdapter
from ai_engine.adapters.openai_adapter import OpenAIAdapter


class AdapterInterfaceTests(unittest.TestCase):
    def test_result_dataclass_can_be_created(self):
        result = AIInterpretationResult(
            adapter_name="test",
            adapter_type=AIAdapterType.NO_AI,
            status=AIAdapterStatus.NO_AI_CONFIGURED,
            used_metric_families=("level",),
        )

        self.assertEqual(result.adapter_name, "test")
        self.assertEqual(result.adapter_type, AIAdapterType.NO_AI)
        self.assertEqual(result.status, AIAdapterStatus.NO_AI_CONFIGURED)
        self.assertEqual(result.used_metric_families, ("level",))

    def test_capability_dataclass_can_be_created(self):
        capability = AIAdapterCapability(
            adapter_name="test",
            adapter_type=AIAdapterType.OPENAI,
            available=False,
            reason="not implemented",
            requires_api_key=True,
        )

        self.assertFalse(capability.available)
        self.assertTrue(capability.requires_api_key)
        self.assertEqual(capability.adapter_type, AIAdapterType.OPENAI)

    def test_adapter_status_enum_contains_expected_statuses(self):
        statuses = {status.value for status in AIAdapterStatus}

        self.assertIn("ready", statuses)
        self.assertIn("limited", statuses)
        self.assertIn("unavailable", statuses)
        self.assertIn("timeout", statuses)
        self.assertIn("error", statuses)
        self.assertIn("no_ai_configured", statuses)

    def test_adapter_type_enum_contains_expected_types(self):
        types = {adapter_type.value for adapter_type in AIAdapterType}

        self.assertEqual(types, {"openai", "local", "no_ai"})

    def test_openai_adapter_does_not_call_provider_and_is_unavailable(self):
        adapter = OpenAIAdapter()
        capability = adapter.get_capability()
        result = adapter.interpret({"mode": "analyze", "source_label": "File Analysis"})

        self.assertFalse(capability.available)
        self.assertTrue(capability.requires_api_key)
        self.assertIn(result.status, {AIAdapterStatus.UNAVAILABLE, AIAdapterStatus.LIMITED})
        self.assertEqual(result.raw_response_available, False)

    def test_local_adapter_does_not_call_provider_and_is_unavailable(self):
        adapter = LocalAIAdapter()
        capability = adapter.get_capability()
        result = adapter.interpret({"mode": "analyze", "source_label": "File Analysis"})

        self.assertFalse(capability.available)
        self.assertTrue(capability.supports_local)
        self.assertIn(result.status, {AIAdapterStatus.UNAVAILABLE, AIAdapterStatus.LIMITED})
        self.assertEqual(result.raw_response_available, False)


if __name__ == "__main__":
    unittest.main()
