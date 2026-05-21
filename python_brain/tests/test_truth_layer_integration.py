"""Integration tests for the Python Truth Layer.

These tests use synthetic data only. They prove already-implemented modules can
pass factual state through the current truth-layer pipeline without generating
advice, fake metric values, or private-path leakage.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.analysis_state import (  # noqa: E402
    AnalysisAvailability,
    analysis_result_to_dict,
    create_analysis_context,
    create_analysis_metric_bundle,
    create_analysis_result,
)
from aifred_brain.compare_ab import compare_packet_facts  # noqa: E402
from aifred_brain.dynamics_metrics import calculate_dynamics_metrics  # noqa: E402
from aifred_brain.export_history import (  # noqa: E402
    ExportHistory,
    append_export_record,
    compare_latest_exports,
    create_export_record,
    export_history_to_dict,
    load_export_history,
    save_export_history,
)
from aifred_brain.frequency_metrics import (  # noqa: E402
    FrequencyMetrics,
    calculate_dft_magnitudes,
    calculate_frequency_metrics,
)
from aifred_brain.interpretation_packet import (  # noqa: E402
    create_interpretation_packet,
    create_metric_fact,
    packet_to_dict,
)
from aifred_brain.level_metrics import LevelMetrics, calculate_level_metrics  # noqa: E402
from aifred_brain.metric_relevance import (  # noqa: E402
    MetricFamily,
    UserIntentCategory,
    classify_user_intent,
    select_relevant_metric_families,
)
from aifred_brain.progress_memory import (  # noqa: E402
    calculate_progress_memory,
    progress_memory_to_dict,
)
from aifred_brain.reference_compare import compare_packet_to_reference  # noqa: E402
from aifred_brain.report_writer import (  # noqa: E402
    ReportFormat,
    render_html_report,
    render_text_report,
    write_report,
)
from aifred_brain.stereo_metrics import StereoMetrics, calculate_stereo_metrics  # noqa: E402
from aifred_brain.tonal_balance import (  # noqa: E402
    TonalBalanceMetrics,
    calculate_tonal_balance_metrics,
)
from aifred_brain.transient_metrics import TransientMetrics, calculate_transient_metrics  # noqa: E402


def synthetic_sine(frequency_hz: float = 100.0, sample_rate: int = 1000, frames: int = 256) -> tuple[float, ...]:
    return tuple(0.5 * math.sin(2.0 * math.pi * frequency_hz * index / sample_rate) for index in range(frames))


def synthetic_stereo_signal() -> tuple[tuple[float, ...], tuple[float, ...], int]:
    sample_rate = 1000
    left = synthetic_sine(100.0, sample_rate, 256)
    right = tuple(sample * 0.75 for sample in left)
    interleaved: list[float] = []
    for left_sample, right_sample in zip(left, right):
        interleaved.extend((left_sample, right_sample))
    return tuple(interleaved), left, sample_rate


def metric_fact(family: MetricFamily | str, name: str, value: object, unit: str | None = None) -> dict[str, object]:
    return {
        "family": family.value if isinstance(family, MetricFamily) else str(family),
        "name": name,
        "value": value,
        "unit": unit,
        "available": True,
        "limitations": [],
    }


def packet_dict(
    facts: list[dict[str, object]],
    *,
    mode: str = "analyze",
    source_label: str = "File Analysis",
    session_label: str = "synthetic-session",
) -> dict[str, object]:
    return {
        "question": "Synthetic factual packet",
        "mode": mode,
        "source_label": source_label,
        "confidence": "High",
        "freshness": "recent",
        "availability": "ready",
        "metric_families": sorted({str(fact["family"]) for fact in facts}),
        "facts": facts,
        "limitations": [],
        "warnings": [],
        "metadata": {"path": r"C:\Private\Session\mix.wav"},
        "session_label": session_label,
    }


def plain(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: plain(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [plain(item) for item in value]
    return value


def assert_json_serializable(testcase: unittest.TestCase, value: object) -> None:
    json.dumps(plain(value), sort_keys=True)


def assert_no_fake_value(testcase: unittest.TestCase, value: object) -> None:
    payload = plain(value)
    if isinstance(payload, dict):
        for item in payload.values():
            assert_no_fake_value(testcase, item)
    elif isinstance(payload, list):
        for item in payload:
            assert_no_fake_value(testcase, item)
    elif isinstance(payload, (int, float)) and not isinstance(payload, bool):
        testcase.assertNotEqual(float(payload), -999.0)


def assert_no_advice_text(testcase: unittest.TestCase, value: object) -> None:
    text = json.dumps(plain(value), sort_keys=True).lower()
    forbidden = (
        "you should",
        "try ",
        "fix ",
        "recommend",
        "advice",
        "better mix",
        "next practical move",
        "make it sound",
        "too loud",
        "smashed",
    )
    testcase.assertFalse(any(phrase in text for phrase in forbidden), text)


def assert_no_subjective_labels(testcase: unittest.TestCase, value: object) -> None:
    text = json.dumps(plain(value), sort_keys=True).lower()
    forbidden = ("warm", "thin", "muddy", "harsh", "polished", "professional", "weak", "stronger")
    testcase.assertFalse(any(phrase in text for phrase in forbidden), text)


def assert_no_private_path(testcase: unittest.TestCase, value: object) -> None:
    text = json.dumps(plain(value), sort_keys=True)
    testcase.assertNotIn(r"C:\Private\Session", text)


class TruthLayerIntegrationTests(unittest.TestCase):
    def test_synthetic_stereo_signal_pipeline(self) -> None:
        interleaved, mono, sample_rate = synthetic_stereo_signal()

        level = calculate_level_metrics(interleaved)
        stereo = calculate_stereo_metrics(interleaved, channels=2)
        frequency = calculate_frequency_metrics(mono, sample_rate)
        magnitudes = calculate_dft_magnitudes(mono, sample_rate)
        tonal = calculate_tonal_balance_metrics(frequency, magnitudes=magnitudes)
        dynamics = calculate_dynamics_metrics(mono, sample_rate, window_seconds=0.050)
        transients = calculate_transient_metrics((0.0, 0.1, 0.6, 0.2, 0.7), sample_rate, threshold=0.25)

        self.assertIsInstance(level, LevelMetrics)
        self.assertIsInstance(stereo, StereoMetrics)
        self.assertIsInstance(frequency, FrequencyMetrics)
        self.assertIsInstance(tonal, TonalBalanceMetrics)
        self.assertTrue(hasattr(dynamics, "window_count"))
        self.assertIsInstance(transients, TransientMetrics)
        self.assertIsNone(calculate_level_metrics(()).sample_peak_dbfs)
        self.assertIsNone(calculate_stereo_metrics((), channels=2).correlation)
        self.assertFalse(calculate_dynamics_metrics((), sample_rate).available)

        for output in (level, stereo, frequency, tonal, dynamics, transients):
            assert_no_fake_value(self, output)
            assert_no_advice_text(self, output)
            assert_no_subjective_labels(self, output)

    def test_analysis_result_assembly(self) -> None:
        interleaved, mono, sample_rate = synthetic_stereo_signal()
        level = calculate_level_metrics(interleaved)
        stereo = calculate_stereo_metrics(interleaved, channels=2)
        frequency = calculate_frequency_metrics(mono, sample_rate)

        context = create_analysis_context(
            "analyze",
            "File Analysis",
            confidence="High",
            freshness="recent",
            sample_rate=sample_rate,
            duration_seconds=len(mono) / sample_rate,
        )
        bundle = create_analysis_metric_bundle(level=level, stereo=stereo, frequency=frequency)
        result = create_analysis_result(context, bundle, metadata={"path": r"C:\Private\Session\mix.wav"})
        empty = create_analysis_result(context, create_analysis_metric_bundle())
        limited = create_analysis_result(context, bundle, limitations=("synthetic short window",))
        payload = analysis_result_to_dict(result)

        self.assertEqual(result.context.mode.value, "analyze")
        self.assertEqual(result.context.source.value, "File Analysis")
        self.assertEqual(result.metrics.level, level)
        self.assertEqual(empty.availability, AnalysisAvailability.UNAVAILABLE)
        self.assertEqual(limited.availability, AnalysisAvailability.LIMITED)
        assert_json_serializable(self, payload)
        assert_no_fake_value(self, payload)
        assert_no_private_path(self, payload)

    def test_metric_relevance_to_packet_pipeline(self) -> None:
        question = "Should I add saturation to this vocal?"
        intent = classify_user_intent(question)
        relevance = select_relevant_metric_families(
            intent,
            mode="analyze",
            available_metrics=(
                MetricFamily.LEVEL,
                MetricFamily.FREQUENCY,
                MetricFamily.TONAL_BALANCE,
                MetricFamily.DYNAMICS,
                MetricFamily.TRANSIENTS,
            ),
        )
        context = create_analysis_context("analyze", "File Analysis", confidence="Medium", freshness="recent")
        facts = (
            create_metric_fact(MetricFamily.LEVEL, "sample_peak_dbfs", -3.0, "dBFS"),
            create_metric_fact(MetricFamily.TONAL_BALANCE, "tilt_value", 0.1, None),
        )
        packet = create_interpretation_packet(
            question,
            context,
            relevance,
            facts=facts,
            metadata={"path": r"C:\Private\Session\vocal.wav"},
        )
        payload = packet_to_dict(packet)

        self.assertEqual(intent, UserIntentCategory.SATURATION)
        self.assertIn(MetricFamily.TONAL_BALANCE, relevance.primary_metrics)
        self.assertIn(MetricFamily.FREQUENCY, relevance.primary_metrics)
        self.assertIn("tonal_balance", payload["metric_families"])
        self.assertTrue(payload["facts"])
        assert_json_serializable(self, payload)
        assert_no_fake_value(self, payload)
        assert_no_advice_text(self, payload)
        assert_no_private_path(self, payload)

    def test_report_writer_from_packet(self) -> None:
        packet = packet_dict(
            [
                metric_fact(MetricFamily.LEVEL, "sample_peak_dbfs", -3.0, "dBFS"),
                metric_fact(MetricFamily.STEREO, "correlation", 0.0, None),
            ],
            session_label="unsafe <session>",
        )
        packet["question"] = "Check <script>alert('x')</script>"

        text_report = render_text_report(packet)
        html_report = render_html_report(packet)

        self.assertIn("Mode: analyze", text_report)
        self.assertIn("Source: File Analysis", text_report)
        self.assertIn("level.sample_peak_dbfs", text_report)
        self.assertIn("&lt;script&gt;alert", html_report)
        self.assertNotIn("<script>alert", html_report)
        assert_no_private_path(self, text_report)
        assert_no_private_path(self, html_report)
        assert_no_fake_value(self, packet)
        assert_no_advice_text(self, text_report)
        assert_no_advice_text(self, html_report)

        with tempfile.TemporaryDirectory() as tmpdir:
            txt_result = write_report(packet, tmpdir, ReportFormat.TEXT)
            html_result = write_report(packet, tmpdir, ReportFormat.HTML)
            self.assertTrue(txt_result.created)
            self.assertTrue(html_result.created)
            self.assertTrue(txt_result.path.exists())
            self.assertTrue(html_result.path.exists())
            self.assertIn("File Analysis", txt_result.path.read_text(encoding="utf-8"))
            written_html = html_result.path.read_text(encoding="utf-8")
            self.assertIn("<td>level</td>", written_html)
            self.assertIn("<td>sample_peak_dbfs</td>", written_html)

    def test_compare_ab_and_reference_separation(self) -> None:
        current_packet = packet_dict(
            [
                metric_fact(MetricFamily.LEVEL, "sample_peak_dbfs", 0.0, "dBFS"),
                metric_fact(MetricFamily.STEREO, "correlation", 0.5, None),
            ],
            mode="compare",
            source_label="Compare A/B",
        )
        target_packet = packet_dict(
            [
                metric_fact(MetricFamily.LEVEL, "sample_peak_dbfs", -1.0, "dBFS"),
                metric_fact(MetricFamily.STEREO, "correlation", 0.25, None),
            ],
            mode="reference",
            source_label="Reference Mode",
        )

        compare_result = compare_packet_facts(current_packet, target_packet)
        reference_result = compare_packet_to_reference(current_packet, target_packet)

        self.assertEqual(compare_result.mode, "Compare A/B")
        self.assertEqual(reference_result.mode, "Reference")
        self.assertNotEqual(reference_result.mode, "Compare A/B")
        self.assertEqual(compare_result.comparisons[0].a_value, 0.0)
        self.assertEqual(reference_result.comparisons[0].current_value, 0.0)

        for result in (compare_result, reference_result):
            text = json.dumps(plain(result), sort_keys=True).lower()
            self.assertNotIn("reference pool", text)
            self.assertNotIn("better mix", text)
            assert_no_fake_value(self, result)
            assert_no_advice_text(self, result)

    def test_export_history_and_progress_memory_pipeline(self) -> None:
        first_packet = packet_dict(
            [
                metric_fact(MetricFamily.LEVEL, "sample_peak_dbfs", -4.0, "dBFS"),
                metric_fact(MetricFamily.STEREO, "correlation", 0.0, None),
            ],
            session_label="mix-a",
        )
        first_packet["timestamp_utc"] = "2026-01-01T00:00:00Z"
        second_packet = packet_dict(
            [
                metric_fact(MetricFamily.LEVEL, "sample_peak_dbfs", -3.0, "dBFS"),
                metric_fact(MetricFamily.DYNAMICS, "dynamic_range_db", 6.0, "dB"),
            ],
            session_label="mix-a",
        )
        second_packet["timestamp_utc"] = "2026-01-02T00:00:00Z"

        first_record = create_export_record(first_packet)
        second_record = create_export_record(second_packet)
        history = append_export_record(append_export_record(ExportHistory(), first_record), second_record)

        with tempfile.TemporaryDirectory() as tmpdir:
            history_path = Path(tmpdir) / "history.json"
            save_export_history(history, history_path)
            loaded = load_export_history(history_path)

        delta = compare_latest_exports(loaded)
        memory = calculate_progress_memory(loaded)
        history_payload = export_history_to_dict(loaded)
        memory_payload = progress_memory_to_dict(memory)

        self.assertEqual(len(loaded.records), 2)
        self.assertIn("level.sample_peak_dbfs", delta.changed_metric_names)
        self.assertIn("dynamics.dynamic_range_db", delta.added_metric_names)
        self.assertIn("stereo.correlation", delta.removed_metric_names)
        self.assertEqual(memory.export_count, 2)
        level_trends = [trend for trend in memory.metric_trends if trend.name == "sample_peak_dbfs"]
        self.assertEqual(level_trends[0].delta, 1.0)

        for payload in (history_payload, memory_payload):
            assert_json_serializable(self, payload)
            assert_no_fake_value(self, payload)
            assert_no_advice_text(self, payload)
            assert_no_subjective_labels(self, payload)
            assert_no_private_path(self, payload)


if __name__ == "__main__":
    unittest.main()
