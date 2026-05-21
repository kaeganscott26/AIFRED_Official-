"""Tests for `aifred_brain.progress_memory`."""

from __future__ import annotations

import unittest

from aifred_brain.export_history import ExportHistory, create_export_record
from aifred_brain.progress_memory import (
    ProgressTrendAvailability,
    calculate_metric_progress_trend,
    calculate_progress_memory,
    collect_metric_keys,
    extract_numeric_metric_facts,
    progress_memory_from_dict,
    progress_memory_to_dict,
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


def _record(
    export_id: str,
    timestamp: str,
    *facts: dict[str, object],
) -> object:
    return create_export_record(
        {
            "timestamp_utc": timestamp,
            "session_label": "Synthetic Session",
            "source_label": "File Analysis",
            "mode": "analyze",
            "facts": facts,
            "limitations": (),
            "warnings": (),
            "metadata": {"fixture": "synthetic"},
        },
        session_label=export_id,
    )


class ProgressMemoryFoundationTests(unittest.TestCase):
    def test_empty_history_does_not_crash(self) -> None:
        memory = calculate_progress_memory(())
        self.assertEqual(memory.export_count, 0)
        self.assertEqual(memory.metric_trends, ())
        self.assertTrue(memory.limitations)

    def test_one_record_history_marks_insufficient_history(self) -> None:
        record = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        memory = calculate_progress_memory((record,))
        self.assertEqual(memory.metric_trends[0].availability, ProgressTrendAvailability.INSUFFICIENT_HISTORY)
        self.assertIsNone(memory.metric_trends[0].delta)

    def test_extracts_numeric_metric_facts(self) -> None:
        record = _record(
            "export-a",
            "2026-05-21T12:00:00Z",
            _fact("sample_peak", 0.25),
            _fact("note", "not numeric", family="metadata", unit="text"),
        )
        facts = extract_numeric_metric_facts(record)
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]["family"], "level")
        self.assertEqual(facts[0]["name"], "sample_peak")
        self.assertEqual(facts[0]["value"], 0.25)

    def test_ignores_non_numeric_values_for_numeric_trend_calculations(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", "unknown"))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        trend = calculate_metric_progress_trend((first, latest), "level", "sample_peak")
        self.assertEqual(trend.availability, ProgressTrendAvailability.NON_NUMERIC)
        self.assertEqual(trend.sample_count, 1)
        self.assertIsNone(trend.delta)

    def test_collects_metric_keys_across_records(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("rms", 0.1))
        self.assertEqual(collect_metric_keys((first, latest)), (("level", "rms"), ("level", "sample_peak")))

    def test_calculates_first_and_latest_values(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        trend = calculate_metric_progress_trend((first, latest), "level", "sample_peak")
        self.assertEqual(trend.first_value, 0.25)
        self.assertEqual(trend.latest_value, 0.5)

    def test_calculates_signed_delta(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.75))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        trend = calculate_metric_progress_trend((first, latest), "level", "sample_peak")
        self.assertEqual(trend.delta, -0.25)

    def test_calculates_absolute_delta(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.75))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        trend = calculate_metric_progress_trend((first, latest), "level", "sample_peak")
        self.assertEqual(trend.absolute_delta, 0.25)

    def test_calculates_percent_delta(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        trend = calculate_metric_progress_trend((first, latest), "level", "sample_peak")
        self.assertEqual(trend.percent_delta, 100.0)

    def test_percent_delta_with_zero_first_value_returns_none(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.0))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        trend = calculate_metric_progress_trend((first, latest), "level", "sample_peak")
        self.assertIsNone(trend.percent_delta)

    def test_zero_values_are_preserved_as_valid(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.0))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.0))
        trend = calculate_metric_progress_trend((first, latest), "level", "sample_peak")
        self.assertEqual(trend.first_value, 0.0)
        self.assertEqual(trend.latest_value, 0.0)
        self.assertEqual(trend.delta, 0.0)
        self.assertEqual(trend.availability, ProgressTrendAvailability.AVAILABLE)

    def test_missing_metric_in_one_export_is_represented_honestly(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        middle = _record("export-b", "2026-05-21T12:01:00Z", _fact("rms", 0.1))
        latest = _record("export-c", "2026-05-21T12:02:00Z", _fact("sample_peak", 0.5))
        trend = calculate_metric_progress_trend((first, middle, latest), "level", "sample_peak")
        self.assertEqual(trend.sample_count, 2)
        self.assertEqual(trend.availability, ProgressTrendAvailability.AVAILABLE)
        self.assertTrue(any("missing" in limitation.lower() for limitation in trend.limitations))

    def test_full_progress_memory_includes_export_count(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        memory = calculate_progress_memory(ExportHistory((first, latest)))
        self.assertEqual(memory.export_count, 2)

    def test_full_progress_memory_includes_first_and_latest_export_ids(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        memory = calculate_progress_memory((first, latest))
        self.assertEqual(memory.first_export_id, first.export_id)
        self.assertEqual(memory.latest_export_id, latest.export_id)
        self.assertEqual(memory.first_timestamp_utc, "2026-05-21T12:00:00Z")
        self.assertEqual(memory.latest_timestamp_utc, "2026-05-21T12:01:00Z")

    def test_serialization_to_dict_works(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        data = progress_memory_to_dict(calculate_progress_memory((first, latest)))
        self.assertEqual(data["export_count"], 2)
        self.assertEqual(data["metric_trends"][0]["availability"], "available")

    def test_deserialization_from_dict_works(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        data = progress_memory_to_dict(calculate_progress_memory((first, latest)))
        loaded = progress_memory_from_dict(data)
        self.assertEqual(loaded.export_count, 2)
        self.assertEqual(loaded.metric_trends[0].delta, 0.25)

    def test_no_fake_minus_999_values_appear(self) -> None:
        with self.assertRaises(ValueError):
            _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", -999))

    def test_no_advice_text_appears(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        text = repr(calculate_progress_memory((first, latest))).lower()
        for phrase in ("advice", "recommend", "you should", "try ", "fix your", "next move"):
            self.assertNotIn(phrase, text)

    def test_no_subjective_or_motivational_labels_appear(self) -> None:
        first = _record("export-a", "2026-05-21T12:00:00Z", _fact("sample_peak", 0.25))
        latest = _record("export-b", "2026-05-21T12:01:00Z", _fact("sample_peak", 0.5))
        text = repr(calculate_progress_memory((first, latest))).lower()
        for phrase in ("improved", "worse", "better", "professional", "progress is good", "great job"):
            self.assertNotIn(phrase, text)


@unittest.skip("Future phase only; AI memory and coaching are not implemented in progress memory.")
class FutureProgressMemoryTests(unittest.TestCase):
    def test_progress_coaching_is_outside_factual_memory(self) -> None:
        """Future test: generated coaching must stay outside factual progress memory."""


if __name__ == "__main__":
    unittest.main()
