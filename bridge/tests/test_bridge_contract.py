import json
import unittest

from bridge.bridge_contract import (
    BridgeAIStatus,
    BridgeAnalysisStatus,
    BridgeInputRef,
    BridgeLens,
    BridgeMode,
    BridgeReportRef,
    BridgeReportStatus,
    BridgeStatus,
    bridge_request_from_dict,
    bridge_request_to_dict,
    bridge_response_from_dict,
    bridge_response_to_dict,
    create_bridge_request,
    create_bridge_response,
    sanitize_bridge_dict,
    validate_bridge_request_shape,
    validate_bridge_response_shape,
)


def input_ref(ref_id="input-a", label="mix.wav"):
    return BridgeInputRef(
        ref_id=ref_id,
        kind="audio_snapshot",
        safe_label=label,
        internal_ref=f"Z:\\Private\\Audio\\{label}",
        metadata={"source_path": f"/Users/example/private/{label}"},
    )


class BridgeRequestContractTests(unittest.TestCase):
    def test_create_analyze_request_with_one_audio_input(self):
        request = create_bridge_request(
            request_id="req-001",
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="File Analysis",
            audio_input_ref=input_ref(),
        )

        self.assertEqual(request.audio_input_ref.ref_id, "input-a")
        self.assertEqual(validate_bridge_request_shape(request), ())

    def test_create_compare_request_with_audio_input_and_comparison_input(self):
        request = create_bridge_request(
            request_id="req-compare",
            mode=BridgeMode.COMPARE,
            lens=BridgeLens.WIDTH,
            source_label="Compare A/B",
            audio_input_ref=input_ref("mix-a", "mix-a.wav"),
            comparison_input_ref=input_ref("mix-b", "mix-b.wav"),
        )

        self.assertEqual(request.comparison_input_ref.ref_id, "mix-b")
        self.assertEqual(validate_bridge_request_shape(request), ())

    def test_create_reference_request_with_audio_input_and_reference_input(self):
        request = create_bridge_request(
            request_id="req-reference",
            mode=BridgeMode.REFERENCE,
            lens=BridgeLens.LOUDNESS,
            source_label="Reference Mode",
            audio_input_ref=input_ref("current", "current.wav"),
            reference_input_ref=input_ref("target", "target.wav"),
        )

        self.assertEqual(request.reference_input_ref.safe_label, "target.wav")
        self.assertEqual(validate_bridge_request_shape(request), ())

    def test_request_preserves_mode_lens_metrics_question_timeout_and_reports_flag(self):
        request = create_bridge_request(
            request_id="req-fields",
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.PUNCH,
            source_label="File Analysis",
            audio_input_ref=input_ref(),
            question="What changed?",
            requested_metric_families=("dynamics", "transients"),
            timeout_ms=2500,
            write_reports=True,
        )

        self.assertEqual(request.mode, BridgeMode.ANALYZE)
        self.assertEqual(request.lens, BridgeLens.PUNCH)
        self.assertEqual(request.requested_metric_families, ("dynamics", "transients"))
        self.assertEqual(request.question, "What changed?")
        self.assertEqual(request.timeout_ms, 2500)
        self.assertTrue(request.write_reports)

    def test_request_zero_timeout_is_preserved_and_validation_flags_it(self):
        request = create_bridge_request(
            request_id="req-zero-timeout",
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="File Analysis",
            audio_input_ref=input_ref(),
            timeout_ms=0,
        )

        self.assertEqual(request.timeout_ms, 0)
        self.assertIn("timeout_ms must be greater than zero when provided.", validate_bridge_request_shape(request))

    def test_request_to_dict_is_json_serializable(self):
        request = create_bridge_request(
            request_id="req-json",
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="File Analysis",
            audio_input_ref=input_ref(),
        )

        json.dumps(bridge_request_to_dict(request))

    def test_request_from_dict_roundtrips(self):
        request = create_bridge_request(
            request_id="req-roundtrip",
            mode=BridgeMode.COMPARE,
            lens=BridgeLens.WIDTH,
            source_label="Compare A/B",
            audio_input_ref=input_ref("a", "a.wav"),
            comparison_input_ref=input_ref("b", "b.wav"),
            requested_metric_families=("stereo", "correlation"),
            question="Compare these.",
            timeout_ms=1000,
            write_reports=True,
        )

        roundtrip = bridge_request_from_dict(bridge_request_to_dict(request))

        self.assertEqual(roundtrip.request_id, request.request_id)
        self.assertEqual(roundtrip.mode, BridgeMode.COMPARE)
        self.assertEqual(roundtrip.lens, BridgeLens.WIDTH)
        self.assertEqual(roundtrip.requested_metric_families, ("stereo", "correlation"))
        self.assertEqual(roundtrip.question, "Compare these.")
        self.assertEqual(validate_bridge_request_shape(roundtrip), ())

    def test_invalid_mode_is_reported_by_validation(self):
        request = create_bridge_request(
            request_id="req-bad-mode",
            mode="Magic",
            lens=BridgeLens.TONE,
            source_label="File Analysis",
            audio_input_ref=input_ref(),
        )

        self.assertIn("mode must be Analyze, Compare, or Reference.", validate_bridge_request_shape(request))

    def test_invalid_lens_is_reported_by_validation(self):
        request = create_bridge_request(
            request_id="req-bad-lens",
            mode=BridgeMode.ANALYZE,
            lens="Sparkle",
            source_label="File Analysis",
            audio_input_ref=input_ref(),
        )

        self.assertIn("lens must be Tone, Width, Loudness, or Punch.", validate_bridge_request_shape(request))

    def test_missing_analyze_input_is_reported_by_validation(self):
        request = create_bridge_request(
            request_id="req-missing-analyze",
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="File Analysis",
        )

        self.assertIn("Analyze mode requires audio_input_ref.", validate_bridge_request_shape(request))

    def test_missing_compare_b_input_is_reported_by_validation(self):
        request = create_bridge_request(
            request_id="req-missing-compare",
            mode=BridgeMode.COMPARE,
            lens=BridgeLens.WIDTH,
            source_label="Compare A/B",
            audio_input_ref=input_ref("a", "a.wav"),
        )

        self.assertIn("Compare mode requires comparison_input_ref for Mix B.", validate_bridge_request_shape(request))

    def test_missing_reference_target_is_reported_by_validation(self):
        request = create_bridge_request(
            request_id="req-missing-reference",
            mode=BridgeMode.REFERENCE,
            lens=BridgeLens.LOUDNESS,
            source_label="Reference Mode",
            audio_input_ref=input_ref("current", "current.wav"),
        )

        self.assertIn("Reference mode requires reference_input_ref for the target.", validate_bridge_request_shape(request))


