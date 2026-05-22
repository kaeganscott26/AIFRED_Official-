"""AI response validation guardrails.

These helpers validate structured AI-layer results against the current
contracts. They do not call providers, generate responses, or interpret
metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import re
from typing import Any, Mapping

from ai_engine.adapters.base import AIAdapterStatus, AIInterpretationResult


class AIResponseValidationSeverity(str, Enum):
    """Severity for response validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class AIResponseValidationIssue:
    """Single response contract issue."""

    severity: AIResponseValidationSeverity
    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True)
class AIResponseValidationResult:
    """Validation result for an AI interpretation result."""

    is_valid: bool
    issues: tuple[AIResponseValidationIssue, ...]
    error_count: int
    warning_count: int


_WINDOWS_PATH_PATTERN = re.compile(r"[A-Za-z]:\\[^\s\"'<>|]+")
_UNIX_PATH_PATTERN = re.compile(r"/(?:Users|home|var|tmp|mnt|Volumes)/[^\s\"'<>|]+")
_FALLBACK_STATUS_TEXT = "AI interpretation is unavailable. Factual metrics and reports remain available."

_FORBIDDEN_PHRASES: tuple[tuple[str, str], ...] = (
    ("your mix is too loud", "forbidden_advice_text"),
    ("you should reduce compression", "forbidden_advice_text"),
    ("this sounds professional", "forbidden_subjective_text"),
    ("mix a is better", "forbidden_compare_judgment"),
    ("add saturation", "forbidden_advice_text"),
    ("the vocals are harsh", "forbidden_subjective_text"),
)


def validate_ai_interpretation_result(
    result: AIInterpretationResult,
    packet: object | None = None,
) -> AIResponseValidationResult:
    """Validate an AI result for structure, privacy, and contract safety."""
    issues: list[AIResponseValidationIssue] = []
    issues.extend(validate_status_consistency(result))
    issues.extend(validate_mode_alignment(result, packet))
    issues.extend(validate_source_alignment(result, packet))
    issues.extend(find_forbidden_response_text(result.response_text))
    issues.extend(_validate_no_ai_text(result))
    issues.extend(_validate_mode_text_rules(result))
    issues.extend(_validate_metric_claims_against_packet(result, packet))
    issues.extend(detect_fake_metric_values(result))
    issues.extend(detect_private_path_leak(result))

    errors = sum(1 for issue in issues if issue.severity == AIResponseValidationSeverity.ERROR)
    warnings = sum(1 for issue in issues if issue.severity == AIResponseValidationSeverity.WARNING)
    return AIResponseValidationResult(
        is_valid=errors == 0,
        issues=tuple(issues),
        error_count=errors,
        warning_count=warnings,
    )


def find_forbidden_response_text(text: str) -> tuple[AIResponseValidationIssue, ...]:
    """Return issues for obvious prohibited response text."""
    normalized = _normalize_text(text)
    issues: list[AIResponseValidationIssue] = []
    for phrase, code in _FORBIDDEN_PHRASES:
        if phrase in normalized:
            issues.append(
                AIResponseValidationIssue(
                    severity=AIResponseValidationSeverity.ERROR,
                    code=code,
                    message=f"Response text contains forbidden phrase: {phrase}",
                    field="response_text",
                )
            )
    return tuple(issues)


def detect_fake_metric_values(value: object) -> tuple[AIResponseValidationIssue, ...]:
    """Detect fake placeholder metric values such as -999 in nested values."""
    issues: list[AIResponseValidationIssue] = []
    for field, item in _walk_values(value):
        if isinstance(item, bool):
            continue
        if isinstance(item, (int, float)) and float(item) == -999.0:
            issues.append(_issue("fake_metric_value", "Fake metric placeholder -999 is not allowed.", field))
        elif isinstance(item, str) and "-999" in item:
            issues.append(_issue("fake_metric_value", "Fake metric placeholder -999 is not allowed.", field))
    return tuple(issues)


