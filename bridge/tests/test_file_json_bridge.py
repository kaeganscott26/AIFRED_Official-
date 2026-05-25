import json
import tempfile
import unittest
from pathlib import Path

from bridge.bridge_contract import (
    BridgeAIStatus,
    BridgeAnalysisStatus,
    BridgeInputRef,
    BridgeLens,
    BridgeMode,
    BridgeReportStatus,
    BridgeStatus,
    bridge_request_to_dict,
    bridge_response_to_dict,
    create_bridge_request,
    create_bridge_response,
)
from bridge.file_json_bridge import (
    SMOKE_BRIDGE_VERSION,
    create_smoke_response_from_request,
    read_bridge_request_json,
    read_bridge_response_json,
    roundtrip_bridge_request_json,
    roundtrip_bridge_response_json,
    write_bridge_request_json,
    write_bridge_response_json,
)


def input_ref(ref_id="input-a", label="mix.wav", internal_ref=None, metadata=None):
    return BridgeInputRef(
        ref_id=ref_id,
        kind="audio_snapshot",
        safe_label=label,
        internal_ref=internal_ref or f"C:\\Users\\North\\Private\\Audio\\{label}",
        metadata=metadata or {"unix_path": f"/Users/north/private/{label}"},
    )


def make_analyze_request(**overrides):
    values = {
        "request_id": "req-analyze",
        "mode": BridgeMode.ANALYZE,
        "lens": BridgeLens.TONE,
        "source_label": "File Analysis",
        "audio_input_ref": input_ref(),
        "question": "What changed?",
        "requested_metric_families": ("frequency", "tonal_balance"),
        "timeout_ms": 1000,
        "write_reports": True,
        "metadata": {
            "path": "C:\\Users\\North\\Private\\Audio\\mix.wav",
            "api_key": "sk-test-private",
            "endpoint": "https://user:pass@example.invalid/v1/status",
            "fake_value": -999,
            "zero_value": 0,
            "none_value": None,
        },
    }
    values.update(overrides)
    return create_bridge_request(**values)


def make_response(**overrides):
    values = {
        "request_id": "req-response",
        "bridge_status": BridgeStatus.LIMITED,
        "analysis_status": BridgeAnalysisStatus.UNAVAILABLE,
        "ai_status": BridgeAIStatus.NO_AI_CONFIGURED,
        "report_status": BridgeReportStatus.NOT_REQUESTED,
        "mode": BridgeMode.ANALYZE,
        "lens": BridgeLens.TONE,
        "source_label": "File Analysis",
        "analysis_availability": "unavailable",
        "analysis_result": {
            "metrics": {
                "zero": 0,
                "none": None,
                "fake": -999,
                "path": "/home/north/private/mix.wav",
            }
        },
        "limitations": ("File/JSON bridge smoke only.",),
        "warnings": ("No real analysis executed.",),
        "fallback_reason": "Real analysis is not executed by the file/JSON bridge smoke runner.",
        "metadata": {
            "api_token": "sk-test-private",
            "endpoint": "https://user:pass@example.invalid/v1/status",
            "windows_path": "C:\\Users\\North\\Private\\Audio\\mix.wav",
        },
    }
    values.update(overrides)
    return create_bridge_response(**values)


