import unittest

from ai_engine.config.openai_config import (
    OpenAIAdapterSettings,
    OpenAIConfigStatus,
    check_openai_config,
    create_default_openai_settings,
    mask_secret_presence,
    safe_openai_config_summary,
    validate_openai_settings,
)


FAKE_KEY = "sk-test-config-boundary-value"
ADVICE_TEXT = ("your mix is too loud", "you should", "add saturation", "better mix")
CANNED_PHRASES = ("if lufs", "say exactly", "fixed sentence", "generic repeated")


def flatten_text(value):
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


class OpenAIConfigTests(unittest.TestCase):
    def test_default_settings_use_openai_api_key_env_var_name(self):
        settings = create_default_openai_settings()

        self.assertEqual(settings.api_key_env_var, "OPENAI_API_KEY")

    def test_disabled_settings_do_not_require_key(self):
        settings = OpenAIAdapterSettings(enabled=False)
        check = check_openai_config(settings, environ={})

        self.assertEqual(check.status, OpenAIConfigStatus.DISABLED)
        self.assertFalse(check.api_key_present)

    def test_enabled_settings_without_key_returns_missing_api_key(self):
        settings = OpenAIAdapterSettings(enabled=True)
        check = check_openai_config(settings, environ={})

        self.assertEqual(check.status, OpenAIConfigStatus.MISSING_API_KEY)
        self.assertFalse(check.api_key_present)

    def test_enabled_settings_with_injected_fake_key_returns_ready(self):
        settings = OpenAIAdapterSettings(enabled=True)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})

        self.assertEqual(check.status, OpenAIConfigStatus.READY)
        self.assertTrue(check.api_key_present)

    def test_fake_key_value_is_never_present_in_safe_summary(self):
        settings = OpenAIAdapterSettings(enabled=True)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})
        summary_text = flatten_text(safe_openai_config_summary(check))

        self.assertNotIn(FAKE_KEY, summary_text)

    def test_key_presence_is_boolean_only(self):
        settings = OpenAIAdapterSettings(enabled=True)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})
        summary = safe_openai_config_summary(check)

        self.assertIsInstance(summary["api_key_present"], bool)

    def test_empty_key_counts_as_missing(self):
        settings = OpenAIAdapterSettings(enabled=True)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": ""})

        self.assertEqual(check.status, OpenAIConfigStatus.MISSING_API_KEY)

    def test_whitespace_key_counts_as_missing(self):
        settings = OpenAIAdapterSettings(enabled=True)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": "   "})

        self.assertEqual(check.status, OpenAIConfigStatus.MISSING_API_KEY)

    def test_invalid_timeout_is_rejected(self):
        settings = OpenAIAdapterSettings(enabled=True, timeout_seconds=0)
        issues = validate_openai_settings(settings)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})

        self.assertTrue(any("timeout_seconds" in issue for issue in issues))
        self.assertEqual(check.status, OpenAIConfigStatus.INVALID_CONFIG)

    def test_empty_model_is_rejected_when_enabled(self):
        settings = OpenAIAdapterSettings(enabled=True, model=" ")
        issues = validate_openai_settings(settings)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})

        self.assertTrue(any("model" in issue for issue in issues))
        self.assertEqual(check.status, OpenAIConfigStatus.INVALID_CONFIG)

    def test_safe_summary_includes_model_and_status(self):
        settings = OpenAIAdapterSettings(enabled=True, model="gpt-test-model")
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})
        summary = safe_openai_config_summary(check)

        self.assertEqual(summary["model"], "gpt-test-model")
        self.assertEqual(summary["status"], "ready")

    def test_safe_summary_does_not_include_secrets(self):
        settings = OpenAIAdapterSettings(enabled=True)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})
        summary = safe_openai_config_summary(check)
        summary_text = flatten_text(summary)

        self.assertNotIn(FAKE_KEY, summary_text)
        self.assertNotIn("sk-test-config-boundary-value", summary_text)

    def test_no_fake_minus_999(self):
        settings = OpenAIAdapterSettings(enabled=True)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})
        summary_text = flatten_text(safe_openai_config_summary(check))

        self.assertNotIn("-999", summary_text)

    def test_no_advice_text(self):
        settings = OpenAIAdapterSettings(enabled=True)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})
        summary_text = flatten_text(safe_openai_config_summary(check)).lower()

        self.assertFalse(any(phrase in summary_text for phrase in ADVICE_TEXT))

    def test_no_canned_phrases(self):
        settings = OpenAIAdapterSettings(enabled=True)
        check = check_openai_config(settings, environ={"OPENAI_API_KEY": FAKE_KEY})
        summary_text = flatten_text(safe_openai_config_summary(check)).lower()

        self.assertFalse(any(phrase in summary_text for phrase in CANNED_PHRASES))

    def test_mask_secret_presence_uses_boolean_only(self):
        self.assertTrue(mask_secret_presence(FAKE_KEY))
        self.assertFalse(mask_secret_presence(""))
        self.assertFalse(mask_secret_presence(None))


if __name__ == "__main__":
    unittest.main()