def detect_private_path_leak(value: object) -> tuple[AIResponseValidationIssue, ...]:
    """Detect obvious private local path leaks in nested values."""
    issues: list[AIResponseValidationIssue] = []
    for field, item in _walk_values(value):
        if not isinstance(item, str):
            continue
        if _WINDOWS_PATH_PATTERN.search(item) or _UNIX_PATH_PATTERN.search(item):
            issues.append(
                _issue(
                    "private_path_leak",
                    "Response result contains an exposed local/private path.",
                    field,
                )
            )
    return tuple(issues)


def validate_mode_alignment(
    result: AIInterpretationResult,
    packet: object | None = None,
) -> tuple[AIResponseValidationIssue, ...]:
    """Validate result mode against packet mode when available."""
    packet_mode = _packet_value(packet, "mode") if packet is not None else None
    if packet_mode is None:
        return ()
    result_mode = _coerce_optional_text(result.mode)
    expected = _coerce_optional_text(packet_mode)
    if result_mode is None:
        return (
            AIResponseValidationIssue(
                severity=AIResponseValidationSeverity.WARNING,
                code="missing_result_mode",
                message="Packet mode exists but result mode is missing.",
                field="mode",
            ),
        )
    if _normalize_mode(result_mode) != _normalize_mode(expected):
        return (
            AIResponseValidationIssue(
                severity=AIResponseValidationSeverity.ERROR,
                code="mode_mismatch",
                message="Result mode does not match packet mode.",
                field="mode",
            ),
        )
    return ()


def validate_source_alignment(
    result: AIInterpretationResult,
    packet: object | None = None,
) -> tuple[AIResponseValidationIssue, ...]:
    """Validate result source label against packet source label when available."""
    packet_source = _packet_value(packet, "source_label") if packet is not None else None
    if packet_source is None:
        return ()
    result_source = _coerce_optional_text(result.source_label)
    expected = _coerce_optional_text(packet_source)
    if result_source is None:
        return (
            AIResponseValidationIssue(
                severity=AIResponseValidationSeverity.WARNING,
                code="missing_result_source",
                message="Packet source label exists but result source label is missing.",
                field="source_label",
            ),
        )
    if result_source != expected:
        return (
            AIResponseValidationIssue(
                severity=AIResponseValidationSeverity.ERROR,
                code="source_mismatch",
                message="Result source label does not match packet source label.",
                field="source_label",
            ),
        )
    return ()


def validate_status_consistency(result: AIInterpretationResult) -> tuple[AIResponseValidationIssue, ...]:
    """Validate status-specific response rules."""
    issues: list[AIResponseValidationIssue] = []
    text = result.response_text.strip()
    if result.status == AIAdapterStatus.READY and not text:
        issues.append(_issue("ready_requires_text", "READY status requires generated response text.", "response_text"))
    if result.status == AIAdapterStatus.NO_AI_CONFIGURED:
        if result.raw_response_available:
            issues.append(_issue("no_ai_raw_response", "No-AI fallback must not expose a raw provider response.", "raw_response_available"))
        if text and text != _FALLBACK_STATUS_TEXT:
            issues.append(_issue("no_ai_not_status_only", "No-AI fallback response text must be status-only.", "response_text"))
    if result.status in {AIAdapterStatus.ERROR, AIAdapterStatus.TIMEOUT}:
        if result.raw_response_available:
            issues.append(_issue("failure_raw_response", "ERROR/TIMEOUT must not expose a raw provider response.", "raw_response_available"))
        if _looks_like_interpretation(text):
            issues.append(_issue("failure_pretends_ready", "ERROR/TIMEOUT must not pretend to be interpretation.", "response_text"))
    return tuple(issues)


def _validate_no_ai_text(result: AIInterpretationResult) -> tuple[AIResponseValidationIssue, ...]:
    if result.status != AIAdapterStatus.NO_AI_CONFIGURED:
        return ()
    if find_forbidden_response_text(result.response_text):
        return (
            _issue(
                "no_ai_advice_text",
                "No-AI/status-only results must not contain advice text.",
                "response_text",
            ),
        )
    return ()