class FileJsonBridgeRequestTests(unittest.TestCase):
    def test_write_and_read_analyze_request_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "request.json"
            request = make_analyze_request()

            write_bridge_request_json(request, path)
            loaded = read_bridge_request_json(path)

        self.assertEqual(loaded.request_id, "req-analyze")
        self.assertEqual(loaded.mode, BridgeMode.ANALYZE)

    def test_write_and_read_compare_request_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "compare.json"
            request = make_analyze_request(
                request_id="req-compare",
                mode=BridgeMode.COMPARE,
                lens=BridgeLens.WIDTH,
                source_label="Compare A/B",
                audio_input_ref=input_ref("mix-a", "a.wav"),
                comparison_input_ref=input_ref("mix-b", "b.wav"),
                requested_metric_families=("stereo", "correlation"),
            )

            loaded = roundtrip_bridge_request_json(request, path)

        self.assertEqual(loaded.mode, BridgeMode.COMPARE)
        self.assertEqual(loaded.lens, BridgeLens.WIDTH)
        self.assertEqual(loaded.comparison_input_ref.ref_id, "mix-b")

    def test_write_and_read_reference_request_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reference.json"
            request = make_analyze_request(
                request_id="req-reference",
                mode=BridgeMode.REFERENCE,
                lens=BridgeLens.LOUDNESS,
                source_label="Reference Mode",
                audio_input_ref=input_ref("current", "current.wav"),
                reference_input_ref=input_ref("target", "target.wav"),
                requested_metric_families=("level", "loudness"),
            )

            loaded = roundtrip_bridge_request_json(request, path)

        self.assertEqual(loaded.mode, BridgeMode.REFERENCE)
        self.assertEqual(loaded.lens, BridgeLens.LOUDNESS)
        self.assertEqual(loaded.reference_input_ref.safe_label, "target.wav")

    def test_request_roundtrip_preserves_required_fields_and_zero_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roundtrip.json"
            request = make_analyze_request()

            loaded = roundtrip_bridge_request_json(request, path)

        self.assertEqual(loaded.request_id, request.request_id)
        self.assertEqual(loaded.mode, BridgeMode.ANALYZE)
        self.assertEqual(loaded.lens, BridgeLens.TONE)
        self.assertEqual(loaded.source_label, "File Analysis")
        self.assertEqual(loaded.requested_metric_families, ("frequency", "tonal_balance"))
        self.assertEqual(loaded.question, "What changed?")
        self.assertTrue(loaded.write_reports)
        self.assertEqual(loaded.timeout_ms, 1000)
        self.assertEqual(loaded.metadata["zero_value"], 0)
        self.assertIsNone(loaded.metadata["none_value"])

    def test_request_json_output_is_serializable_and_sanitized(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "safe-request.json"
            write_bridge_request_json(make_analyze_request(), path)
            data = json.loads(path.read_text(encoding="utf-8"))
            text = json.dumps(data)

        json.dumps(data)
        self.assertNotIn("-999", text)
        self.assertNotIn("C:\\Users\\North", text)
        self.assertNotIn("/Users/north", text)
        self.assertNotIn("sk-test-private", text)
        self.assertNotIn("user:pass", text)
        self.assertIn("[unavailable]", text)
        self.assertNotIn("https://user:pass@example.invalid", text)

    def test_bridge_contract_request_dict_output_is_json_serializable(self):
        json.dumps(bridge_request_to_dict(make_analyze_request()))


class FileJsonBridgeResponseTests(unittest.TestCase):
    def test_write_and_read_bridge_response_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "response.json"
            response = make_response()

            write_bridge_response_json(response, path)
            loaded = read_bridge_response_json(path)

        self.assertEqual(loaded.request_id, "req-response")
        self.assertEqual(loaded.bridge_status, BridgeStatus.LIMITED)

    def test_response_roundtrip_preserves_statuses_limitations_and_warnings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "response-roundtrip.json"
            response = make_response()

            loaded = roundtrip_bridge_response_json(response, path)

        self.assertEqual(loaded.request_id, response.request_id)
        self.assertEqual(loaded.bridge_status, BridgeStatus.LIMITED)
        self.assertEqual(loaded.analysis_status, BridgeAnalysisStatus.UNAVAILABLE)
        self.assertEqual(loaded.ai_status, BridgeAIStatus.NO_AI_CONFIGURED)
        self.assertEqual(loaded.report_status, BridgeReportStatus.NOT_REQUESTED)
        self.assertEqual(loaded.limitations, ("File/JSON bridge smoke only.",))
        self.assertEqual(loaded.warnings, ("No real analysis executed.",))

    def test_response_json_output_is_serializable_and_sanitized(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "safe-response.json"
            write_bridge_response_json(make_response(), path)
            data = json.loads(path.read_text(encoding="utf-8"))
            text = json.dumps(data)

        json.dumps(data)
        self.assertNotIn("-999", text)
        self.assertNotIn("C:\\Users\\North", text)
        self.assertNotIn("/home/north", text)
        self.assertNotIn("sk-test-private", text)
        self.assertNotIn("user:pass", text)
        self.assertIn("[unavailable]", text)
        self.assertNotIn("https://user:pass@example.invalid", text)

    def test_bridge_contract_response_dict_output_is_json_serializable(self):
        json.dumps(bridge_response_to_dict(make_response()))


class FileJsonBridgeSmokeResponseTests(unittest.TestCase):
    def test_smoke_response_is_structured_and_preserves_request_context(self):
        request = make_analyze_request(
            request_id="req-smoke",
            mode=BridgeMode.REFERENCE,
            lens=BridgeLens.PUNCH,
            source_label="Reference Mode",
            audio_input_ref=input_ref("current", "current.wav"),
            reference_input_ref=input_ref("target", "target.wav"),
            write_reports=True,
        )

        response = create_smoke_response_from_request(request)
        serialized = bridge_response_to_dict(response)

        self.assertEqual(response.request_id, "req-smoke")
        self.assertEqual(response.mode, BridgeMode.REFERENCE)
        self.assertEqual(response.lens, BridgeLens.PUNCH)
        self.assertEqual(response.source_label, "Reference Mode")
        self.assertEqual(response.bridge_status, BridgeStatus.LIMITED)
        self.assertNotEqual(response.analysis_status, BridgeAnalysisStatus.READY)
        self.assertNotEqual(response.ai_status, BridgeAIStatus.READY)
        self.assertEqual(response.ai_status, BridgeAIStatus.NO_AI_CONFIGURED)
        self.assertEqual(response.report_status, BridgeReportStatus.UNAVAILABLE)
        self.assertEqual(response.bridge_version, SMOKE_BRIDGE_VERSION)
        self.assertTrue(serialized["validation_result"]["smoke_only"])

    def test_smoke_response_says_real_analysis_is_not_executed(self):
        response = create_smoke_response_from_request(make_analyze_request())
        text = json.dumps(bridge_response_to_dict(response)).lower()

        self.assertIn("real analysis is not executed", text)
        self.assertNotIn("advice", text)
        self.assertNotIn("your mix is too loud", text)
        self.assertNotIn("this sounds professional", text)
        self.assertNotIn("-999", text)
        self.assertNotIn("C:\\Users\\North", text)
        self.assertNotIn("/Users/north", text)


class FileJsonBridgeErrorHandlingTests(unittest.TestCase):
    def test_invalid_request_json_raises_value_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad-request.json"
            path.write_text(json.dumps({"request_id": "bad", "mode": "Magic"}), encoding="utf-8")

            with self.assertRaises(ValueError) as error:
                read_bridge_request_json(path)

        self.assertEqual(str(error.exception), "Invalid bridge request JSON shape.")

    def test_invalid_response_json_raises_value_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad-response.json"
            path.write_text(json.dumps({"request_id": "bad", "bridge_status": "BROKEN"}), encoding="utf-8")

            with self.assertRaises(ValueError) as error:
                read_bridge_response_json(path)

        self.assertEqual(str(error.exception), "Invalid bridge response JSON shape.")

    def test_malformed_json_raises_safe_value_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "malformed.json"
            path.write_text("{not-json", encoding="utf-8")

            with self.assertRaises(ValueError) as error:
                read_bridge_request_json(path)

        self.assertEqual(str(error.exception), "Invalid bridge JSON.")

    def test_missing_file_raises_safe_file_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.json"

            with self.assertRaises(FileNotFoundError) as error:
                read_bridge_request_json(path)

        self.assertEqual(str(error.exception), "Bridge JSON file not found.")

    def test_error_messages_do_not_expose_private_path_or_secret(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad-secret.json"
            path.write_text(
                json.dumps(
                    {
                        "request_id": "bad",
                        "mode": "Magic",
                        "lens": "Sparkle",
                        "source_label": "File Analysis",
                        "metadata": {
                            "secret": "sk-test-private",
                            "path": "C:\\Users\\North\\Private\\mix.wav",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError) as error:
                read_bridge_request_json(path)

        message = str(error.exception)
        self.assertNotIn("sk-test-private", message)
        self.assertNotIn("C:\\Users\\North", message)

    def test_invalid_mode_and_lens_are_rejected_by_validation(self):
        bad_request = make_analyze_request(mode="Magic", lens="Sparkle")

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            with self.assertRaises(ValueError):
                write_bridge_request_json(bad_request, path)


if __name__ == "__main__":
    unittest.main()
