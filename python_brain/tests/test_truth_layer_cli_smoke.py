"""Tests for the Python Truth Layer CLI smoke runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "python_brain" / "scripts" / "aifred_truth_smoke.py"


def run_smoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_no_forbidden_stdout(testcase: unittest.TestCase, stdout: str) -> None:
    lowered = stdout.lower()
    forbidden = (
        "you should",
        "try ",
        "fix ",
        "recommend",
        "advice",
        "good",
        "bad",
        "better",
        "professional",
        "warm",
        "thin",
        "muddy",
        "harsh",
        "-999",
    )
    testcase.assertFalse(any(term in lowered for term in forbidden), stdout)


class TruthLayerCliSmokeTests(unittest.TestCase):
    def test_script_runs_successfully_with_generated_synthetic_wav(self) -> None:
        result = run_smoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AIFRED Truth Layer Smoke Summary", result.stdout)
        self.assertIn("Source: aifred-smoke-synthetic.wav", result.stdout)
        self.assertIn("Packet availability:", result.stdout)
        assert_no_forbidden_stdout(self, result.stdout)

    def test_script_runs_successfully_with_generated_synthetic_wav_and_json(self) -> None:
        result = run_smoke("--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["source_display_name"], "aifred-smoke-synthetic.wav")
        self.assertIn("packet_availability", payload)
        self.assertIsInstance(payload["selected_metric_families"], list)
        assert_no_forbidden_stdout(self, result.stdout)

    def test_json_output_is_parseable(self) -> None:
        result = run_smoke("--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, dict)
        self.assertIn("analysis", payload)
        self.assertIn("packet", payload)

    def test_script_writes_text_and_html_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_smoke("--write-reports", "--output-dir", tmpdir)
            self.assertEqual(result.returncode, 0, result.stderr)
            txt_files = list(Path(tmpdir).glob("*.txt"))
            html_files = list(Path(tmpdir).glob("*.html"))
            self.assertEqual(len(txt_files), 1)
            self.assertEqual(len(html_files), 1)
            self.assertIn("Reports:", result.stdout)
            self.assertIn(txt_files[0].name, result.stdout)
            self.assertIn(html_files[0].name, result.stdout)
            assert_no_forbidden_stdout(self, result.stdout)

    def test_script_rejects_missing_input_when_no_synthetic_is_used(self) -> None:
        result = run_smoke("--no-synthetic")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("synthetic input is disabled", result.stderr)

    def test_stdout_does_not_expose_private_temp_parent_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_smoke("--write-reports", "--output-dir", tmpdir)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(tmpdir, result.stdout)
            self.assertNotIn(str(Path(tmpdir).parent), result.stdout)

    def test_stdout_does_not_contain_advice_text(self) -> None:
        result = run_smoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        lowered = result.stdout.lower()
        self.assertNotIn("you should", lowered)
        self.assertNotIn("advice", lowered)
        self.assertNotIn("recommend", lowered)

    def test_stdout_does_not_contain_subjective_labels(self) -> None:
        result = run_smoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        lowered = result.stdout.lower()
        for term in ("good", "bad", "better", "professional", "warm", "thin", "muddy", "harsh"):
            self.assertNotIn(term, lowered)

    def test_stdout_does_not_contain_fake_minus_999(self) -> None:
        result = run_smoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("-999", result.stdout)

    def test_report_files_are_created_in_temp_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_smoke("--json", "--write-reports", "--output-dir", tmpdir)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload["reports"]), 2)
            self.assertTrue(all(report["created"] for report in payload["reports"]))
            self.assertEqual(len(list(Path(tmpdir).glob("*.txt"))), 1)
            self.assertEqual(len(list(Path(tmpdir).glob("*.html"))), 1)


if __name__ == "__main__":
    unittest.main()
