"""Tests for `aifred_brain.export_history`."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from aifred_brain.export_history import (
    ExportHistory,
    append_export_record,
    compare_latest_exports,
    create_export_record,
    export_history_from_dict,
    export_history_to_dict,
    generate_export_id,
    load_export_history,
    save_export_history,
)


def _fact(name: str, value: object, family: str = "level", unit: str = "linear") -> dict[str, object]:
    return {
        "family": family,
        "name": name,
        "value": value,
        "unit": unit,
        "available": True,
        "limitations": (),
    }


def _packet(*facts: dict[str, object], timestamp: str = "2026-05-21T12:00:00Z") -> dict[str, object]:
    return {
        "timestamp_utc": timestamp,
        "session_label": "Session One",
        "source_label": "File Analysis",
        "mode": "analyze",
        "facts": facts or (_fact("sample_peak", 0.5),),
        "limitations": ("short capture",),
        "warnings": ("windowed facts only",),
        "metadata": {"file_path": r"C:\Users\North\Secret\mix.wav", "take": "A"},
    }


class ExportHistoryFoundationTests(unittest.TestCase):
    def test_generates_stableish_export_id_with_timestamp_and_session(self) -> None:
        export_id = generate_export_id("2026-05-21T12:00:00Z", "Session One")
        self.assertEqual(export_id, "session-one-2026-05-21t12-00-00z")

    def test_creates_export_record_from_packet_like_dict(self) -> None:
        record = create_export_record(_packet())
        self.assertEqual(record.session_label, "Session One")
        self.assertEqual(record.source_label, "File Analysis")
        self.assertEqual(record.mode, "analyze")
        self.assertIn("level.sample_peak", record.metrics)

    def test_appends_export_record_without_mutating_original_history_unexpectedly(self) -> None:
        history = ExportHistory()
        record = create_export_record(_packet())
        updated = append_export_record(history, record)
        self.assertEqual(history.records, ())
        self.assertEqual(updated.records, (record,))

    def test_serializes_export_history_to_dict(self) -> None:
        record = create_export_record(_packet())
        data = export_history_to_dict(ExportHistory((record,)))
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(data["records"][0]["export_id"], record.export_id)

    def test_deserializes_export_history_from_dict(self) -> None:
        record = create_export_record(_packet())
        data = export_history_to_dict(ExportHistory((record,)))
        loaded = export_history_from_dict(data)
        self.assertEqual(loaded.records[0].export_id, record.export_id)
        self.assertEqual(loaded.records[0].metrics["level.sample_peak"]["value"], 0.5)

    def test_saves_json_file_to_temp_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.json"
            record = create_export_record(_packet())
            written = save_export_history(ExportHistory((record,)), path)
            self.assertTrue(written.exists())
            self.assertIn('"records"', written.read_text(encoding="utf-8"))

    def test_loads_json_file_from_temp_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.json"
            record = create_export_record(_packet())
            save_export_history(ExportHistory((record,)), path)
            loaded = load_export_history(path)
            self.assertEqual(loaded.records[0].export_id, record.export_id)

    def test_empty_history_compare_does_not_crash(self) -> None:
        delta = compare_latest_exports(ExportHistory())
        self.assertIsNone(delta.previous_export_id)
        self.assertIsNone(delta.current_export_id)
        self.assertTrue(delta.limitations)

    def test_one_record_history_compare_returns_limited_or_unavailable_comparison(self) -> None:
        record = create_export_record(_packet())
        delta = compare_latest_exports(ExportHistory((record,)))
        self.assertIsNone(delta.previous_export_id)
        self.assertEqual(delta.current_export_id, record.export_id)
        self.assertTrue(delta.limitations)

    def test_latest_two_exports_identify_changed_metric_names(self) -> None:
        previous = create_export_record(_packet(_fact("sample_peak", 0.5), timestamp="2026-05-21T12:00:00Z"))
        current = create_export_record(_packet(_fact("sample_peak", 0.75), timestamp="2026-05-21T12:01:00Z"))
        delta = compare_latest_exports(ExportHistory((previous, current)))
        self.assertEqual(delta.changed_metric_names, ("level.sample_peak",))

    def test_latest_two_exports_identify_added_metric_names(self) -> None:
        previous = create_export_record(_packet(_fact("sample_peak", 0.5), timestamp="2026-05-21T12:00:00Z"))
        current = create_export_record(
            _packet(_fact("sample_peak", 0.5), _fact("rms", 0.25), timestamp="2026-05-21T12:01:00Z")
        )
        delta = compare_latest_exports(ExportHistory((previous, current)))
        self.assertEqual(delta.added_metric_names, ("level.rms",))

    def test_latest_two_exports_identify_removed_metric_names(self) -> None:
        previous = create_export_record(
            _packet(_fact("sample_peak", 0.5), _fact("rms", 0.25), timestamp="2026-05-21T12:00:00Z")
        )
        current = create_export_record(_packet(_fact("sample_peak", 0.5), timestamp="2026-05-21T12:01:00Z"))
        delta = compare_latest_exports(ExportHistory((previous, current)))
        self.assertEqual(delta.removed_metric_names, ("level.rms",))

    def test_zero_metric_values_are_preserved(self) -> None:
        record = create_export_record(_packet(_fact("sample_peak", 0.0)))
        self.assertEqual(record.metrics["level.sample_peak"]["value"], 0.0)

    def test_metadata_is_privacy_sanitized(self) -> None:
        record = create_export_record(_packet())
        self.assertEqual(record.metadata["file_path"], "<private-path>/mix.wav")
        self.assertEqual(record.metadata["take"], "A")

    def test_local_paths_are_not_exposed(self) -> None:
        record = create_export_record(_packet())
        text = repr(record)
        self.assertNotIn(r"C:\Users\North\Secret", text)

    def test_no_fake_minus_999_values_appear(self) -> None:
        with self.assertRaises(ValueError):
            create_export_record(_packet(_fact("sample_peak", -999)))

    def test_no_advice_text_appears(self) -> None:
        record = create_export_record(_packet())
        text = repr(record).lower()
        for phrase in ("advice", "recommend", "you should", "try ", "fix your"):
            self.assertNotIn(phrase, text)

    def test_no_subjective_labels_appear(self) -> None:
        history = ExportHistory((create_export_record(_packet()),))
        text = repr(history).lower()
        for phrase in ("improved", "worse", "better", "professional", "punchy"):
            self.assertNotIn(phrase, text)


@unittest.skip("Future phase only; progress coaching is not implemented in export history.")
class FutureExportHistoryTests(unittest.TestCase):
    def test_history_based_progress_summary_is_separate_from_record_storage(self) -> None:
        """Future test: coaching/progress summaries belong outside export history storage."""


if __name__ == "__main__":
    unittest.main()
