import unittest
from dataclasses import asdict, is_dataclass

from ai_engine.prompts.prompt_builder import (
    build_local_prompt,
    build_openai_prompt,
    build_prompt_context,
    build_prompt_sections,
    extract_prompt_packet_context,
    prompt_context_to_dict,
)


CANNED_PHRASES = ("your mix is too loud", "you should", "add saturation", "better mix")


def sample_packet():
    return {
        "question": "Is saturation relevant here?",
        "mode": "analyze",
        "source_label": "File Analysis",
        "confidence": "High",
        "freshness": "recent",
        "availability": "ready",
        "metric_families": ["level", "tonal_balance"],
        "facts": [{"family": "level", "name": "sample_peak_dbfs", "value": -6.0, "available": True}],
        "limitations": ["short analysis window"],
        "warnings": ["synthetic packet"],
        "metadata": {
            "path": r"C:\Users\North\Private Session\mix.wav",
            "unix_path": "/Users/North/Private Session/mix.wav",
            "api_key": "sk-test-secret",
        },
    }


def flatten_text(value):
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


class PromptContractTests(unittest.TestCase):
    def test_extracts_packet_question(self):
        context = extract_prompt_packet_context(sample_packet())

        self.assertEqual(context["question"], "Is saturation relevant here?")

    def test_extracts_packet_mode(self):
        context = extract_prompt_packet_context(sample_packet())

        self.assertEqual(context["mode"], "analyze")

    def test_extracts_source_label(self):
        context = extract_prompt_packet_context(sample_packet())

        self.assertEqual(context["source_label"], "File Analysis")

    def test_extracts_selected_metric_families(self):
        context = extract_prompt_packet_context(sample_packet())

        self.assertEqual(context["selected_metric_families"], ("level", "tonal_balance"))

    def test_extracts_facts(self):
        context = extract_prompt_packet_context(sample_packet())

        self.assertEqual(context["facts"][0]["name"], "sample_peak_dbfs")
        self.assertEqual(context["facts"][0]["value"], -6.0)

    def test_preserves_limitations(self):
        result = build_prompt_context(sample_packet())

        self.assertEqual(result.limitations, ("short analysis window",))

    def test_preserves_warnings(self):
        result = build_prompt_context(sample_packet())

        self.assertEqual(result.warnings, ("synthetic packet",))

    def test_handles_missing_packet_fields_gracefully(self):
        context = extract_prompt_packet_context({"mode": "analyze"})

        self.assertEqual(context["mode"], "analyze")
        self.assertIn("question", context["missing_fields"])

    def test_does_not_expose_local_private_paths(self):
        context_text = flatten_text(extract_prompt_packet_context(sample_packet()))

        self.assertNotIn(r"C:\Users\North\Private Session", context_text)
        self.assertNotIn(r"C:\Users\North", context_text)

    def test_does_not_expose_unix_style_local_paths(self):
        context_text = flatten_text(extract_prompt_packet_context(sample_packet()))

        self.assertNotIn("/Users/North/Private Session", context_text)
        self.assertNotIn("/Users/North", context_text)

    def test_does_not_include_secrets(self):
        context_text = flatten_text(extract_prompt_packet_context(sample_packet()))

        self.assertNotIn("sk-test-secret", context_text)
        self.assertNotIn("api_key", context_text)

    def test_does_not_generate_final_response_text(self):
        result = build_prompt_context(sample_packet())

        self.assertFalse(hasattr(result, "response_text"))

    def test_openai_prompt_builder_stub_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            build_openai_prompt(sample_packet())

    def test_local_prompt_builder_stub_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            build_local_prompt(sample_packet())

    def test_no_canned_phrases_appear(self):
        context_text = flatten_text(build_prompt_context(sample_packet())).lower()

        self.assertFalse(any(phrase in context_text for phrase in CANNED_PHRASES))

    def test_builds_model_neutral_prompt_sections(self):
        sections = build_prompt_sections(sample_packet())
        section_names = {section.name for section in sections}

        self.assertIn("system_constraints", section_names)
        self.assertIn("packet_identity", section_names)
        self.assertIn("facts", section_names)

    def test_prompt_context_preserves_freshness_and_confidence(self):
        result = build_prompt_context(sample_packet())

        self.assertEqual(result.freshness, "recent")
        self.assertEqual(result.confidence, "High")

    def test_prompt_context_can_be_converted_to_dict(self):
        context_dict = prompt_context_to_dict(build_prompt_context(sample_packet()))

        self.assertEqual(context_dict["user_question"], "Is saturation relevant here?")
        self.assertEqual(context_dict["mode"], "analyze")
        self.assertIn("sections", context_dict)

    def test_prompt_context_dict_contains_no_fake_minus_999(self):
        packet = sample_packet()
        packet["facts"] = [{"family": "level", "name": "placeholder", "value": -999}]
        context_text = flatten_text(prompt_context_to_dict(build_prompt_context(packet)))

        self.assertNotIn("-999", context_text)


if __name__ == "__main__":
    unittest.main()
