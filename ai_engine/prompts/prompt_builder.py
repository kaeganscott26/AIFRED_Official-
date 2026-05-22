"""Prompt context assembly stubs.

This module prepares structural packet context only. It does not call providers,
send prompts, generate final responses, or build metric-threshold templates.
"""

from __future__ import annotations

from dataclasses import dataclass, field, is_dataclass, fields
from enum import Enum
from pathlib import PurePath, PureWindowsPath
import re
from typing import Any, Mapping

_PRIVATE_PATH_PATTERN = re.compile(r"(?P<path>(?:[A-Za-z]:\\|/)[^\s\"'<>|]+)")
_SECRET_KEY_TERMS = ("api_key", "secret", "token", "password", "private_key")


@dataclass(frozen=True)
class PromptBuildResult:
    """Structural prompt context for future provider-specific builders."""

    system_context: tuple[str, ...] = field(default_factory=tuple)
    packet_context: dict[str, object] = field(default_factory=dict)
    user_question: str | None = None
    mode: str | None = None
    source_label: str | None = None
    selected_metric_families: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


def extract_prompt_packet_context(packet: object) -> dict[str, object]:
    """Extract privacy-safe prompt context from a packet-like object."""
    context: dict[str, object] = {
        "question": _safe_optional_text(_packet_value(packet, "question")),
        "mode": _safe_optional_text(_packet_value(packet, "mode")),
        "source_label": _safe_optional_text(_packet_value(packet, "source_label")),
        "freshness": _safe_optional_text(_packet_value(packet, "freshness")),
        "confidence": _safe_optional_text(_packet_value(packet, "confidence")),
        "availability": _safe_optional_text(_packet_value(packet, "availability")),
        "selected_metric_families": _safe_string_tuple(_packet_value(packet, "metric_families", ())),
        "facts": _safe_value(_packet_value(packet, "facts", ())),
        "limitations": _safe_string_tuple(_packet_value(packet, "limitations", ())),
        "warnings": _safe_string_tuple(_packet_value(packet, "warnings", ())),
    }
    missing_fields = tuple(key for key, value in context.items() if key not in {"facts", "limitations", "warnings"} and value in (None, ()))
    return {**context, "missing_fields": missing_fields}


def build_prompt_context(packet: object) -> PromptBuildResult:
    """Build structural prompt context without creating final response text."""
    packet_context = extract_prompt_packet_context(packet)
    return PromptBuildResult(
        system_context=(
            "Do not invent metrics.",
            "Use only selected metric families.",
            "Respect mode, source, freshness, and confidence.",
            "Do not expose private paths or secrets.",
            "Follow the AI response contract.",
        ),
        packet_context=packet_context,
        user_question=_optional_str(packet_context["question"]),
        mode=_optional_str(packet_context["mode"]),
        source_label=_optional_str(packet_context["source_label"]),
        selected_metric_families=tuple(str(item) for item in packet_context["selected_metric_families"]),
        limitations=tuple(str(item) for item in packet_context["limitations"]),
        warnings=tuple(str(item) for item in packet_context["warnings"]),
    )


def build_openai_prompt(packet: object) -> object:
    """Future OpenAI prompt builder."""
    del packet
    raise NotImplementedError("OpenAI prompt building is not implemented in Phase 4D.")


def build_local_prompt(packet: object) -> object:
    """Future local prompt builder."""
    del packet
    raise NotImplementedError("Local prompt building is not implemented in Phase 4D.")


def _packet_value(packet: object, key: str, default: object = None) -> object:
    if isinstance(packet, Mapping):
        return packet.get(key, default)
    return getattr(packet, key, default)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _safe_optional_text(value: object) -> str | None:
    if value is None:
        return None
    return _safe_text(value)


def _safe_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (_safe_text(value),)
    try:
        return tuple(_safe_text(item) for item in value)  # type: ignore[arg-type]
    except TypeError:
        return (_safe_text(value),)


def _safe_value(value: object, key: str | None = None) -> object:
    if key and _is_secret_key(key):
        return "[redacted]"
    if isinstance(value, Enum):
        return _safe_text(value.value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if float(value) == -999.0:
            return "[unavailable]"
        return value
    if isinstance(value, str):
        return _safe_text(value)
    if isinstance(value, Mapping):
        return {str(item_key): _safe_value(item_value, str(item_key)) for item_key, item_value in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _safe_value(getattr(value, item.name), item.name) for item in fields(value)}
    if isinstance(value, tuple):
        return tuple(_safe_value(item) for item in value)
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    return value


def _safe_text(value: object) -> str:
    text = str(getattr(value, "value", value))
    text = text.replace("-999", "[unavailable]")
    return _PRIVATE_PATH_PATTERN.sub(_redact_path_match, text)


def _is_secret_key(key: str) -> bool:
    normalized = key.lower()
    return any(term in normalized for term in _SECRET_KEY_TERMS)


def _redact_path_match(match: re.Match[str]) -> str:
    raw_path = match.group("path").rstrip(".,;:)")
    trailing = match.group("path")[len(raw_path):]
    try:
        filename = PureWindowsPath(raw_path).name or PurePath(raw_path).name
    except ValueError:
        filename = "redacted"
    return f"[redacted path]/{filename}{trailing}"
