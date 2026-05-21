"""Export history helpers for factual local session records.

Responsibility:
    Store and retrieve privacy-safe export records derived from approved
    factual packets or packet-like dictionaries.

This module must not implement AI memory, progress coaching, advice, reference
comparison, compare analysis, or fake metric values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from .privacy import redact_private_path, scrub_private_metadata


@dataclass(frozen=True)
class ExportRecord:
    """One privacy-safe factual export record."""

    export_id: str
    timestamp_utc: str
    session_label: str | None
    source_label: str | None
    mode: str | None
    metrics: dict[str, object]
    limitations: tuple[str, ...]
    warnings: tuple[str, ...]
    metadata: dict[str, object]


@dataclass(frozen=True)
class ExportHistory:
    """Immutable collection of factual export records."""

    records: tuple[ExportRecord, ...] = ()


@dataclass(frozen=True)
class ExportHistoryDelta:
    """High-level factual difference between the latest two export records."""

    previous_export_id: str | None
    current_export_id: str | None
    changed_metric_names: tuple[str, ...]
    added_metric_names: tuple[str, ...]
    removed_metric_names: tuple[str, ...]
    limitations: tuple[str, ...]


_UNSAFE_ID_CHARS = re.compile(r"[^a-zA-Z0-9_.-]+")


def _enum_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    return value


def _get_value(packet: object, key: str, default: object = None) -> object:
    if isinstance(packet, Mapping):
        return packet.get(key, default)
    return getattr(packet, key, default)


def _as_sequence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError:
        return (value,)


def _reject_fake_value(value: object) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) == -999.0:
        raise ValueError("Export history must not preserve fake placeholder metric values.")
    if isinstance(value, Mapping):
        for nested_value in value.values():
            _reject_fake_value(nested_value)
    elif isinstance(value, (list, tuple, set)):
        for nested_value in value:
            _reject_fake_value(nested_value)


def _json_safe(value: object) -> object:
    value = _enum_value(value)
    _reject_fake_value(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(nested_value) for key, nested_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=str)]
    if isinstance(value, str):
        return redact_private_path(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact_private_path(str(value))


def _normalize_redaction(value: object) -> object:
    if isinstance(value, str):
        return value.replace("<private-path><private-path>/", "<private-path>/")
    if isinstance(value, Mapping):
        return {str(key): _normalize_redaction(nested_value) for key, nested_value in value.items()}
    if isinstance(value, list):
        return [_normalize_redaction(item) for item in value]
    return value


def _safe_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    return dict(_normalize_redaction(scrub_private_metadata(dict(metadata))))


def _current_timestamp_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_label(value: str | None) -> str:
    if value is None or not str(value).strip():
        return "export"
    redacted = redact_private_path(str(value).strip())
    safe = _UNSAFE_ID_CHARS.sub("-", redacted).strip("-._").lower()
    return safe or "export"


def generate_export_id(timestamp_utc: str | None = None, session_label: str | None = None) -> str:
    """Generate a deterministic-enough export id from timestamp and label."""
    timestamp = timestamp_utc or _current_timestamp_utc()
    timestamp_part = _UNSAFE_ID_CHARS.sub("-", timestamp).strip("-._").lower()
    return f"{_safe_label(session_label)}-{timestamp_part}"


def _fact_value(fact: object, key: str, default: object = None) -> object:
    if isinstance(fact, Mapping):
        return fact.get(key, default)
    return getattr(fact, key, default)


def _metric_name(fact: object) -> str:
    family = _enum_value(_fact_value(fact, "family"))
    name = _fact_value(fact, "name", "")
    if family:
        return f"{family}.{name}"
    return str(name)


def _metrics_from_facts(facts: Sequence[object]) -> dict[str, object]:
    metrics: dict[str, object] = {}
    for fact in facts:
        value = _json_safe(_fact_value(fact, "value"))
        metric_name = _metric_name(fact)
        metrics[metric_name] = {
            "family": _json_safe(_fact_value(fact, "family")),
            "name": _json_safe(_fact_value(fact, "name")),
            "value": value,
            "unit": _json_safe(_fact_value(fact, "unit")),
            "available": bool(_fact_value(fact, "available", True)),
            "limitations": [_json_safe(item) for item in _as_sequence(_fact_value(fact, "limitations", ()))],
        }
    return metrics


def _packet_metrics(packet_or_dict: object) -> dict[str, object]:
    raw_metrics = _get_value(packet_or_dict, "metrics")
    if isinstance(raw_metrics, Mapping):
        return {str(key): _json_safe(value) for key, value in raw_metrics.items()}
    facts = _as_sequence(_get_value(packet_or_dict, "facts", ()))
    return _metrics_from_facts(facts)


def create_export_record(packet_or_dict: object, session_label: str | None = None) -> ExportRecord:
    """Create a privacy-safe factual export record from a packet-like object."""
    label_value = session_label if session_label is not None else _get_value(packet_or_dict, "session_label")
    safe_session_label = None if label_value is None else redact_private_path(str(label_value))
    timestamp = str(_get_value(packet_or_dict, "timestamp_utc", _current_timestamp_utc()))
    metadata = _get_value(packet_or_dict, "metadata", {})
    return ExportRecord(
        export_id=generate_export_id(timestamp, safe_session_label),
        timestamp_utc=timestamp,
        session_label=safe_session_label,
        source_label=None if _get_value(packet_or_dict, "source_label") is None else str(_enum_value(_get_value(packet_or_dict, "source_label"))),
        mode=None if _get_value(packet_or_dict, "mode") is None else str(_enum_value(_get_value(packet_or_dict, "mode"))),
        metrics=_packet_metrics(packet_or_dict),
        limitations=tuple(str(_json_safe(item)) for item in _as_sequence(_get_value(packet_or_dict, "limitations", ()))),
        warnings=tuple(str(_json_safe(item)) for item in _as_sequence(_get_value(packet_or_dict, "warnings", ()))),
        metadata=_safe_metadata(metadata) if isinstance(metadata, Mapping) else {},
    )


def append_export_record(history: ExportHistory | Sequence[ExportRecord], record: ExportRecord) -> ExportHistory:
    """Return a new history with `record` appended, leaving input unchanged."""
    records = history.records if isinstance(history, ExportHistory) else tuple(history)
    return ExportHistory(records=(*records, record))


def _record_to_dict(record: ExportRecord) -> dict[str, object]:
    return {
        "export_id": record.export_id,
        "timestamp_utc": record.timestamp_utc,
        "session_label": record.session_label,
        "source_label": record.source_label,
        "mode": record.mode,
        "metrics": _json_safe(record.metrics),
        "limitations": list(record.limitations),
        "warnings": list(record.warnings),
        "metadata": _safe_metadata(record.metadata),
    }


def export_history_to_dict(history: ExportHistory) -> dict[str, object]:
    """Serialize export history to a JSON-safe dictionary."""
    return {"records": [_record_to_dict(record) for record in history.records]}


def _record_from_dict(data: Mapping[str, object]) -> ExportRecord:
    metrics = data.get("metrics", {})
    metadata = data.get("metadata", {})
    return ExportRecord(
        export_id=str(data.get("export_id", "")),
        timestamp_utc=str(data.get("timestamp_utc", "")),
        session_label=None if data.get("session_label") is None else redact_private_path(str(data.get("session_label"))),
        source_label=None if data.get("source_label") is None else str(data.get("source_label")),
        mode=None if data.get("mode") is None else str(data.get("mode")),
        metrics={str(key): _json_safe(value) for key, value in dict(metrics).items()} if isinstance(metrics, Mapping) else {},
        limitations=tuple(str(_json_safe(item)) for item in _as_sequence(data.get("limitations", ()))),
        warnings=tuple(str(_json_safe(item)) for item in _as_sequence(data.get("warnings", ()))),
        metadata=_safe_metadata(metadata) if isinstance(metadata, Mapping) else {},
    )


def export_history_from_dict(data: dict[str, object]) -> ExportHistory:
    """Deserialize export history from a dictionary."""
    raw_records = data.get("records", ())
    records = tuple(_record_from_dict(record) for record in _as_sequence(raw_records) if isinstance(record, Mapping))
    return ExportHistory(records=records)


def save_export_history(history: ExportHistory, path: str | Path) -> Path:
    """Save export history to a JSON file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = export_history_to_dict(history)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def load_export_history(path: str | Path | None = None) -> ExportHistory:
    """Load export history from a JSON file, or return empty if absent."""
    if path is None:
        return ExportHistory()
    source = Path(path)
    if not source.exists():
        return ExportHistory()
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return ExportHistory()
    return export_history_from_dict(data)


