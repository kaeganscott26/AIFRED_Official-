import unittest

from ai_engine.config.local_config import (
    LocalAdapterSettings,
    LocalConfigStatus,
    LocalProviderType,
    check_local_config,
    create_default_lm_studio_settings,
    create_default_ollama_settings,
    safe_local_config_summary,
    validate_local_settings,
)


CREDENTIAL_ENDPOINT = "http://user:pass@127.0.0.1:11434"
ADVICE_TEXT = ("your mix is too loud", "you should", "add saturation", "better mix")
CANNED_PHRASES = ("if lufs", "say exactly", "fixed sentence", "generic repeated")


def flatten_text(value):
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


class LocalConfigTests(unittest.TestCase):
    def test_default_ollama_settings_use_local_ollama_endpoint(self):
        settings = create_default_ollama_settings()

        self.assertEqual(settings.provider, LocalProviderType.OLLAMA)
        self.assertEqual(settings.endpoint, "http://127.0.0.1:11434")

    def test_default_lm_studio_settings_use_local_lm_studio_endpoint(self):
        settings = create_default_lm_studio_settings()

        self.assertEqual(settings.provider, LocalProviderType.LM_STUDIO)
        self.assertEqual(settings.endpoint, "http://127.0.0.1:1234/v1")

    def test_disabled_settings_do_not_require_model(self):
        settings = LocalAdapterSettings(enabled=False, model="")
        check = check_local_config(settings)

        self.assertEqual(check.status, LocalConfigStatus.DISABLED)

    def test_disabled_settings_do_not_require_endpoint(self):
        settings = LocalAdapterSettings(enabled=False, endpoint="")
        check = check_local_config(settings)

        self.assertEqual(check.status, LocalConfigStatus.DISABLED)

    def test_enabled_settings_without_model_returns_missing_model(self):
        settings = LocalAdapterSettings(enabled=True, model="", endpoint="http://127.0.0.1:11434")
        check = check_local_config(settings)

        self.assertEqual(check.status, LocalConfigStatus.MISSING_MODEL)

    def test_enabled_settings_without_endpoint_returns_missing_endpoint(self):
        settings = LocalAdapterSettings(enabled=True, model="llama-test", endpoint="")
        check = check_local_config(settings)

        self.assertEqual(check.status, LocalConfigStatus.MISSING_ENDPOINT)

    def test_enabled_valid_ollama_settings_returns_ready(self):
        settings = LocalAdapterSettings(
            enabled=True,
            provider=LocalProviderType.OLLAMA,
            model="llama-test",
            endpoint="http://127.0.0.1:11434",
        )
        check = check_local_config(settings)

        self.assertEqual(check.status, LocalConfigStatus.READY)

    def test_enabled_valid_lm_studio_settings_returns_ready(self):
        settings = LocalAdapterSettings(
            enabled=True,
            provider=LocalProviderType.LM_STUDIO,
            model="local-test-model",
            endpoint="http://127.0.0.1:1234/v1",
        )
        check = check_local_config(settings)

        self.assertEqual(check.status, LocalConfigStatus.READY)

    def test_invalid_timeout_is_rejected(self):
        settings = LocalAdapterSettings(enabled=True, model="llama-test", timeout_seconds=0)
        issues = validate_local_settings(settings)
        check = check_local_config(settings)

        self.assertTrue(any("timeout_seconds" in issue for issue in issues))
        self.assertEqual(check.status, LocalConfigStatus.INVALID_CONFIG)

    def test_credential_embedded_endpoint_is_rejected(self):
        settings = LocalAdapterSettings(
            enabled=True,
            model="llama-test",
            endpoint=CREDENTIAL_ENDPOINT,
        )
        issues = validate_local_settings(settings)
        check = check_local_config(settings)

        self.assertTrue(any("credentials" in issue for issue in issues))
        self.assertEqual(check.status, LocalConfigStatus.INVALID_CONFIG)

    def test_safe_summary_includes_provider_model_and_status(self):
        settings = LocalAdapterSettings(
            enabled=True,
            provider=LocalProviderType.OLLAMA,
            model="llama-test",
            endpoint="http://127.0.0.1:11434",
        )
        summary = safe_local_config_summary(check_local_config(settings))

        self.assertEqual(summary["provider"], "ollama")
        self.assertEqual(summary["model"], "llama-test")
        self.assertEqual(summary["status"], "ready")

    def test_safe_summary_does_not_include_credentials(self):
        settings = LocalAdapterSettings(
            enabled=True,
            model="llama-test",
            endpoint=CREDENTIAL_ENDPOINT,
        )
        summary_text = flatten_text(safe_local_config_summary(check_local_config(settings)))

        self.assertNotIn("user:pass", summary_text)
        self.assertNotIn(CREDENTIAL_ENDPOINT, summary_text)

    def test_custom_provider_can_reference_explicit_custom_endpoint(self):
        settings = LocalAdapterSettings(
            enabled=True,
            provider=LocalProviderType.CUSTOM,
            model="local-test-model",
            endpoint="http://local-ai.internal:8080/v1",
        )
        check = check_local_config(settings)

        self.assertEqual(check.status, LocalConfigStatus.READY)

    def test_non_custom_provider_rejects_non_local_endpoint(self):
        settings = LocalAdapterSettings(
            enabled=True,
            provider=LocalProviderType.OLLAMA,
            model="llama-test",
            endpoint="http://local-ai.internal:11434",
        )
        check = check_local_config(settings)

        self.assertEqual(check.status, LocalConfigStatus.INVALID_CONFIG)

    def test_no_fake_minus_999(self):
        settings = LocalAdapterSettings(enabled=True, model="llama-test")
        summary_text = flatten_text(safe_local_config_summary(check_local_config(settings)))

        self.assertNotIn("-999", summary_text)

    def test_no_advice_text(self):
        settings = LocalAdapterSettings(enabled=True, model="llama-test")
        summary_text = flatten_text(safe_local_config_summary(check_local_config(settings))).lower()

        self.assertFalse(any(phrase in summary_text for phrase in ADVICE_TEXT))

    def test_no_canned_phrases(self):
        settings = LocalAdapterSettings(enabled=True, model="llama-test")
        summary_text = flatten_text(safe_local_config_summary(check_local_config(settings))).lower()

        self.assertFalse(any(phrase in summary_text for phrase in CANNED_PHRASES))


if __name__ == "__main__":
    unittest.main()