class BridgeResponseContractTests(unittest.TestCase):
    def ready_response(self, **overrides):
        values = {
            "request_id": "req-response",
            "bridge_status": BridgeStatus.READY,
            "analysis_status": BridgeAnalysisStatus.READY,
            "ai_status": BridgeAIStatus.NO_AI_CONFIGURED,
            "report_status": BridgeReportStatus.NOT_REQUESTED,
            "mode": BridgeMode.ANALYZE,
            "lens": BridgeLens.TONE,
            "source_label": "File Analysis",
            "analysis_availability": "ready",
            "analysis_result": {"metrics": {"sample_peak_dbfs": -1.2}},
        }
        values.update(overrides)
        return create_bridge_response(**values)

    def test_create_response_with_separate_statuses(self):
        response = self.ready_response(report_status=BridgeReportStatus.FAILED)

        self.assertEqual(response.bridge_status, BridgeStatus.READY)
        self.assertEqual(response.analysis_status, BridgeAnalysisStatus.READY)
        self.assertEqual(response.ai_status, BridgeAIStatus.NO_AI_CONFIGURED)
        self.assertEqual(response.report_status, BridgeReportStatus.FAILED)
        self.assertEqual(validate_bridge_response_shape(response), ())

    def test_analysis_ready_with_ai_no_ai_configured_remains_valid(self):
        response = self.ready_response(ai_status=BridgeAIStatus.NO_AI_CONFIGURED)

        self.assertEqual(validate_bridge_response_shape(response), ())
        self.assertEqual(bridge_response_to_dict(response)["ai_status"], "NO_AI_CONFIGURED")

    def test_analysis_ready_with_report_failed_remains_valid_with_warning(self):
        response = self.ready_response(
            report_status=BridgeReportStatus.FAILED,
            warnings=("Report writing failed; factual analysis remains available.",),
        )

        serialized = bridge_response_to_dict(response)

        self.assertEqual(validate_bridge_response_shape(response), ())
        self.assertEqual(serialized["analysis_status"], "READY")
        self.assertEqual(serialized["report_status"], "FAILED")
        self.assertIn("Report writing failed", serialized["warnings"][0])

    def test_timeout_response_preserves_partial_limitations(self):
        response = self.ready_response(
            bridge_status=BridgeStatus.TIMEOUT,
            analysis_status=BridgeAnalysisStatus.LIMITED,
            limitations=("Timed out after partial factual analysis.",),
        )

        self.assertEqual(bridge_response_to_dict(response)["limitations"], ["Timed out after partial factual analysis."])

    def test_error_response_does_not_expose_stack_traces_in_user_facing_dict(self):
        response = self.ready_response(
            bridge_status=BridgeStatus.ERROR,
            analysis_status=BridgeAnalysisStatus.ERROR,
            warnings=('Traceback (most recent call last): File "bridge.py", line 1',),
            fallback_reason='Traceback: File "internal.py", line 2',
        )

        serialized = bridge_response_to_dict(response)
        text = json.dumps(serialized)

        self.assertNotIn("Traceback", text)
        self.assertNotIn("bridge.py", text)
        self.assertIn("[redacted error detail]", text)

    def test_response_to_dict_is_json_serializable(self):
        json.dumps(bridge_response_to_dict(self.ready_response()))

    def test_response_from_dict_roundtrips(self):
        response = self.ready_response(
            reports=(
                BridgeReportRef(
                    report_id="report-1",
                    kind="txt",
                    safe_label="mix-report.txt",
                    output_ref="Z:\\Private\\Reports\\mix-report.txt",
                    status=BridgeReportStatus.READY,
                ),
            )
        )

        roundtrip = bridge_response_from_dict(bridge_response_to_dict(response))

        self.assertEqual(roundtrip.request_id, response.request_id)
        self.assertEqual(roundtrip.bridge_status, BridgeStatus.READY)
        self.assertEqual(roundtrip.ai_status, BridgeAIStatus.NO_AI_CONFIGURED)
        self.assertEqual(roundtrip.reports[0].status, BridgeReportStatus.READY)

    def test_zero_metric_values_inside_analysis_result_are_preserved(self):
        response = self.ready_response(analysis_result={"metrics": {"rms_dbfs": 0, "crest_factor": 0.0}})
        serialized = bridge_response_to_dict(response)

        self.assertEqual(serialized["analysis_result"]["metrics"]["rms_dbfs"], 0)
        self.assertEqual(serialized["analysis_result"]["metrics"]["crest_factor"], 0.0)

    def test_fake_minus_999_values_are_not_exposed(self):
        response = self.ready_response(analysis_result={"metrics": {"lufs": -999, "note": "value -999"}})
        serialized_text = json.dumps(bridge_response_to_dict(response))

        self.assertNotIn("-999", serialized_text)
        self.assertIn("[unavailable]", serialized_text)

    def test_private_windows_paths_are_redacted(self):
        response = self.ready_response(metadata={"path": "Z:\\Private\\Audio\\mix.wav"})
        serialized_text = json.dumps(bridge_response_to_dict(response))

        self.assertNotIn("Z:\\Private\\Audio", serialized_text)
        self.assertIn("[redacted path]/mix.wav", serialized_text)

    def test_private_unix_paths_are_redacted(self):
        response = self.ready_response(metadata={"path": "/Users/example/private/mix.wav"})
        serialized_text = json.dumps(bridge_response_to_dict(response))

        self.assertNotIn("/Users/example/private", serialized_text)
        self.assertIn("[redacted path]/mix.wav", serialized_text)

    def test_endpoint_credentials_are_redacted(self):
        response = self.ready_response(metadata={"endpoint": "https://user:pass@example.invalid/v1/status"})
        serialized_text = json.dumps(bridge_response_to_dict(response))

        self.assertNotIn("user:pass", serialized_text)
        self.assertIn("https://[redacted]@example.invalid/v1/status", serialized_text)

    def test_api_key_like_metadata_is_redacted(self):
        response = self.ready_response(metadata={"api_key": "synthetic-key-value", "nested": {"token": "abc"}})
        serialized = bridge_response_to_dict(response)

        self.assertEqual(serialized["metadata"]["api_key"], "[redacted]")
        self.assertEqual(serialized["metadata"]["nested"]["token"], "[redacted]")
        self.assertNotIn("synthetic-key-value", json.dumps(serialized))

    def test_no_advice_or_canned_diagnosis_text_appears(self):
        response = self.ready_response(metadata={"bad_text": "Your mix is too loud; you should reduce compression."})
        serialized_text = json.dumps(bridge_response_to_dict(response)).lower()

        self.assertNotIn("your mix is too loud", serialized_text)
        self.assertNotIn("you should reduce compression", serialized_text)
        self.assertNotIn("this sounds professional", serialized_text)
        self.assertIn("[redacted unsupported advice]", serialized_text)


