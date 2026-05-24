"""Bridge request/response contract objects.

This module defines structure and JSON-safe serialization only. It does not
run analysis, call AI providers, start subprocesses, read or write files,
open sockets, send HTTP requests, or generate advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from pathlib import PurePath, PureWindowsPath
import re
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit


class BridgeMode(str, Enum):
    """Supported bridge request modes."""

    ANALYZE = "Analyze"
    COMPARE = "Compare"
    REFERENCE = "Reference"


class BridgeLens(str, Enum):
    """Future UI/analysis lens selectors."""

    TONE = "Tone"
    WIDTH = "Width"
    LOUDNESS = "Loudness"
    PUNCH = "Punch"


class BridgeStatus(str, Enum):
    """Overall bridge execution status."""

    READY = "READY"
    LIMITED = "LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    RUNNING = "RUNNING"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    NO_AI_CONFIGURED = "NO_AI_CONFIGURED"


class BridgeAnalysisStatus(str, Enum):
    """Factual analysis status, separate from AI and reports."""

    READY = "READY"
    LIMITED = "LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    STALE = "STALE"


class BridgeAIStatus(str, Enum):
    """AI interpretation status, separate from factual analysis."""

    READY = "READY"
    LIMITED = "LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    NO_AI_CONFIGURED = "NO_AI_CONFIGURED"


class BridgeReportStatus(str, Enum):
    """Report writing/export status, separate from factual analysis."""

    NOT_REQUESTED = "NOT_REQUESTED"
    READY = "READY"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class BridgeInputRef:
    """Internal input reference plus privacy-safe display label."""

    ref_id: str
    kind: str
    safe_label: str
    internal_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BridgeReportRef:
    """Report reference returned by a future bridge implementation."""

    report_id: str
    kind: str
    safe_label: str
    output_ref: str | None = None
    status: BridgeReportStatus | str = BridgeReportStatus.NOT_REQUESTED
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BridgeAnalysisRequest:
    """Structured request accepted by future bridge transports."""

    request_id: str
    mode: BridgeMode | str
    lens: BridgeLens | str
    source_label: str
    audio_input_ref: BridgeInputRef | None = None
    comparison_input_ref: BridgeInputRef | None = None
    reference_input_ref: BridgeInputRef | None = None
    question: str | None = None
    requested_metric_families: tuple[str, ...] = field(default_factory=tuple)
    snapshot_timestamp_utc: str | None = None
    timeout_ms: int | None = None
    write_reports: bool = False
    output_dir_ref: str | None = None
    privacy_flags: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BridgeAnalysisResponse:
    """Structured response returned by future bridge transports."""

    request_id: str
    bridge_status: BridgeStatus | str
    analysis_status: BridgeAnalysisStatus | str
    ai_status: BridgeAIStatus | str
    report_status: BridgeReportStatus | str
    mode: BridgeMode | str
    lens: BridgeLens | str
    source_label: str
    analysis_availability: str | None = None
    analysis_result: dict[str, Any] = field(default_factory=dict)
    interpretation_packet: dict[str, Any] = field(default_factory=dict)
    ai_result: dict[str, Any] = field(default_factory=dict)
    validation_result: dict[str, Any] = field(default_factory=dict)
    reports: tuple[BridgeReportRef, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    fallback_reason: str | None = None
    latency_ms: float | None = None
    bridge_version: str = "5B-contract"
    metadata: dict[str, Any] = field(default_factory=dict)


_WINDOWS_PATH_PATTERN = re.compile(r"(?P<path>[A-Za-z]:\\[^\s\"'<>|]+)")
_UNIX_PATH_PATTERN = re.compile(r"(?P<path>/(?:Users|home|var|tmp|mnt|Volumes)/[^\s\"'<>|]+)")
_SECRET_KEY_TERMS = ("api_key", "apikey", "secret", "token", "password", "private_key", "credential")
_STACK_TRACE_MARKERS = (
    "Traceback (most recent call last):",
    "Traceback:",
    "File \"",
    "stack trace",
)
_FORBIDDEN_TEXT = (
    "your mix is too loud",
    "you should reduce compression",
    "this sounds professional",
    "add saturation",
    "the vocals are harsh",
)


def create_bridge_request(
    *,
    request_id: str,
    mode: BridgeMode | str,
    lens: BridgeLens | str,
    source_label: str,
    audio_input_ref: BridgeInputRef | Mapping[str, Any] | None = None,
    comparison_input_ref: BridgeInputRef | Mapping[str, Any] | None = None,
    reference_input_ref: BridgeInputRef | Mapping[str, Any] | None = None,
    question: str | None = None,
    requested_metric_families: tuple[str, ...] | list[str] = (),
    snapshot_timestamp_utc: str | None = None,
    timeout_ms: int | None = None,
    write_reports: bool = False,
    output_dir_ref: str | None = None,
    privacy_flags: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> BridgeAnalysisRequest:
    """Create a bridge request without executing analysis."""
    return BridgeAnalysisRequest(
        request_id=str(request_id),
        mode=_coerce_enum_value(BridgeMode, mode),
        lens=_coerce_enum_value(BridgeLens, lens),
        source_label=str(source_label),
        audio_input_ref=_coerce_input_ref(audio_input_ref),
        comparison_input_ref=_coerce_input_ref(comparison_input_ref),
        reference_input_ref=_coerce_input_ref(reference_input_ref),
        question=question,
        requested_metric_families=tuple(str(item) for item in requested_metric_families),
        snapshot_timestamp_utc=snapshot_timestamp_utc,
        timeout_ms=timeout_ms,
        write_reports=bool(write_reports),
        output_dir_ref=output_dir_ref,
        privacy_flags=dict(privacy_flags or {}),
        metadata=dict(metadata or {}),
    )


def bridge_request_to_dict(request: BridgeAnalysisRequest) -> dict[str, Any]:
    """Return a JSON-safe, privacy-sanitized request dictionary."""
    return sanitize_bridge_dict(_dataclass_to_dict(request))


def bridge_request_from_dict(data: Mapping[str, Any]) -> BridgeAnalysisRequest:
    """Create a request object from a dictionary without executing it."""
    return create_bridge_request(
        request_id=str(data.get("request_id", "")),
        mode=_coerce_enum_value(BridgeMode, data.get("mode", "")),
        lens=_coerce_enum_value(BridgeLens, data.get("lens", "")),
        source_label=str(data.get("source_label", "")),
        audio_input_ref=_coerce_input_ref(data.get("audio_input_ref")),
        comparison_input_ref=_coerce_input_ref(data.get("comparison_input_ref")),
        reference_input_ref=_coerce_input_ref(data.get("reference_input_ref")),
        question=data.get("question"),
        requested_metric_families=tuple(data.get("requested_metric_families") or ()),
        snapshot_timestamp_utc=data.get("snapshot_timestamp_utc"),
        timeout_ms=data.get("timeout_ms"),
        write_reports=bool(data.get("write_reports", False)),
        output_dir_ref=data.get("output_dir_ref"),
        privacy_flags=data.get("privacy_flags") if isinstance(data.get("privacy_flags"), Mapping) else {},
        metadata=data.get("metadata") if isinstance(data.get("metadata"), Mapping) else {},
    )


def create_bridge_response(
    *,
    request_id: str,
    bridge_status: BridgeStatus | str,
    analysis_status: BridgeAnalysisStatus | str,
    ai_status: BridgeAIStatus | str,
    report_status: BridgeReportStatus | str,
    mode: BridgeMode | str,
    lens: BridgeLens | str,
    source_label: str,
    analysis_availability: str | None = None,
    analysis_result: Mapping[str, Any] | None = None,
    interpretation_packet: Mapping[str, Any] | None = None,
    ai_result: Mapping[str, Any] | None = None,
    validation_result: Mapping[str, Any] | None = None,
    reports: tuple[BridgeReportRef, ...] | list[BridgeReportRef | Mapping[str, Any]] = (),
    limitations: tuple[str, ...] | list[str] = (),
    warnings: tuple[str, ...] | list[str] = (),
    fallback_reason: str | None = None,
    latency_ms: float | None = None,
    bridge_version: str = "5B-contract",
    metadata: Mapping[str, Any] | None = None,
) -> BridgeAnalysisResponse:
    """Create a bridge response without executing bridge behavior."""
    return BridgeAnalysisResponse(
        request_id=str(request_id),
        bridge_status=_coerce_enum_value(BridgeStatus, bridge_status),
        analysis_status=_coerce_enum_value(BridgeAnalysisStatus, analysis_status),
        ai_status=_coerce_enum_value(BridgeAIStatus, ai_status),
        report_status=_coerce_enum_value(BridgeReportStatus, report_status),
        mode=_coerce_enum_value(BridgeMode, mode),
        lens=_coerce_enum_value(BridgeLens, lens),
        source_label=str(source_label),
        analysis_availability=analysis_availability,
        analysis_result=dict(analysis_result or {}),
        interpretation_packet=dict(interpretation_packet or {}),
        ai_result=dict(ai_result or {}),
        validation_result=dict(validation_result or {}),
        reports=tuple(_coerce_report_ref(report) for report in reports),
        limitations=tuple(str(item) for item in limitations),
        warnings=tuple(str(item) for item in warnings),
        fallback_reason=fallback_reason,
        latency_ms=latency_ms,
        bridge_version=str(bridge_version),
        metadata=dict(metadata or {}),
    )


def bridge_response_to_dict(response: BridgeAnalysisResponse) -> dict[str, Any]:
    """Return a JSON-safe, privacy-sanitized response dictionary."""
    return sanitize_bridge_dict(_dataclass_to_dict(response))


def bridge_response_from_dict(data: Mapping[str, Any]) -> BridgeAnalysisResponse:
    """Create a response object from a dictionary without executing it."""
    return create_bridge_response(
        request_id=str(data.get("request_id", "")),
        bridge_status=_coerce_enum_value(BridgeStatus, data.get("bridge_status", "")),
        analysis_status=_coerce_enum_value(BridgeAnalysisStatus, data.get("analysis_status", "")),
        ai_status=_coerce_enum_value(BridgeAIStatus, data.get("ai_status", "")),
        report_status=_coerce_enum_value(BridgeReportStatus, data.get("report_status", "")),
        mode=_coerce_enum_value(BridgeMode, data.get("mode", "")),
        lens=_coerce_enum_value(BridgeLens, data.get("lens", "")),
        source_label=str(data.get("source_label", "")),
        analysis_availability=data.get("analysis_availability"),
        analysis_result=data.get("analysis_result") if isinstance(data.get("analysis_result"), Mapping) else {},
        interpretation_packet=data.get("interpretation_packet") if isinstance(data.get("interpretation_packet"), Mapping) else {},
        ai_result=data.get("ai_result") if isinstance(data.get("ai_result"), Mapping) else {},
        validation_result=data.get("validation_result") if isinstance(data.get("validation_result"), Mapping) else {},
        reports=tuple(data.get("reports") or ()),
        limitations=tuple(data.get("limitations") or ()),
        warnings=tuple(data.get("warnings") or ()),
        fallback_reason=data.get("fallback_reason"),
        latency_ms=data.get("latency_ms"),
        bridge_version=str(data.get("bridge_version", "5B-contract")),
        metadata=data.get("metadata") if isinstance(data.get("metadata"), Mapping) else {},
    )


def validate_bridge_request_shape(request: BridgeAnalysisRequest) -> tuple[str, ...]:
    """Return request shape issues without raising for invalid mode/lens."""
    issues: list[str] = []
    mode_valid = _is_valid_enum_value(BridgeMode, request.mode)
    lens_valid = _is_valid_enum_value(BridgeLens, request.lens)

    if not request.request_id:
        issues.append("request_id is required.")
    if not mode_valid:
        issues.append("mode must be Analyze, Compare, or Reference.")
    if not lens_valid:
        issues.append("lens must be Tone, Width, Loudness, or Punch.")
    if not request.source_label:
        issues.append("source_label is required.")
    if request.timeout_ms is not None and request.timeout_ms <= 0:
        issues.append("timeout_ms must be greater than zero when provided.")

    normalized_mode = _normalized_enum_text(request.mode)
    if normalized_mode == "analyze" and request.audio_input_ref is None:
        issues.append("Analyze mode requires audio_input_ref.")
    if normalized_mode == "compare":
        if request.audio_input_ref is None:
            issues.append("Compare mode requires audio_input_ref for Mix A.")
        if request.comparison_input_ref is None:
            issues.append("Compare mode requires comparison_input_ref for Mix B.")
    if normalized_mode == "reference":
        if request.audio_input_ref is None:
            issues.append("Reference mode requires audio_input_ref for the current mix.")
        if request.reference_input_ref is None:
            issues.append("Reference mode requires reference_input_ref for the target.")

    return tuple(issues)


def validate_bridge_response_shape(response: BridgeAnalysisResponse) -> tuple[str, ...]:
    """Return response shape issues without collapsing independent statuses."""
    issues: list[str] = []
    if not response.request_id:
        issues.append("request_id is required.")
    if not _is_valid_enum_value(BridgeStatus, response.bridge_status):
        issues.append("bridge_status is invalid.")
    if not _is_valid_enum_value(BridgeAnalysisStatus, response.analysis_status):
        issues.append("analysis_status is invalid.")
    if not _is_valid_enum_value(BridgeAIStatus, response.ai_status):
        issues.append("ai_status is invalid.")
    if not _is_valid_enum_value(BridgeReportStatus, response.report_status):
        issues.append("report_status is invalid.")
    if not _is_valid_enum_value(BridgeMode, response.mode):
        issues.append("mode is invalid.")
    if not _is_valid_enum_value(BridgeLens, response.lens):
        issues.append("lens is invalid.")
    if not response.source_label:
        issues.append("source_label is required.")
    if response.latency_ms is not None and response.latency_ms < 0:
        issues.append("latency_ms must not be negative.")
    return tuple(issues)


def sanitize_bridge_dict(data: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively sanitize bridge dictionaries for JSON/user-facing output."""
    return {str(key): sanitize_bridge_value(value, str(key)) for key, value in data.items()}


