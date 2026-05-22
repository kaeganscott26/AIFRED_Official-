import unittest
from dataclasses import asdict, is_dataclass

from ai_engine.adapters.base import AIAdapterStatus, AIAdapterType, AIInterpretationResult
from ai_engine.prompts.prompt_builder import build_prompt_context, prompt_context_to_dict
from ai_engine.response_validation import validate_ai_interpretation_result


FALLBACK_TEXT = "AI interpretation is unavailable. Factual metrics and reports remain available."
CANNED_DIAGNOSIS_PHRASES = ("your mix is too loud", "this sounds professional", "the vocals are harsh")


def synthetic_packet(**overrides):
    packet = {
        "question": "Is saturation relevant here?",
        "mode": "analyze",
        "source_label": "File Analysis",
        "confidence": "high",
        "freshness": "current",
        "availability": "ready",
        "metric_families": ("level", "tonal_balance"),
        "facts": (
            {"family": "level", "name": "sample_peak_dbfs", "value": -1.0, "unit": "dBFS", "available": True},
            {"family": "tonal_balance", "name": "low_mid_ratio", "value": 0.25, "available": True},
        ),
        "limitations": (),
        "warnings": (),
        "metadata": {
            "source_path": r"C:\Users\North\Private Session\mix.wav",
            "unix_path": "/Users/North/Private Session/mix.wav",
            "api_key": "sk-test-secret",
        },
    }
    packet.update(overrides)
    return packet


def flatten_text(value):
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


def ready_response(context, **overrides):
    base = {
        "adapter_name": "SyntheticAdapter",
        "adapter_type": AIAdapterType.OPENAI,
        "status": AIAdapterStatus.READY,
        "response_text": "Selected packet facts were interpreted.",
        "used_metric_families": tuple(context.selected_metric_families),
        "facts_referenced": ("sample_peak_dbfs",),
        "source_label": context.source_label,
        "mode": context.mode,
        "limitations": context.limitations,
        "warnings": context.warnings,
        "raw_response_available": False,
    }
    base.update(overrides)
    return AIInterpretationResult(**base)


