import unittest

from ai_engine.adapters.base import AIAdapterStatus, AIAdapterType, AIInterpretationResult
from ai_engine.response_validation import (
    AIResponseValidationSeverity,
    detect_fake_metric_values,
    detect_private_path_leak,
    validate_ai_interpretation_result,
)


FALLBACK_TEXT = "AI interpretation is unavailable. Factual metrics and reports remain available."


def packet(**overrides):
    base = {
        "question": "Is this ready for review?",
        "mode": "analyze",
        "source_label": "File Analysis",
        "confidence": "high",
        "freshness": "current",
        "availability": "ready",
        "metric_families": ("level",),
        "facts": ({"family": "level", "name": "sample_peak_dbfs", "value": -1.0, "available": True},),
        "limitations": (),
        "warnings": (),
        "metadata": {},
    }
    base.update(overrides)
    return base


def ready_result(**overrides):
    base = {
        "adapter_name": "TestAdapter",
        "adapter_type": AIAdapterType.OPENAI,
        "status": AIAdapterStatus.READY,
        "response_text": "Selected packet facts were interpreted.",
        "used_metric_families": ("level",),
        "facts_referenced": ("sample_peak_dbfs",),
        "source_label": "File Analysis",
        "mode": "analyze",
        "limitations": (),
        "warnings": (),
        "raw_response_available": False,
    }
    base.update(overrides)
    return AIInterpretationResult(**base)


class ResponseValidationTests(unittest.TestCase):
    def test_valid_ready_result_passes_when_structure_is_aligned(self):
        validation = validate_ai_interpretation_result(ready_result(), packet())

        self.assertTrue(validation.is_valid)
        self.assertEqual(validation.error_count, 0)

    def test_ready_result_with_empty_response_text_fails(self):
        validation = validate_ai_interpretation_result(ready_result(response_text=""), packet())

        self.assertFalse(validation.is_valid)
        self.assertIn("ready_requires_text", {issue.code for issue in validation.issues})

    def test_no_ai_configured_result_with_status_only_text_passes(self):
        result = AIInterpretationResult(
            adapter_name="NoAIAdapter",
            adapter_type=AIAdapterType.NO_AI,
            status=AIAdapterStatus.NO_AI_CONFIGURED,
            response_text=FALLBACK_TEXT,
            source_label="File Analysis",
            mode="analyze",
            limitations=("AI interpretation is unavailable.",),
        )

        validation = validate_ai_interpretation_result(result, packet())

        self.assertTrue(validation.is_valid)

    def test_no_ai_configured_result_with_advice_text_fails(self):
        result = AIInterpretationResult(
            adapter_name="NoAIAdapter",
            adapter_type=AIAdapterType.NO_AI,
            status=AIAdapterStatus.NO_AI_CONFIGURED,
            response_text="You should reduce compression.",
            source_label="File Analysis",
            mode="analyze",
        )

        validation = validate_ai_interpretation_result(result, packet())

        self.assertFalse(validation.is_valid)
        self.assertIn("forbidden_advice_text", {issue.code for issue in validation.issues})

    def test_timeout_result_does_not_pretend_to_be_ready(self):
        result = ready_result(
            status=AIAdapterStatus.TIMEOUT,
            response_text="Based on your mix, the stereo field was interpreted.",
        )

        validation = validate_ai_interpretation_result(result, packet())

        self.assertFalse(validation.is_valid)
        self.assertIn("failure_pretends_ready", {issue.code for issue in validation.issues})

    def test_error_result_does_not_pretend_to_be_ready(self):
        result = ready_result(
            status=AIAdapterStatus.ERROR,
            response_text="Based on your mix, the level facts were interpreted.",
        )

        validation = validate_ai_interpretation_result(result, packet())

        self.assertFalse(validation.is_valid)
        self.assertIn("failure_pretends_ready", {issue.code for issue in validation.issues})

    def test_fake_minus_999_is_detected(self):
        issues = detect_fake_metric_values({"facts": [{"value": -999}]})

        self.assertTrue(any(issue.code == "fake_metric_value" for issue in issues))

    def test_private_windows_style_local_path_is_detected(self):
        issues = detect_private_path_leak({"text": r"C:\Users\North\Documents\Projects\private.wav"})

        self.assertTrue(any(issue.code == "private_path_leak" for issue in issues))

    def test_private_unix_style_local_path_is_detected(self):
        issues = detect_private_path_leak({"text": "/Users/North/Documents/private.wav"})

        self.assertTrue(any(issue.code == "private_path_leak" for issue in issues))

    def test_mode_mismatch_between_packet_and_result_is_detected(self):
        validation = validate_ai_interpretation_result(ready_result(mode="reference"), packet(mode="analyze"))

        self.assertFalse(validation.is_valid)
        self.assertIn("mode_mismatch", {issue.code for issue in validation.issues})

    def test_source_mismatch_between_packet_and_result_is_detected(self):
        validation = validate_ai_interpretation_result(ready_result(source_label="Live Buffer"), packet(source_label="File Analysis"))

        self.assertFalse(validation.is_valid)
        self.assertIn("source_mismatch", {issue.code for issue in validation.issues})

    def test_analyze_mode_reference_pool_leakage_is_detected(self):
        validation = validate_ai_interpretation_result(
            ready_result(response_text="The reference pool indicates a different target."),
            packet(mode="analyze"),
        )

        self.assertFalse(validation.is_valid)
        self.assertIn("analyze_reference_pool_leak", {issue.code for issue in validation.issues})

    def test_compare_mode_b_is_reference_leakage_is_detected(self):
        validation = validate_ai_interpretation_result(
            ready_result(mode="compare", response_text="Mix B is a reference for this comparison."),
            packet(mode="compare"),
        )

        self.assertFalse(validation.is_valid)
        self.assertIn("compare_b_reference_leak", {issue.code for issue in validation.issues})

    def test_true_peak_claim_without_true_peak_fact_is_detected(self):
        validation = validate_ai_interpretation_result(
            ready_result(response_text="True peak is present in the response."),
            packet(facts=({"family": "level", "name": "sample_peak_dbfs", "value": -1.0},)),
        )

        self.assertFalse(validation.is_valid)
        self.assertIn("missing_true_peak_fact", {issue.code for issue in validation.issues})

    def test_lufs_claim_without_lufs_fact_is_detected(self):
        validation = validate_ai_interpretation_result(
            ready_result(response_text="LUFS is present in the response."),
            packet(facts=({"family": "level", "name": "rms_dbfs", "value": -18.0},)),
        )

        self.assertFalse(validation.is_valid)
        self.assertIn("missing_lufs_fact", {issue.code for issue in validation.issues})

    def test_limitations_and_warnings_structure_is_accepted(self):
        validation = validate_ai_interpretation_result(
            ready_result(limitations=("limited packet",), warnings=("short window",)),
            packet(limitations=("limited packet",), warnings=("short window",)),
        )

        self.assertTrue(validation.is_valid)

    def test_validation_result_counts_errors_and_warnings_correctly(self):
        result = ready_result(response_text="", mode=None, source_label=None)
        validation = validate_ai_interpretation_result(result, packet())

        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.error_count, 1)
        self.assertEqual(validation.warning_count, 2)
        self.assertTrue(all(issue.severity in AIResponseValidationSeverity for issue in validation.issues))


if __name__ == "__main__":
    unittest.main()
