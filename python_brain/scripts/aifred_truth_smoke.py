"""CLI smoke runner for the AIFRED Python Truth Layer.

This script exercises existing factual modules only. It does not generate AI
interpretation, advice, canned response text, plugin behavior, or new DSP
algorithms.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import tempfile
import wave
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

SCRIPT_PATH = Path(__file__).resolve()
PYTHON_BRAIN_DIR = SCRIPT_PATH.parents[1]
if str(PYTHON_BRAIN_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_BRAIN_DIR))

from aifred_brain.analysis_state import (  # noqa: E402
    analysis_result_to_dict,
    create_analysis_context,
    create_analysis_metric_bundle,
    create_analysis_result,
)
from aifred_brain.audio_loader import load_wav_buffer  # noqa: E402
from aifred_brain.dynamics_metrics import calculate_dynamics_metrics  # noqa: E402
from aifred_brain.frequency_metrics import calculate_frequency_metrics  # noqa: E402
from aifred_brain.interpretation_packet import (  # noqa: E402
    create_interpretation_packet,
    create_metric_fact,
    packet_to_dict,
)
from aifred_brain.level_metrics import calculate_level_metrics  # noqa: E402
from aifred_brain.metric_relevance import (  # noqa: E402
    MetricFamily,
    classify_user_intent,
    select_relevant_metric_families,
)
from aifred_brain.privacy import safe_display_path  # noqa: E402
from aifred_brain.report_writer import ReportFormat, write_report  # noqa: E402
from aifred_brain.stereo_metrics import calculate_stereo_metrics, split_interleaved_stereo  # noqa: E402
from aifred_brain.tonal_balance import calculate_tonal_balance_metrics  # noqa: E402
from aifred_brain.transient_metrics import calculate_transient_metrics  # noqa: E402


DEFAULT_QUESTION = "Saturation vocal check"


def _enum_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    return value


def _json_safe(value: object) -> object:
    value = _enum_value(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _json_safe(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return safe_display_path(value)
    return value


def _format_optional_float(value: float | None) -> str:
    if value is None:
        return "unavailable"
    return f"{value:.6g}"


def _write_synthetic_wav(path: Path) -> None:
    sample_rate = 8000
    frame_count = 256
    frequency_hz = 220.0
    amplitude = 0.35

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        for index in range(frame_count):
            left = amplitude * math.sin(2.0 * math.pi * frequency_hz * index / sample_rate)
            right = left * 0.75
            frames.extend(struct.pack("<h", int(max(-1.0, min(1.0, left)) * 32767)))
            frames.extend(struct.pack("<h", int(max(-1.0, min(1.0, right)) * 32767)))
        wav_file.writeframes(bytes(frames))


def _mono_samples(samples: Sequence[float], channels: int) -> tuple[float, ...]:
    if channels == 1:
        return tuple(float(sample) for sample in samples)
    left, _right = split_interleaved_stereo(samples, channels)
    return left


def _available_metric_families() -> tuple[MetricFamily, ...]:
    return (
        MetricFamily.LEVEL,
        MetricFamily.STEREO,
        MetricFamily.FREQUENCY,
        MetricFamily.TONAL_BALANCE,
        MetricFamily.DYNAMICS,
        MetricFamily.TRANSIENTS,
    )


def _create_packet_facts(level: object, stereo: object, frequency: object, tonal: object, dynamics: object, transients: object) -> tuple[object, ...]:
    return (
        create_metric_fact(MetricFamily.LEVEL, "sample_peak_dbfs", getattr(level, "sample_peak_dbfs"), "dBFS", getattr(level, "sample_peak_dbfs") is not None),
        create_metric_fact(MetricFamily.LEVEL, "rms_dbfs", getattr(level, "rms_dbfs"), "dBFS", getattr(level, "rms_dbfs") is not None),
        create_metric_fact(MetricFamily.STEREO, "correlation", getattr(stereo, "correlation"), None, getattr(stereo, "correlation") is not None),
        create_metric_fact(MetricFamily.FREQUENCY, "total_energy", getattr(frequency, "total_energy"), None, True),
        create_metric_fact(MetricFamily.TONAL_BALANCE, "low_energy_ratio", getattr(tonal, "low_energy_ratio"), None, getattr(tonal, "low_energy_ratio") is not None),
        create_metric_fact(MetricFamily.TONAL_BALANCE, "mid_energy_ratio", getattr(tonal, "mid_energy_ratio"), None, getattr(tonal, "mid_energy_ratio") is not None),
        create_metric_fact(MetricFamily.TONAL_BALANCE, "high_energy_ratio", getattr(tonal, "high_energy_ratio"), None, getattr(tonal, "high_energy_ratio") is not None),
        create_metric_fact(MetricFamily.DYNAMICS, "window_count", getattr(dynamics, "window_count"), None, True),
        create_metric_fact(MetricFamily.TRANSIENTS, "event_count", getattr(transients, "event_count"), None, True),
    )


def run_truth_smoke(input_path: Path, question: str, output_dir: Path | None, write_reports: bool) -> dict[str, object]:
    audio = load_wav_buffer(input_path)
    metadata = audio.metadata
    mono = _mono_samples(audio.samples, audio.channels)

    level = calculate_level_metrics(audio.samples)
    stereo = calculate_stereo_metrics(audio.samples, audio.channels)
    frequency = calculate_frequency_metrics(mono, audio.sample_rate)
    tonal = calculate_tonal_balance_metrics(frequency)
    dynamics = calculate_dynamics_metrics(mono, audio.sample_rate, window_seconds=0.010)
    transients = calculate_transient_metrics(mono, audio.sample_rate, threshold=0.20)

    context = create_analysis_context(
        "analyze",
        "File Analysis",
        confidence="High",
        freshness="recent",
        sample_rate=metadata.sample_rate,
        duration_seconds=metadata.duration_seconds,
    )
    metrics = create_analysis_metric_bundle(
        level=level,
        stereo=stereo,
        frequency=frequency,
        tonal_balance=tonal,
        dynamics=dynamics,
        transients=transients,
    )
    analysis = create_analysis_result(context, metrics, metadata={"input": metadata.path_display})
    intent = classify_user_intent(question)
    relevance = select_relevant_metric_families(intent, mode="analyze", available_metrics=_available_metric_families())
    packet = create_interpretation_packet(
        question,
        context,
        relevance,
        facts=_create_packet_facts(level, stereo, frequency, tonal, dynamics, transients),
        metadata={"input": metadata.path_display},
        session_label=Path(metadata.path_display).stem,
    )
    packet_payload = packet_to_dict(packet)

    written_reports: list[dict[str, object]] = []
    if write_reports:
        destination = output_dir
        if destination is None:
            destination = Path.cwd() / "aifred-smoke-reports"
        text_result = write_report(packet, destination, ReportFormat.TEXT)
        html_result = write_report(packet, destination, ReportFormat.HTML)
        written_reports = [
            {"format": text_result.format.value, "created": text_result.created, "path": text_result.safe_display_path},
            {"format": html_result.format.value, "created": html_result.created, "path": html_result.safe_display_path},
        ]

    return {
        "source_display_name": metadata.path_display,
        "sample_rate": metadata.sample_rate,
        "channels": metadata.channels,
        "duration_seconds": metadata.duration_seconds,
        "peak_dbfs": level.sample_peak_dbfs,
        "rms_dbfs": level.rms_dbfs,
        "stereo_correlation": stereo.correlation,
        "frequency_total_energy": frequency.total_energy,
        "tonal_low_ratio": tonal.low_energy_ratio,
        "tonal_mid_ratio": tonal.mid_energy_ratio,
        "tonal_high_ratio": tonal.high_energy_ratio,
        "dynamics_window_count": dynamics.window_count,
        "transient_event_count": transients.event_count,
        "packet_availability": packet.availability.value,
        "selected_metric_families": [family.value for family in (*relevance.primary_metrics, *relevance.secondary_metrics)],
        "analysis": analysis_result_to_dict(analysis),
        "packet": packet_payload,
        "reports": written_reports,
    }


def print_text_summary(summary: dict[str, object]) -> None:
    lines = [
        "AIFRED Truth Layer Smoke Summary",
        f"Source: {summary['source_display_name']}",
        f"Sample rate: {summary['sample_rate']}",
        f"Channels: {summary['channels']}",
        f"Duration seconds: {_format_optional_float(summary['duration_seconds'])}",  # type: ignore[arg-type]
        f"Peak dBFS: {_format_optional_float(summary['peak_dbfs'])}",  # type: ignore[arg-type]
        f"RMS dBFS: {_format_optional_float(summary['rms_dbfs'])}",  # type: ignore[arg-type]
        f"Stereo correlation: {_format_optional_float(summary['stereo_correlation'])}",  # type: ignore[arg-type]
        f"Frequency total energy: {_format_optional_float(summary['frequency_total_energy'])}",  # type: ignore[arg-type]
        f"Tonal low ratio: {_format_optional_float(summary['tonal_low_ratio'])}",  # type: ignore[arg-type]
        f"Tonal mid ratio: {_format_optional_float(summary['tonal_mid_ratio'])}",  # type: ignore[arg-type]
        f"Tonal high ratio: {_format_optional_float(summary['tonal_high_ratio'])}",  # type: ignore[arg-type]
        f"Dynamics window count: {summary['dynamics_window_count']}",
        f"Transient event count: {summary['transient_event_count']}",
        f"Packet availability: {summary['packet_availability']}",
        f"Selected metric families: {', '.join(str(item) for item in summary['selected_metric_families'])}",
    ]
    reports = summary.get("reports", ())
    if reports:
        lines.append("Reports:")
        for report in reports:  # type: ignore[assignment]
            lines.append(f"- {report['format']}: {report['path']}")  # type: ignore[index]
    print("\n".join(lines))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a factual AIFRED truth-layer smoke test.")
    parser.add_argument("--input", type=Path, help="Optional WAV path.")
    parser.add_argument("--question", default=DEFAULT_QUESTION, help="Optional user question for metric relevance routing.")
    parser.add_argument("--output-dir", type=Path, help="Optional report output directory.")
    parser.add_argument("--write-reports", action="store_true", help="Write factual .txt and .html reports.")
    parser.add_argument("--json", action="store_true", help="Print JSON-safe factual output.")
    parser.add_argument("--no-synthetic", action="store_true", help="Fail when no input WAV path is provided.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(argv or sys.argv[1:]))
    try:
        if args.input is None:
            if args.no_synthetic:
                print("No input WAV path was provided and synthetic input is disabled.", file=sys.stderr)
                return 2
            with tempfile.TemporaryDirectory(prefix="aifred-truth-smoke-") as tmpdir:
                synthetic_path = Path(tmpdir) / "aifred-smoke-synthetic.wav"
                _write_synthetic_wav(synthetic_path)
                summary = run_truth_smoke(synthetic_path, args.question, args.output_dir, args.write_reports)
        else:
            summary = run_truth_smoke(args.input, args.question, args.output_dir, args.write_reports)

        if args.json:
            print(json.dumps(_json_safe(summary), indent=2, sort_keys=True))
        else:
            print_text_summary(summary)
        return 0
    except Exception as exc:
        print(f"Truth layer smoke validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
