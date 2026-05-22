"""Prompt context assembly helpers.

This module prepares structural packet context only. It does not call providers,
send prompts, generate final responses, or build metric-threshold templates.
"""

from __future__ import annotations

from dataclasses import dataclass, field, is_dataclass, fields
from enum import Enum
from pathlib import PurePath, PureWindowsPath
import re
from typing import Any, Mapping

_PRIVATE_PATH_PATTERN = re.compile(r"(?P<path>(?:[A-Za-z]:\\|/)[^\"'<>|]+)")
_SECRET_KEY_TERMS = ("api_key", "secret", "token", "password", "private_key")
_REQUIRED_PACKET_FIELDS = (
    "question",
    "mode",
    "source_label",
    "freshness",
    "confidence",
    "availability",
    "metric_families",
    "facts",
    "limitations",
    "warnings",
    "metadata",
)


@dataclass(frozen=True)
class PromptSection:
    """Model-neutral prompt section data for future provider builders."""

    name: str
    content: object
    required: bool = True


@dataclass(frozen=True)
class PromptBuildResult:
    """Structural prompt context for future provider-specific builders."""

    system_constraints: tuple[str, ...] = field(default_factory=tuple)
    system_context: tuple[str, ...] = field(default_factory=tuple)
    packet_context: dict[str, object] = field(default_factory=dict)
    user_question: str | None = None
    mode: str | None = None
    source_label: str | None = None
    freshness: str | None = None
    confidence: str | None = None
    selected_metric_families: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    sections: tuple[PromptSection, ...] = field(default_factory=tuple)


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
        "metadata": _safe_metadata(_packet_value(packet, "metadata", {})),
        "session_label": _safe_optional_text(_packet_value(packet, "session_label")),
    }
    missing_fields = tuple(
        key
        for key in _REQUIRED_PACKET_FIELDS
        if _required_context_value(context, key) in (None, ())
    )
    return {**context, "missing_fields": missing_fields}


def build_system_constraints() -> tuple[str, ...]:
    """Return behavioral constraints as data, not final response text."""
    return (
        "Do not invent metrics.",
        "Respect active mode.",
        "Use relevant metric families.",
        "Disclose limitations.",
        "Do not expose private paths.",
        "Do not use canned responses.",
        "Preserve source label, freshness, and confidence.",
    )


def build_prompt_sections(packet: object) -> tuple[PromptSection, ...]:
    """Build model-neutral sections without creating provider prompts."""
    packet_context = extract_prompt_packet_context(packet)
    return (
        PromptSection("system_constraints", build_system_constraints(), True),
        PromptSection(
            "packet_identity",
            {
                "mode": packet_context["mode"],
                "source_label": packet_context["source_label"],
                "freshness": packet_context["freshness"],
                "confidence": packet_context["confidence"],
                "availability": packet_context["availability"],
            },
            True,
        ),
        PromptSection("user_question", packet_context["question"], True),
        PromptSection("selected_metric_families", packet_context["selected_metric_families"], True),
        PromptSection("facts", packet_context["facts"], True),
        PromptSection("limitations", packet_context["limitations"], False),
        PromptSection("warnings", packet_context["warnings"], False),
        PromptSection("metadata", packet_context["metadata"], False),
        PromptSection("missing_fields", packet_context["missing_fields"], False),
    )


def build_prompt_context(packet: object) -> PromptBuildResult:
    """Build structural prompt context without creating final response text."""
    packet_context = extract_prompt_packet_context(packet)
    system_constraints = build_system_constraints()
    return PromptBuildResult(
        system_constraints=system_constraints,
        system_context=system_constraints,
        packet_context=packet_context,
        user_question=_optional_str(packet_context["question"]),
        mode=_optional_str(packet_context["mode"]),
        source_label=_optional_str(packet_context["source_label"]),
        freshness=_optional_str(packet_context["freshness"]),
        confidence=_optional_str(packet_context["confidence"]),
        selected_metric_families=tuple(str(item) for item in packet_context["selected_metric_families"]),
        limitations=tuple(str(item) for item in packet_context["limitations"]),
        warnings=tuple(str(item) for item in packet_context["warnings"]),
        sections=build_prompt_sections(packet),
    )


def prompt_context_to_dict(context: PromptBuildResult) -> dict[str, object]:
    """Return a standard-library serializable prompt context dictionary."""
    return {
        "system_constraints": list(context.system_constraints),
        "packet_context": _to_serializable(context.packet_context),
        "user_question": context.user_question,
        "mode": context.mode,
        "source_label": context.source_label,
        "freshness": context.freshness,
        "confidence": context.confidence,
        "selected_metric_families": list(context.selected_metric_families),
        "limitations": list(context.limitations),
        "warnings": list(context.warnings),
        "sections": [_prompt_section_to_dict(section) for section in context.sections],
    }


def build_openai_prompt(packet: object) -> object:
    """Future OpenAI prompt builder."""
    del packet
    raise NotImplementedError("OpenAI prompt building is not implemented in Phase 4F.")


def build_local_prompt(packet: object) -> object:
    """Future local prompt builder."""
    del packet
    raise NotImplementedError("Local prompt building is not implemented in Phase 4F.")


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


def _safe_metadata(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    safe: dict[str, object] = {}
    for item_key, item_value in value.items():
        key = str(item_key)
        if _is_secret_key(key):
            continue
        safe[key] = _safe_value(item_value, key)
    return safe


def _required_context_value(context: Mapping[str, object], key: str) -> object:
    if key == "metric_families":
        return context.get("selected_metric_families")
    return context.get(key)


def _prompt_section_to_dict(section: PromptSection) -> dict[str, object]:
    return {
        "name": section.name,
        "content": _to_serializable(section.content),
        "required": section.required,
    }


def _to_serializable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _to_serializable(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _to_serializable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_serializable(item) for item in value]
    if isinstance(value, list):
        return [_to_serializable(item) for item in value]
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