class PromptResponseGuardrailTests(unittest.TestCase):
    def test_prompt_context_built_from_packet_can_support_response_validation(self):
        packet = synthetic_packet()
        context = build_prompt_context(packet)
        response = ready_response(context)

        validation = validate_ai_interpretation_result(response, packet)

        self.assertTrue(validation.is_valid)

    def test_prompt_context_includes_mode_source_and_facts_needed_for_alignment(self):
        context = build_prompt_context(synthetic_packet())
        context_dict = prompt_context_to_dict(context)

        self.assertEqual(context_dict["mode"], "analyze")
        self.assertEqual(context_dict["source_label"], "File Analysis")
        self.assertIn("facts", context_dict["packet_context"])

    def test_generated_test_response_with_matching_mode_and_source_validates(self):
        packet = synthetic_packet()
        context = build_prompt_context(packet)

        validation = validate_ai_interpretation_result(ready_response(context), packet)

        self.assertTrue(validation.is_valid)

    def test_generated_test_response_with_mismatched_mode_fails_validation(self):
        packet = synthetic_packet()
        context = build_prompt_context(packet)

        validation = validate_ai_interpretation_result(ready_response(context, mode="reference"), packet)

        self.assertFalse(validation.is_valid)
        self.assertIn("mode_mismatch", {issue.code for issue in validation.issues})

    def test_generated_test_response_with_mismatched_source_fails_validation(self):
        packet = synthetic_packet()
        context = build_prompt_context(packet)

        validation = validate_ai_interpretation_result(ready_response(context, source_label="Live Buffer"), packet)

        self.assertFalse(validation.is_valid)
        self.assertIn("source_mismatch", {issue.code for issue in validation.issues})

    def test_analyze_mode_response_mentioning_reference_pool_fails_validation(self):
        packet = synthetic_packet(mode="analyze")
        context = build_prompt_context(packet)

        validation = validate_ai_interpretation_result(
            ready_response(context, response_text="The reference pool indicates a target difference."),
            packet,
        )

        self.assertFalse(validation.is_valid)
        self.assertIn("analyze_reference_pool_leak", {issue.code for issue in validation.issues})

    def test_compare_mode_response_calling_b_a_reference_fails_validation(self):
        packet = synthetic_packet(mode="compare", source_label="Compare A/B")
        context = build_prompt_context(packet)

        validation = validate_ai_interpretation_result(
            ready_response(context, response_text="Mix B is a reference for this comparison."),
            packet,
        )

        self.assertFalse(validation.is_valid)
        self.assertIn("compare_b_reference_leak", {issue.code for issue in validation.issues})

    def test_response_claiming_lufs_without_lufs_fact_fails_validation(self):
        packet = synthetic_packet()
        context = build_prompt_context(packet)

        validation = validate_ai_interpretation_result(
            ready_response(context, response_text="LUFS is referenced in this response."),
            packet,
        )

        self.assertFalse(validation.is_valid)
        self.assertIn("missing_lufs_fact", {issue.code for issue in validation.issues})

    def test_response_claiming_true_peak_without_true_peak_fact_fails_validation(self):
        packet = synthetic_packet()
        context = build_prompt_context(packet)

        validation = validate_ai_interpretation_result(
            ready_response(context, response_text="True peak is referenced in this response."),
            packet,
        )

        self.assertFalse(validation.is_valid)
        self.assertIn("missing_true_peak_fact", {issue.code for issue in validation.issues})

    def test_no_ai_status_only_response_passes_validation(self):
        packet = synthetic_packet()
        context = build_prompt_context(packet)
        response = AIInterpretationResult(
            adapter_name="NoAIAdapter",
            adapter_type=AIAdapterType.NO_AI,
            status=AIAdapterStatus.NO_AI_CONFIGURED,
            response_text=FALLBACK_TEXT,
            source_label=context.source_label,
            mode=context.mode,
            limitations=("AI interpretation is unavailable.",),
            raw_response_available=False,
        )

        validation = validate_ai_interpretation_result(response, packet)

        self.assertTrue(validation.is_valid)

    def test_no_ai_status_only_response_fails_if_it_contains_advice(self):
        packet = synthetic_packet()
        context = build_prompt_context(packet)
        response = AIInterpretationResult(
            adapter_name="NoAIAdapter",
            adapter_type=AIAdapterType.NO_AI,
            status=AIAdapterStatus.NO_AI_CONFIGURED,
            response_text="You should reduce compression.",
            source_label=context.source_label,
            mode=context.mode,
        )

        validation = validate_ai_interpretation_result(response, packet)

        self.assertFalse(validation.is_valid)
        self.assertIn("forbidden_advice_text", {issue.code for issue in validation.issues})

    def test_prompt_context_contains_no_fake_minus_999(self):
        packet = synthetic_packet(facts=({"family": "level", "name": "placeholder", "value": -999},))
        context_text = flatten_text(prompt_context_to_dict(build_prompt_context(packet)))

        self.assertNotIn("-999", context_text)

    def test_prompt_context_contains_no_private_paths(self):
        context_text = flatten_text(prompt_context_to_dict(build_prompt_context(synthetic_packet())))

        self.assertNotIn(r"C:\Users\North", context_text)
        self.assertNotIn("/Users/North", context_text)
        self.assertNotIn("sk-test-secret", context_text)

    def test_prompt_context_contains_no_canned_diagnosis_phrase(self):
        context_text = flatten_text(prompt_context_to_dict(build_prompt_context(synthetic_packet()))).lower()

        self.assertFalse(any(phrase in context_text for phrase in CANNED_DIAGNOSIS_PHRASES))


if __name__ == "__main__":
    unittest.main()