class BridgeStatusSeparationTests(unittest.TestCase):
    def test_bridge_status_ready_does_not_force_ai_status_ready(self):
        response = create_bridge_response(
            request_id="req-status",
            bridge_status=BridgeStatus.READY,
            analysis_status=BridgeAnalysisStatus.READY,
            ai_status=BridgeAIStatus.NO_AI_CONFIGURED,
            report_status=BridgeReportStatus.NOT_REQUESTED,
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="File Analysis",
        )

        self.assertEqual(bridge_response_to_dict(response)["bridge_status"], "READY")
        self.assertEqual(bridge_response_to_dict(response)["ai_status"], "NO_AI_CONFIGURED")

    def test_ai_status_error_does_not_force_bridge_status_error_if_factual_analysis_ready(self):
        response = create_bridge_response(
            request_id="req-ai-error",
            bridge_status=BridgeStatus.READY,
            analysis_status=BridgeAnalysisStatus.READY,
            ai_status=BridgeAIStatus.ERROR,
            report_status=BridgeReportStatus.NOT_REQUESTED,
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="File Analysis",
        )

        serialized = bridge_response_to_dict(response)
        self.assertEqual(serialized["bridge_status"], "READY")
        self.assertEqual(serialized["analysis_status"], "READY")
        self.assertEqual(serialized["ai_status"], "ERROR")

    def test_report_status_failed_does_not_force_analysis_status_error(self):
        response = create_bridge_response(
            request_id="req-report-failed",
            bridge_status=BridgeStatus.READY,
            analysis_status=BridgeAnalysisStatus.READY,
            ai_status=BridgeAIStatus.NO_AI_CONFIGURED,
            report_status=BridgeReportStatus.FAILED,
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="File Analysis",
        )

        serialized = bridge_response_to_dict(response)
        self.assertEqual(serialized["analysis_status"], "READY")
        self.assertEqual(serialized["report_status"], "FAILED")

    def test_no_ai_configured_is_preserved_as_ai_status(self):
        response = create_bridge_response(
            request_id="req-no-ai",
            bridge_status=BridgeStatus.NO_AI_CONFIGURED,
            analysis_status=BridgeAnalysisStatus.READY,
            ai_status=BridgeAIStatus.NO_AI_CONFIGURED,
            report_status=BridgeReportStatus.NOT_REQUESTED,
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="File Analysis",
        )

        self.assertEqual(bridge_response_to_dict(response)["ai_status"], "NO_AI_CONFIGURED")

    def test_unavailable_analysis_stays_unavailable(self):
        response = create_bridge_response(
            request_id="req-unavailable",
            bridge_status=BridgeStatus.UNAVAILABLE,
            analysis_status=BridgeAnalysisStatus.UNAVAILABLE,
            ai_status=BridgeAIStatus.UNAVAILABLE,
            report_status=BridgeReportStatus.UNAVAILABLE,
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="Meter-Only Fallback",
        )

        self.assertEqual(bridge_response_to_dict(response)["analysis_status"], "UNAVAILABLE")


