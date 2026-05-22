import unittest

from ai_engine.adapters.base import AIAdapterStatus, AIAdapterType, AIInterpretationResult


CANNED_ADVICE = ("your mix is too loud", "you should", "add saturation", "better mix")


class ResponseContractTests(unittest.TestCase):
    def test_ai_interpretation_result_supports_required_fields(self):
        result = AIInterpretationResult(
            adapter_name="NoAIAdapter",
            adapter_type=AIAdapterType.NO_AI,
            status=AIAdapterStatus.NO_AI_CONFIGURED,
            response_text="",
            mode="analyze",
            source_label="File Analysis",
            used_metric_families=("level",),
            facts_referenced=("level.sample_peak_dbfs",),
            limitations=("AI interpretation is unavailable.",),
            warnings=("short analysis window",),
            fallback_reason="No AI adapter is configured.",
            latency_ms=None,
            raw_response_available=False,
        )

        self.assertEqual(result.adapter_name, "NoAIAdapter")
        self.assertEqual(result.facts_referenced, ("level.sample_peak_dbfs",))
        self.assertEqual(result.source_label, "File Analysis")

    def test_status_enum_supports_required_statuses(self):
        statuses = {status.value for status in AIAdapterStatus}

        self.assertEqual(
            statuses,
            {"ready", "limited", "unavailable", "timeout", "error", "no_ai_configured"},
        )

    def test_ready_status_can_be_represented(self):
        result = AIInterpretationResult("test", AIAdapterType.OPENAI, AIAdapterStatus.READY)

        self.assertEqual(result.status, AIAdapterStatus.READY)

    def test_no_ai_configured_status_can_be_represented(self):
        result = AIInterpretationResult("test", AIAdapterType.NO_AI, AIAdapterStatus.NO_AI_CONFIGURED)

        self.assertEqual(result.status, AIAdapterStatus.NO_AI_CONFIGURED)

    def test_fallback_reason_can_be_represented(self):
        result = AIInterpretationResult(
            "test",
            AIAdapterType.NO_AI,
            AIAdapterStatus.NO_AI_CONFIGURED,
            fallback_reason="No AI adapter is configured.",
        )

        self.assertEqual(result.fallback_reason, "No AI adapter is configured.")

    def test_used_metric_families_can_be_represented(self):
        result = AIInterpretationResult("test", AIAdapterType.LOCAL, AIAdapterStatus.LIMITED, used_metric_families=("stereo",))

        self.assertEqual(result.used_metric_families, ("stereo",))

    def test_limitations_and_warnings_can_be_represented(self):
        result = AIInterpretationResult(
            "test",
            AIAdapterType.LOCAL,
            AIAdapterStatus.LIMITED,
            limitations=("limited packet",),
            warnings=("stale snapshot",),
        )

        self.assertEqual(result.limitations, ("limited packet",))
        self.assertEqual(result.warnings, ("stale snapshot",))

    def test_raw_response_availability_flag_can_be_represented(self):
        result = AIInterpretationResult("test", AIAdapterType.OPENAI, AIAdapterStatus.READY, raw_response_available=True)

        self.assertTrue(result.raw_response_available)

    def test_result_does_not_require_raw_provider_response(self):
        result = AIInterpretationResult("test", AIAdapterType.NO_AI, AIAdapterStatus.NO_AI_CONFIGURED)

        self.assertFalse(result.raw_response_available)

    def test_result_repr_does_not_contain_fake_minus_999(self):
        result = AIInterpretationResult("test", AIAdapterType.NO_AI, AIAdapterStatus.NO_AI_CONFIGURED)

        self.assertNotIn("-999", repr(result))

    def test_result_repr_does_not_contain_canned_advice_phrases(self):
        result = AIInterpretationResult("test", AIAdapterType.NO_AI, AIAdapterStatus.NO_AI_CONFIGURED)
        result_text = repr(result).lower()

        self.assertFalse(any(phrase in result_text for phrase in CANNED_ADVICE))


if __name__ == "__main__":
    unittest.main()