def sanitize_bridge_value(value: Any, key: str | None = None) -> Any:
    """Return a JSON-safe value with secrets, paths, and fake values redacted."""
    if key and _is_secret_key(key):
        return "[redacted]"
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if float(value) == -999.0:
            return "[unavailable]"
        return value
    if isinstance(value, str):
        return _sanitize_text(value)
    if is_dataclass(value) and not isinstance(value, type):
        return sanitize_bridge_dict(_dataclass_to_dict(value))
    if isinstance(value, Mapping):
        return {str(item_key): sanitize_bridge_value(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, (tuple, list)):
        return [sanitize_bridge_value(item) for item in value]
    return _sanitize_text(str(value))


def _coerce_input_ref(value: BridgeInputRef | Mapping[str, Any] | None) -> BridgeInputRef | None:
    if value is None or isinstance(value, BridgeInputRef):
        return value
    if not isinstance(value, Mapping):
        return None
    return BridgeInputRef(
        ref_id=str(value.get("ref_id", "")),
        kind=str(value.get("kind", "")),
        safe_label=str(value.get("safe_label", "")),
        internal_ref=value.get("internal_ref"),
        metadata=dict(value.get("metadata") or {}) if isinstance(value.get("metadata"), Mapping) else {},
    )


def _coerce_report_ref(value: BridgeReportRef | Mapping[str, Any]) -> BridgeReportRef:
    if isinstance(value, BridgeReportRef):
        return value
    return BridgeReportRef(
        report_id=str(value.get("report_id", "")),
        kind=str(value.get("kind", "")),
        safe_label=str(value.get("safe_label", "")),
        output_ref=value.get("output_ref"),
        status=_coerce_enum_value(BridgeReportStatus, value.get("status", BridgeReportStatus.NOT_REQUESTED)),
        warnings=tuple(str(item) for item in value.get("warnings", ()) or ()),
    )


def _coerce_enum_value(enum_type: type[Enum], value: Any) -> Enum | str:
    if isinstance(value, enum_type):
        return value
    text = str(getattr(value, "value", value))
    for option in enum_type:
        if text == option.value or text == option.name or text.lower() == option.value.lower() or text.lower() == option.name.lower():
            return option
    return text


def _is_valid_enum_value(enum_type: type[Enum], value: Any) -> bool:
    return isinstance(_coerce_enum_value(enum_type, value), enum_type)


def _normalized_enum_text(value: Any) -> str:
    text = str(getattr(value, "value", value))
    return text.strip().replace("_", " ").replace("-", " ").lower()


def _dataclass_to_dict(value: Any) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise TypeError("Expected a dataclass instance.")
    return {item.name: _to_raw_json_value(getattr(value, item.name)) for item in fields(value)}


def _to_raw_json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return _dataclass_to_dict(value)
    if isinstance(value, Mapping):
        return {str(key): _to_raw_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_to_raw_json_value(item) for item in value]
    return value


def _sanitize_text(text: str) -> str:
    sanitized = text.replace("-999", "[unavailable]")
    if _contains_forbidden_text(sanitized):
        return "[redacted unsupported advice]"
    sanitized = _redact_endpoint_credentials(sanitized)
    sanitized = _WINDOWS_PATH_PATTERN.sub(_redact_path_match, sanitized)
    sanitized = _UNIX_PATH_PATTERN.sub(_redact_path_match, sanitized)
    sanitized = _redact_stack_trace(sanitized)
    return sanitized


def _redact_endpoint_credentials(text: str) -> str:
    def replace_url(match: re.Match[str]) -> str:
        raw = match.group(0)
        try:
            parts = urlsplit(raw)
        except ValueError:
            return "[redacted endpoint]"
        if not parts.netloc or "@" not in parts.netloc:
            return raw
        host = parts.hostname or "redacted-host"
        port = f":{parts.port}" if parts.port else ""
        netloc = f"[redacted]@{host}{port}"
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))

    return re.sub(r"https?://[^\s\"'<>]+", replace_url, text)


def _redact_path_match(match: re.Match[str]) -> str:
    raw_path = match.group("path").rstrip(".,;:)")
    trailing = match.group("path")[len(raw_path):]
    try:
        filename = PureWindowsPath(raw_path).name or PurePath(raw_path).name
    except ValueError:
        filename = "redacted"
    return f"[redacted path]/{filename}{trailing}"


def _redact_stack_trace(text: str) -> str:
    if any(marker.lower() in text.lower() for marker in _STACK_TRACE_MARKERS):
        return "[redacted error detail]"
    return text


def _is_secret_key(key: str) -> bool:
    normalized = key.lower()
    return any(term in normalized for term in _SECRET_KEY_TERMS)


def _contains_forbidden_text(value: Any) -> bool:
    text = str(value).lower()
    return any(phrase in text for phrase in _FORBIDDEN_TEXT)
