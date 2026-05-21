"""Factual report writing for interpretation packets.

Responsibility:
    Render and write `.txt` and `.html` reports that preserve measured facts,
    source labels, mode, confidence, freshness, limitations, warnings, and
    privacy-safe metadata.

Reports must not invent advice or preserve fake meter values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from html import escape
from os import PathLike
from pathlib import Path
import re
from typing import Any

from .config_paths import get_reports_dir
from .privacy import is_probably_private_path, redact_private_path, safe_display_path, scrub_private_metadata


class ReportFormat(str, Enum):
    """Supported user-facing report formats."""

    TEXT = "txt"
    HTML = "html"


@dataclass(frozen=True)
class ReportWriteResult:
    """Facts about a written report file."""

    path: Path
    format: ReportFormat
    bytes_written: int
    created: bool
    safe_display_path: str


_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_WHITESPACE = re.compile(r"\s+")
_REPEATED_UNDERSCORES = re.compile(r"_+")


def _enum_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    return value


def _display_value(value: object) -> str:
    value = _enum_value(value)
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    return redact_private_path(str(value))


def _get_value(packet: object, key: str, default: object = None) -> object:
    if isinstance(packet, dict):
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


def _fact_value(fact: object, key: str, default: object = None) -> object:
    if isinstance(fact, dict):
        return fact.get(key, default)
    return getattr(fact, key, default)


def _reject_fake_value(value: object) -> None:
    if isinstance(value, (int, float)) and value == -999:
        raise ValueError("Reports must not preserve fake placeholder metric values.")
    if isinstance(value, dict):
        for nested in value.values():
            _reject_fake_value(nested)
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            _reject_fake_value(nested)


def _coerce_report_format(report_format: ReportFormat | str) -> ReportFormat:
    if isinstance(report_format, ReportFormat):
        return report_format
    normalized = str(report_format).strip().lower().lstrip(".")
    if normalized == "text":
        normalized = "txt"
    try:
        return ReportFormat(normalized)
    except ValueError as exc:
        raise ValueError(f"Unsupported report format: {report_format!r}") from exc


def sanitize_report_filename(value: str | None) -> str:
    """Return a filesystem-safe report filename stem."""
    text = "aifred-report" if value is None else str(value).strip()
    if is_probably_private_path(text):
        text = safe_display_path(text)
    text = _UNSAFE_FILENAME_CHARS.sub("_", text)
    text = _WHITESPACE.sub("_", text).strip(" ._")
    text = _REPEATED_UNDERSCORES.sub("_", text)
    return text or "aifred-report"


def generate_report_filename(session_label: str | None = None, extension: str = ".txt") -> str:
    """Generate a timestamped report filename with a safe stem."""
    ext = extension if extension.startswith(".") else f".{extension}"
    if ext.lower() not in {".txt", ".html"}:
        raise ValueError("Report filename extension must be .txt or .html.")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{sanitize_report_filename(session_label)}-{timestamp}{ext.lower()}"


def _packet_items(packet: object) -> dict[str, object]:
    metadata = _get_value(packet, "metadata", {})
    safe_metadata = scrub_private_metadata(dict(metadata)) if isinstance(metadata, dict) else {}
    facts = _as_sequence(_get_value(packet, "facts", ()))
    for fact in facts:
        _reject_fake_value(_fact_value(fact, "value"))
    return {
        "question": _get_value(packet, "question"),
        "mode": _get_value(packet, "mode"),
        "source_label": _get_value(packet, "source_label"),
        "confidence": _get_value(packet, "confidence"),
        "freshness": _get_value(packet, "freshness"),
        "availability": _get_value(packet, "availability"),
        "metric_families": _as_sequence(_get_value(packet, "metric_families", ())),
        "facts": facts,
        "limitations": _as_sequence(_get_value(packet, "limitations", ())),
        "warnings": _as_sequence(_get_value(packet, "warnings", ())),
        "metadata": safe_metadata,
        "session_label": _get_value(packet, "session_label"),
    }


def _render_fact_text(fact: object) -> str:
    family = _display_value(_fact_value(fact, "family"))
    name = _display_value(_fact_value(fact, "name"))
    value = _display_value(_fact_value(fact, "value"))
    unit = _display_value(_fact_value(fact, "unit"))
    available = _display_value(_fact_value(fact, "available", True))
    prefix = f"- {family}.{name}: " if family else f"- {name}: "
    suffix = f" {unit}" if unit else ""
    line = f"{prefix}{value}{suffix} (available: {available})"
    limitations = tuple(_display_value(item) for item in _as_sequence(_fact_value(fact, "limitations", ())))
    if limitations:
        line += f"\n  limitations: {', '.join(limitations)}"
    return line


def render_text_report(packet: object) -> str:
    """Render a factual plain-text report from a packet-like object."""
    items = _packet_items(packet)
    lines = ["AIFRED Factual Report"]
    header_fields = (
        ("Session", items["session_label"]),
        ("Question", items["question"]),
        ("Mode", items["mode"]),
        ("Source", items["source_label"]),
        ("Confidence", items["confidence"]),
        ("Freshness", items["freshness"]),
        ("Availability", items["availability"]),
    )
    for label, value in header_fields:
        text = _display_value(value)
        if text:
            lines.append(f"{label}: {text}")

    families = tuple(_display_value(family) for family in items["metric_families"])
    if families:
        lines.extend(["", "Metric Families:"])
        lines.extend(f"- {family}" for family in families if family)

    facts = tuple(items["facts"])
    if facts:
        lines.extend(["", "Facts:"])
        lines.extend(_render_fact_text(fact) for fact in facts)

    limitations = tuple(_display_value(item) for item in items["limitations"])
    if limitations:
        lines.extend(["", "Limitations:"])
        lines.extend(f"- {item}" for item in limitations if item)

    warnings = tuple(_display_value(item) for item in items["warnings"])
    if warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {item}" for item in warnings if item)

    metadata = items["metadata"]
    if isinstance(metadata, dict) and metadata:
        lines.extend(["", "Metadata:"])
        for key in sorted(metadata):
            lines.append(f"- {_display_value(key)}: {_display_value(metadata[key])}")

    return "\n".join(lines) + "\n"


def _html_row(label: str, value: object) -> str:
    return f"<tr><th>{escape(label)}</th><td>{escape(_display_value(value))}</td></tr>"


def render_html_report(packet: object) -> str:
    """Render a factual HTML report from a packet-like object."""
    items = _packet_items(packet)
    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>AIFRED Factual Report</title>",
        "</head>",
        "<body>",
        "<h1>AIFRED Factual Report</h1>",
        "<table>",
    ]
    for label, key in (
        ("Session", "session_label"),
        ("Question", "question"),
        ("Mode", "mode"),
        ("Source", "source_label"),
        ("Confidence", "confidence"),
        ("Freshness", "freshness"),
        ("Availability", "availability"),
    ):
        value = items[key]
        if _display_value(value):
            parts.append(_html_row(label, value))
    parts.append("</table>")

    families = tuple(_display_value(family) for family in items["metric_families"])
    if families:
        parts.extend(["<h2>Metric Families</h2>", "<ul>"])
        parts.extend(f"<li>{escape(family)}</li>" for family in families if family)
        parts.append("</ul>")

    facts = tuple(items["facts"])
    if facts:
        parts.extend(["<h2>Facts</h2>", "<table>", "<tr><th>Family</th><th>Name</th><th>Value</th><th>Unit</th><th>Available</th><th>Limitations</th></tr>"])
        for fact in facts:
            limitations = ", ".join(_display_value(item) for item in _as_sequence(_fact_value(fact, "limitations", ())))
            parts.append(
                "<tr>"
                f"<td>{escape(_display_value(_fact_value(fact, 'family')))}</td>"
                f"<td>{escape(_display_value(_fact_value(fact, 'name')))}</td>"
                f"<td>{escape(_display_value(_fact_value(fact, 'value')))}</td>"
                f"<td>{escape(_display_value(_fact_value(fact, 'unit')))}</td>"
                f"<td>{escape(_display_value(_fact_value(fact, 'available', True)))}</td>"
                f"<td>{escape(limitations)}</td>"
                "</tr>"
            )
        parts.append("</table>")

    for heading, key in (("Limitations", "limitations"), ("Warnings", "warnings")):
        values = tuple(_display_value(item) for item in items[key])
        if values:
            parts.extend([f"<h2>{heading}</h2>", "<ul>"])
            parts.extend(f"<li>{escape(value)}</li>" for value in values if value)
            parts.append("</ul>")

    metadata = items["metadata"]
    if isinstance(metadata, dict) and metadata:
        parts.extend(["<h2>Metadata</h2>", "<table>"])
        for key in sorted(metadata):
            parts.append(_html_row(str(key), metadata[key]))
        parts.append("</table>")

    parts.extend(["</body>", "</html>"])
    return "\n".join(parts) + "\n"


def write_report(
    packet: object,
    output_dir: str | PathLike[str] | None = None,
    report_format: ReportFormat | str = ReportFormat.TEXT,
    *,
    output_format: ReportFormat | str | None = None,
) -> ReportWriteResult:
    """Write a factual report and return write facts."""
    selected_format = _coerce_report_format(output_format if output_format is not None else report_format)
    directory = Path(output_dir) if output_dir is not None else get_reports_dir(create=False)
    directory.mkdir(parents=True, exist_ok=True)
    extension = ".html" if selected_format is ReportFormat.HTML else ".txt"
    filename = generate_report_filename(_get_value(packet, "session_label"), extension=extension)
    path = directory / filename
    content = render_html_report(packet) if selected_format is ReportFormat.HTML else render_text_report(packet)
    encoded = content.encode("utf-8")
    path.write_bytes(encoded)
    return ReportWriteResult(
        path=path,
        format=selected_format,
        bytes_written=len(encoded),
        created=path.exists(),
        safe_display_path=safe_display_path(path),
    )


def build_report_draft(report_context: dict[str, Any]) -> dict[str, Any]:
    """Build a privacy-safe factual report draft from approved context."""
    items = _packet_items(report_context)
    return dict(items)


def write_text_report(report_draft: dict[str, Any], destination: str | PathLike[str]) -> str:
    """Write a factual `.txt` report to an approved destination."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = render_text_report(report_draft)
    path.write_text(content, encoding="utf-8")
    return str(path)


def write_html_report(report_draft: dict[str, Any], destination: str | PathLike[str]) -> str:
    """Write a factual `.html` report to an approved destination."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = render_html_report(report_draft)
    path.write_text(content, encoding="utf-8")
    return str(path)