def _metric_value(metric_payload: object) -> object:
    if isinstance(metric_payload, Mapping) and "value" in metric_payload:
        return metric_payload["value"]
    return metric_payload


def compare_latest_exports(history: ExportHistory) -> ExportHistoryDelta:
    """Compare metric names and raw metric values for the latest two records."""
    if len(history.records) < 2:
        limitation = "At least two export records are required for latest export comparison."
        current_id = history.records[-1].export_id if history.records else None
        return ExportHistoryDelta(
            previous_export_id=None,
            current_export_id=current_id,
            changed_metric_names=(),
            added_metric_names=(),
            removed_metric_names=(),
            limitations=(limitation,),
        )

    previous = history.records[-2]
    current = history.records[-1]
    previous_names = set(previous.metrics)
    current_names = set(current.metrics)
    shared_names = previous_names & current_names
    changed = tuple(
        sorted(
            name
            for name in shared_names
            if _metric_value(previous.metrics[name]) != _metric_value(current.metrics[name])
        )
    )
    return ExportHistoryDelta(
        previous_export_id=previous.export_id,
        current_export_id=current.export_id,
        changed_metric_names=changed,
        added_metric_names=tuple(sorted(current_names - previous_names)),
        removed_metric_names=tuple(sorted(previous_names - current_names)),
        limitations=(),
    )