class BridgeSerializationSafetyTests(unittest.TestCase):
    def test_nested_dataclass_serialization_works(self):
        request = create_bridge_request(
            request_id="req-nested",
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="File Analysis",
            audio_input_ref=input_ref(),
        )

        serialized = bridge_request_to_dict(request)
        self.assertEqual(serialized["audio_input_ref"]["safe_label"], "mix.wav")

    def test_enum_serialization_uses_string_values(self):
        response = create_bridge_response(
            request_id="req-enum",
            bridge_status=BridgeStatus.READY,
            analysis_status=BridgeAnalysisStatus.READY,
            ai_status=BridgeAIStatus.NO_AI_CONFIGURED,
            report_status=BridgeReportStatus.NOT_REQUESTED,
            mode=BridgeMode.REFERENCE,
            lens=BridgeLens.LOUDNESS,
            source_label="Reference Mode",
        )

        serialized = bridge_response_to_dict(response)
        self.assertEqual(serialized["mode"], "Reference")
        self.assertEqual(serialized["lens"], "Loudness")

    def test_tuple_fields_become_json_safe_lists(self):
        response = create_bridge_response(
            request_id="req-tuples",
            bridge_status=BridgeStatus.LIMITED,
            analysis_status=BridgeAnalysisStatus.LIMITED,
            ai_status=BridgeAIStatus.NO_AI_CONFIGURED,
            report_status=BridgeReportStatus.NOT_REQUESTED,
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.PUNCH,
            source_label="File Analysis",
            limitations=("limited snapshot",),
            warnings=("short window",),
        )

        serialized = bridge_response_to_dict(response)
        self.assertIsInstance(serialized["limitations"], list)
        json.dumps(serialized)

    def test_metadata_sanitization_is_recursive(self):
        sanitized = sanitize_bridge_dict(
            {
                "metadata": {
                    "nested": {
                        "api_token": "secretish",
                        "path": "/home/example/project/session.wav",
                        "value": -999,
                    }
                }
            }
        )

        text = json.dumps(sanitized)
        self.assertNotIn("secretish", text)
        self.assertNotIn("/home/example/project", text)
        self.assertNotIn("-999", text)
        self.assertIn("[redacted]", text)
        self.assertIn("[unavailable]", text)

    def test_zero_and_none_values_are_preserved(self):
        sanitized = sanitize_bridge_dict({"zero_int": 0, "zero_float": 0.0, "none_value": None})

        self.assertEqual(sanitized["zero_int"], 0)
        self.assertEqual(sanitized["zero_float"], 0.0)
        self.assertIsNone(sanitized["none_value"])

    def test_serialized_output_has_no_fake_values_full_paths_or_secrets(self):
        request = create_bridge_request(
            request_id="req-safe",
            mode=BridgeMode.ANALYZE,
            lens=BridgeLens.TONE,
            source_label="File Analysis",
            audio_input_ref=input_ref(),
            output_dir_ref="/var/private/aifred/reports",
            metadata={"secret": "hidden", "metric": -999},
        )

        serialized_text = json.dumps(bridge_request_to_dict(request))

        self.assertNotIn("-999", serialized_text)
        self.assertNotIn("Z:\\Private", serialized_text)
        self.assertNotIn("/var/private", serialized_text)
        self.assertNotIn("hidden", serialized_text)
        self.assertIn("[redacted]", serialized_text)


if __name__ == "__main__":
    unittest.main()
