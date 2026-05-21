"""Progress memory helpers for factual trend preservation.

Responsibility:
    Track metric values across approved export records without generating
    advice, coaching, subjective labels, or hidden telemetry.

This module preserves factual progress state only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any, Mapping, Sequence


class ProgressTrendAvailability(Enum):
    """Availability state for one metric trend."""

    AVAILABLE = "available"
    INSUFFICIENT_HISTORY = "insufficient_history"
    NON_NUMERIC = "non_numeric"
    MISSING = "missing"


@dataclass(frozen=True)
class MetricProgressTrend:
    """Factual numeric trend state for one metric key."""

    name: str
    family: str
    unit: str | None
    first_value: float | None
    latest_value: float | None
    delta: float | None
    absolute_delta: float | None
    percent_delta: float | None
    sample_count: int
    availability: ProgressTrendAvailability
    first_export_id: str | None = None
    latest_export_id: str | None = None
    first_timestamp_utc: str | None = None
    latest_timestamp_utc: str | None = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProgressMemory:
    """Factual progress state derived from export history records."""

    export_count: int
    first_export_id: str | None
    latest_export_id: str | None
    first_timestamp_utc: str | None
    latest_timestamp_utc: str | None
    metric_trends: tuple[MetricProgressTrend, ...]
    limitations: tuple[str, ...] = ()


def _enum_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    return value


def _get_value(source: object, key: str, default: object = None) -> object:
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _as_records(history_or_records: object) -> tuple[object, ...]:
    records = _get_value(history_or_records, "records", history_or_records)
    if records is None:
        return ()
    if isinstance(records, (str, bytes, Mapping)):
        return (records,)
    try:
        return tuple(records)  # type: ignore[arg-type]
    except TypeError:
        return (records,)


def _as_metrics(record: object) -> Mapping[str, object]:
    metrics = _get_value(record, "metrics", {})
    return metrics if isinstance(metrics, Mapping) else {}


def _metric_payload_value(payload: object) -> object:
    if isinstance(payload, Mapping) and "value" in payload:
        return payload["value"]
    return payload


def _metric_family_and_name(metric_key: str, payload: object) -> tuple[str, str]:
    family = _get_value(payload, "family")
    name = _get_value(payload, "name")
    if family is not None and name is not None:
        return str(_enum_value(family)), str(_enum_value(name))
    if "." in metric_key:
        family_part, name_part = metric_key.split(".", 1)
        return family_part, name_part
    return "", metric_key


def _metric_unit(payload: object) -> str | None:
    unit = _get_value(payload, "unit")
    if unit is None:
        return None
    return str(_enum_value(unit))


def _reject_fake_value(value: object) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) == -999.0:
        raise ValueError("Progress memory must not preserve fake placeholder metric values.")
    if isinstance(value, Mapping):
        for nested_value in value.values():
            _reject_fake_value(nested_value)
    elif isinstance(value, (list, tuple, set)):
        for nested_value in value:
            _reject_fake_value(nested_value)


def _is_numeric(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(float(value))


def extract_numeric_metric_facts(record: object) -> tuple[dict[str, object], ...]:
    """Extract numeric metric facts from an export-history-like record."""
    facts: list[dict[str, object]] = []
    for metric_key, payload in _as_metrics(record).items():
        _reject_fake_value(payload)
        value = _metric_payload_value(payload)
        if not _is_numeric(value):
            continue
        family, name = _metric_family_and_name(str(metric_key), payload)
        facts.append(
            {
                "family": family,
                "name": name,
                "unit": _metric_unit(payload),
                "value": float(value),
                "export_id": _get_value(record, "export_id"),
                "timestamp_utc": _get_value(record, "timestamp_utc"),
            }
        )
    return tuple(facts)


def collect_metric_keys(records: Sequence[object]) -> tuple[tuple[str, str], ...]:
    """Collect metric `(family, name)` keys seen across export records."""
    keys: set[tuple[str, str]] = set()
    for record in records:
        for metric_key, payload in _as_metrics(record).items():
            _reject_fake_value(payload)
            keys.add(_metric_family_and_name(str(metric_key), payload))
    return tuple(sorted(keys))


def _metric_occurrences(records: Sequence[object], family: str, name: str) -> tuple[dict[str, object], ...]:
    occurrences: list[dict[str, object]] = []
    for record in records:
        for metric_key, payload in _as_metrics(record).items():
            _reject_fake_value(payload)
            payload_family, payload_name = _metric_family_and_name(str(metric_key), payload)
            if payload_family != family or payload_name != name:
                continue
            occurrences.append(
                {
                    "value": _metric_payload_value(payload),
                    "unit": _metric_unit(payload),
                    "export_id": _get_value(record, "export_id"),
                    "timestamp_utc": _get_value(record, "timestamp_utc"),
                }
            )
    return tuple(occurrences)


def calculate_metric_progress_trend(records: Sequence[object], family: str, name: str) -> MetricProgressTrend:
    """Calculate factual first/latest/delta values for one metric."""
    record_tuple = tuple(records)
    occurrences = _metric_occurrences(record_tuple, family, name)
    units = tuple(item["unit"] for item in occurrences if item.get("unit") is not None)
    unit = str(units[0]) if units else None
    numeric = tuple(item for item in occurrences if _is_numeric(item["value"]))
    limitations: list[str] = []

    if not occurrences:
        limitations.append("Metric was not present in the provided export records.")
        return MetricProgressTrend(
            name=name,
            family=family,
            unit=unit,
            first_value=None,
            latest_value=None,
            delta=None,
            absolute_delta=None,
            percent_delta=None,
            sample_count=0,
            availability=ProgressTrendAvailability.MISSING,
            limitations=tuple(limitations),
        )

    non_numeric_count = len(occurrences) - len(numeric)
    if non_numeric_count:
        limitations.append("One or more metric values were non-numeric.")
    missing_count = len(record_tuple) - len(occurrences)
    if missing_count > 0:
        limitations.append("Metric was missing from one or more export records.")

    if not numeric:
        return MetricProgressTrend(
            name=name,
            family=family,
            unit=unit,
            first_value=None,
            latest_value=None,
            delta=None,
            absolute_delta=None,
            percent_delta=None,
            sample_count=0,
            availability=ProgressTrendAvailability.NON_NUMERIC,
            limitations=tuple(limitations),
        )

    first = numeric[0]
    latest = numeric[-1]
    first_value = float(first["value"])
    latest_value = float(latest["value"])
    if len(numeric) < 2:
        limitations.append("At least two numeric samples are required for delta calculation.")
        availability = (
            ProgressTrendAvailability.NON_NUMERIC
            if non_numeric_count and len(occurrences) > len(numeric)
            else ProgressTrendAvailability.INSUFFICIENT_HISTORY
        )
        return MetricProgressTrend(
            name=name,
            family=family,
            unit=unit,
            first_value=first_value,
            latest_value=latest_value,
            delta=None,
            absolute_delta=None,
            percent_delta=None,
            sample_count=len(numeric),
            availability=availability,
            first_export_id=None if first.get("export_id") is None else str(first["export_id"]),
            latest_export_id=None if latest.get("export_id") is None else str(latest["export_id"]),
            first_timestamp_utc=None if first.get("timestamp_utc") is None else str(first["timestamp_utc"]),
            latest_timestamp_utc=None if latest.get("timestamp_utc") is None else str(latest["timestamp_utc"]),
            limitations=tuple(limitations),
        )

    delta = latest_value - first_value
    percent_delta = None if first_value == 0.0 else (delta / first_value) * 100.0
    return MetricProgressTrend(
        name=name,
        family=family,
        unit=unit,
        first_value=first_value,
        latest_value=latest_value,
        delta=delta,
        absolute_delta=abs(delta),
        percent_delta=percent_delta,
        sample_count=len(numeric),
        availability=ProgressTrendAvailability.AVAILABLE,
        first_export_id=None if first.get("export_id") is None else str(first["export_id"]),
        latest_export_id=None if latest.get("export_id") is None else str(latest["export_id"]),
        first_timestamp_utc=None if first.get("timestamp_utc") is None else str(first["timestamp_utc"]),
        latest_timestamp_utc=None if latest.get("timestamp_utc") is None else str(latest["timestamp_utc"]),
        limitations=tuple(limitations),
    )


def calculate_progress_memory(history_or_records: object) -> ProgressMemory:
    """Calculate factual progress memory from export history or records."""
    records = _as_records(history_or_records)
    limitations: list[str] = []
    if not records:
        limitations.append("No export records were provided.")
        return ProgressMemory(
            export_count=0,
            first_export_id=None,
            latest_export_id=None,
            first_timestamp_utc=None,
            latest_timestamp_utc=None,
            metric_trends=(),
            limitations=tuple(limitations),
        )

    trends = tuple(calculate_metric_progress_trend(records, family, name) for family, name in collect_metric_keys(records))
    if len(records) < 2:
        limitations.append("At least two export records are required for progress deltas.")
    return ProgressMemory(
        export_count=len(records),
        first_export_id=None if _get_value(records[0], "export_id") is None else str(_get_value(records[0], "export_id")),
        latest_export_id=None if _get_value(records[-1], "export_id") is None else str(_get_value(records[-1], "export_id")),
        first_timestamp_utc=None
        if _get_value(records[0], "timestamp_utc") is None
        else str(_get_value(records[0], "timestamp_utc")),
        latest_timestamp_utc=None
        if _get_value(records[-1], "timestamp_utc") is None
        else str(_get_value(records[-1], "timestamp_utc")),
        metric_trends=trends,
        limitations=tuple(limitations),
    )


def _trend_to_dict(trend: MetricProgressTrend) -> dict[str, object]:
    return {
        "name": trend.name,
        "family": trend.family,
        "unit": trend.unit,
        "first_value": trend.first_value,
        "latest_value": trend.latest_value,
        "delta": trend.delta,
        "absolute_delta": trend.absolute_delta,
        "percent_delta": trend.percent_delta,
        "sample_count": trend.sample_count,
        "availability": trend.availability.value,
        "first_export_id": trend.first_export_id,
        "latest_export_id": trend.latest_export_id,
        "first_timestamp_utc": trend.first_timestamp_utc,
        "latest_timestamp_utc": trend.latest_timestamp_utc,
        "limitations": list(trend.limitations),
    }


def progress_memory_to_dict(memory: ProgressMemory) -> dict[str, object]:
    """Serialize progress memory to a JSON-safe dictionary."""
    return {
        "export_count": memory.export_count,
        "first_export_id": memory.first_export_id,
        "latest_export_id": memory.latest_export_id,
        "first_timestamp_utc": memory.first_timestamp_utc,
        "latest_timestamp_utc": memory.latest_timestamp_utc,
        "metric_trends": [_trend_to_dict(trend) for trend in memory.metric_trends],
        "limitations": list(memory.limitations),
    }


def _availability_from_value(value: object) -> ProgressTrendAvailability:
    if isinstance(value, ProgressTrendAvailability):
        return value
    try:
        return ProgressTrendAvailability(str(value))
    except ValueError:
        return ProgressTrendAvailability.MISSING


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if not _is_numeric(value):
        return None
    return float(value)


def _trend_from_dict(data: Mapping[str, object]) -> MetricProgressTrend:
    return MetricProgressTrend(
        name=str(data.get("name", "")),
        family=str(data.get("family", "")),
        unit=None if data.get("unit") is None else str(data.get("unit")),
        first_value=_optional_float(data.get("first_value")),
        latest_value=_optional_float(data.get("latest_value")),
        delta=_optional_float(data.get("delta")),
        absolute_delta=_optional_float(data.get("absolute_delta")),
        percent_delta=_optional_float(data.get("percent_delta")),
        sample_count=int(data.get("sample_count", 0)) if _is_numeric(data.get("sample_count", 0)) else 0,
        availability=_availability_from_value(data.get("availability")),
        first_export_id=None if data.get("first_export_id") is None else str(data.get("first_export_id")),
        latest_export_id=None if data.get("latest_export_id") is None else str(data.get("latest_export_id")),
        first_timestamp_utc=None
        if data.get("first_timestamp_utc") is None
        else str(data.get("first_timestamp_utc")),
        latest_timestamp_utc=None
        if data.get("latest_timestamp_utc") is None
        else str(data.get("latest_timestamp_utc")),
        limitations=tuple(str(item) for item in data.get("limitations", ()) if item is not None)
        if isinstance(data.get("limitations", ()), Sequence) and not isinstance(data.get("limitations"), (str, bytes))
        else (),
    )


def progress_memory_from_dict(data: dict[str, object]) -> ProgressMemory:
    """Deserialize progress memory from a dictionary."""
    raw_trends = data.get("metric_trends", ())
    trends = (
        tuple(_trend_from_dict(item) for item in raw_trends if isinstance(item, Mapping))
        if isinstance(raw_trends, Sequence) and not isinstance(raw_trends, (str, bytes))
        else ()
    )
    return ProgressMemory(
        export_count=int(data.get("export_count", 0)) if _is_numeric(data.get("export_count", 0)) else 0,
        first_export_id=None if data.get("first_export_id") is None else str(data.get("first_export_id")),
        latest_export_id=None if data.get("latest_export_id") is None else str(data.get("latest_export_id")),
        first_timestamp_utc=None
        if data.get("first_timestamp_utc") is None
        else str(data.get("first_timestamp_utc")),
        latest_timestamp_utc=None
        if data.get("latest_timestamp_utc") is None
        else str(data.get("latest_timestamp_utc")),
        metric_trends=trends,
        limitations=tuple(str(item) for item in data.get("limitations", ()) if item is not None)
        if isinstance(data.get("limitations", ()), Sequence) and not isinstance(data.get("limitations"), (str, bytes))
        else (),
    )


def update_progress_memory(memory: dict[str, Any], analysis_summary: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper returning serialized factual progress memory."""
    existing = progress_memory_from_dict(memory) if memory else ProgressMemory(0, None, None, None, None, ())
    records = _as_records(analysis_summary)
    if not records:
        return progress_memory_to_dict(existing)
    return progress_memory_to_dict(calculate_progress_memory(records))


def summarize_progress_trends(memory: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper that normalizes serialized progress memory."""
    return progress_memory_to_dict(progress_memory_from_dict(memory))
