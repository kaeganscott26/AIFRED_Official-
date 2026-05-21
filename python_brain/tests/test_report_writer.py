"""Tests for `aifred_brain.report_writer`."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from aifred_brain.report_writer import (
    ReportFormat,
    generate_report_filename,
    render_html_report,
    render_text_report,
    sanitize_report_filename,
    write_report,
)


def _packet() -> dict[str, object]:
    return {
        "question": "Check <levels> only",
        "mode": "analyze",
        "source_label": "File Analysis",
        "confidence": "High",
        "freshness": "current",
        "availability": "ready",
        "metric_families": ("level", "dynamics"),
        "facts": (
            {
                "family": "level",
                "name": "sample_peak",
                "value": 0.5,
                "unit": "linear",
                "available": True,
                "limitations": (),
            },
        ),
        "limitations": ("short capture",),
        "warnings": ("windowed facts only",),
        "metadata": {"file_path": r"C:\Users\North\Secret\mix.wav", "take": "A"},
        "session_label": "Session: One/Two",
    }


class ReportWriterTests(unittest.TestCase):
    def test_sanitizes_unsafe_filename_characters(self) -> None:
        self.assertEqual(sanitize_report_filename('Mix: A/B*?"<>|'), "Mix_A_B")

    def test_generates_txt_filename(self) -> None:
        filename = generate_report_filename("mix", ".txt")
        self.assertTrue(filename.startswith("mix-"))
        self.assertTrue(filename.endswith(".txt"))

    def test_generates_html_filename(self) -> None:
        filename = generate_report_filename("mix", ".html")
        self.assertTrue(filename.startswith("mix-"))
        self.assertTrue(filename.endswith(".html"))

    def test_text_report_includes_mode_source_confidence_freshness(self) -> None:
        report = render_text_report(_packet())
        self.assertIn("Mode: analyze", report)
        self.assertIn("Source: File Analysis", report)
        self.assertIn("Confidence: High", report)
        self.assertIn("Freshness: current", report)

    def test_text_report_includes_facts(self) -> None:
        report = render_text_report(_packet())
        self.assertIn("Facts:", report)
        self.assertIn("level.sample_peak: 0.5 linear", report)

    def test_text_report_includes_limitations_and_warnings(self) -> None:
        report = render_text_report(_packet())
        self.assertIn("Limitations:", report)
        self.assertIn("short capture", report)
        self.assertIn("Warnings:", report)
        self.assertIn("windowed facts only", report)

    def test_html_report_escapes_user_provided_text(self) -> None:
        report = render_html_report(_packet())
        self.assertIn("Check &lt;levels&gt; only", report)
        self.assertNotIn("Check <levels> only", report)

    def test_html_report_includes_facts(self) -> None:
        report = render_html_report(_packet())
        self.assertIn("<h2>Facts</h2>", report)
        self.assertIn("sample_peak", report)
        self.assertIn("0.5", report)

    def test_write_text_report_creates_file_in_temp_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = write_report(_packet(), temp_dir, ReportFormat.TEXT)
            self.assertTrue(result.created)
            self.assertTrue(result.path.exists())
            self.assertEqual(result.format, ReportFormat.TEXT)
            self.assertEqual(result.path.suffix, ".txt")

    def test_write_html_report_creates_file_in_temp_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = write_report(_packet(), temp_dir, "html")
            self.assertTrue(result.created)
            self.assertTrue(result.path.exists())
            self.assertEqual(result.format, ReportFormat.HTML)
            self.assertEqual(result.path.suffix, ".html")

    def test_report_result_includes_safe_display_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = write_report(_packet(), temp_dir)
            self.assertEqual(result.safe_display_path, result.path.name)
            self.assertNotIn(str(Path(temp_dir)), result.safe_display_path)

    def test_metadata_is_privacy_sanitized(self) -> None:
        report = render_text_report(_packet())
        self.assertIn("<private-path>/mix.wav", report)
        self.assertIn("take: A", report)

    def test_local_paths_are_not_exposed(self) -> None:
        report = render_text_report(_packet())
        self.assertNotIn(r"C:\Users\North\Secret", report)

    def test_no_fake_minus_999_values_appear(self) -> None:
        bad_packet = _packet()
        bad_packet["facts"] = ({"family": "level", "name": "sample_peak", "value": -999},)
        with self.assertRaises(ValueError):
            render_text_report(bad_packet)

    def test_no_advice_text_appears(self) -> None:
        report = render_text_report(_packet()).lower()
        for phrase in ("advice", "recommend", "you should", "try ", "fix your"):
            self.assertNotIn(phrase, report)

    def test_no_canned_phrases_appear(self) -> None:
        report = render_text_report(_packet()).lower()
        for phrase in ("next practical move", "make it sound more professional", "your mix needs"):
            self.assertNotIn(phrase, report)

    def test_unsupported_report_format_is_rejected_cleanly(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                write_report(_packet(), temp_dir, "pdf")


if __name__ == "__main__":
    unittest.main()