def _validate_mode_text_rules(result: AIInterpretationResult) -> tuple[AIResponseValidationIssue, ...]:
    text = _normalize_text(result.response_text)
    mode = _normalize_mode(result.mode)
    issues: list[AIResponseValidationIssue] = []
    if mode == "analyze" and "reference pool" in text:
        issues.append(_issue("analyze_reference_pool_leak", "Analyze Mode must not reference the global reference pool by default.", "response_text"))
    if mode == "compare" and ("b is reference" in text or "b is a reference" in text or "mix b is reference" in text or "mix b is a reference" in text):
        issues.append(_issue("compare_b_reference_leak", "Compare Mode must not call B a reference by default.", "response_text"))
    return tuple(issues)


def _validate_metric_claims_against_packet(
    result: AIInterpretationResult,
    packet: object | None,
) -> tuple[AIResponseValidationIssue, ...]:
    text = _normalize_text(result.response_text)
    issues: list[AIResponseValidationIssue] = []
    fact_names = _packet_fact_names(packet)
    if "true peak" in text and not _has_named_fact(fact_names, ("true_peak", "true peak", "truepeak")):
        issues.append(_issue("missing_true_peak_fact", "Response claims true peak without a true peak fact in the packet.", "response_text"))
    if "lufs" in text and not _has_named_fact(fact_names, ("lufs", "integrated_lufs", "integrated lufs")):
        issues.append(_issue("missing_lufs_fact", "Response claims LUFS without a LUFS fact in the packet.", "response_text"))
    return tuple(issues)


def _packet_fact_names(packet: object | None) -> tuple[str, ...]:
    facts = _packet_value(packet, "facts", ()) if packet is not None else ()
    names: list[str] = []
    for fact in facts or ():
        name = _packet_value(fact, "name")
        if name is not None:
            names.append(_normalize_text(name))
        family = _packet_value(fact, "family")
        if family is not None:
            names.append(_normalize_text(family))
    return tuple(names)


def _has_named_fact(fact_names: tuple[str, ...], targets: tuple[str, ...]) -> bool:
    normalized_targets = tuple(_normalize_text(target) for target in targets)
    return any(any(target in fact_name for target in normalized_targets) for fact_name in fact_names)


def _walk_values(value: object, field: str | None = None) -> tuple[tuple[str | None, object], ...]:
    walked: list[tuple[str | None, object]] = [(field, value)]
    if isinstance(value, Mapping):
        for key, item in value.items():
            walked.extend(_walk_values(item, _join_field(field, str(key))))
    elif is_dataclass(value) and not isinstance(value, type):
        for item_field in fields(value):
            walked.extend(_walk_values(getattr(value, item_field.name), _join_field(field, item_field.name)))
    elif isinstance(value, (tuple, list, set, frozenset)):
        for index, item in enumerate(value):
            walked.extend(_walk_values(item, _join_field(field, str(index))))
    return tuple(walked)


def _packet_value(packet: object | None, key: str, default: object = None) -> object:
    if packet is None:
        return default
    if isinstance(packet, Mapping):
        return packet.get(key, default)
    return getattr(packet, key, default)


def _issue(code: str, message: str, field: str | None = None) -> AIResponseValidationIssue:
    return AIResponseValidationIssue(
        severity=AIResponseValidationSeverity.ERROR,
        code=code,
        message=message,
        field=field,
    )


def _join_field(parent: str | None, child: str) -> str:
    if parent:
        return f"{parent}.{child}"
    return child


def _coerce_optional_text(value: object) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def _normalize_mode(value: object) -> str:
    text = _normalize_text(value)
    text = text.replace("_", " ").replace("-", " ")
    if "compare" in text:
        return "compare"
    if "reference" in text:
        return "reference"
    if "analyze" in text:
        return "analyze"
    return text.strip()


def _normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(getattr(value, "value", value)).lower()).strip()


def _looks_like_interpretation(text: str) -> bool:
    normalized = _normalize_text(text)
    if not normalized:
        return False
    if normalized == _normalize_text(_FALLBACK_STATUS_TEXT):
        return False
    interpretation_markers = (
        "based on",
        "your mix",
        "mix a",
        "mix b",
        "lufs",
        "true peak",
        "stereo",
        "compression",
        "saturation",
        "vocals",
    )
    return any(marker in normalized for marker in interpretation_markers)
