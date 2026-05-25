"""Safe file/JSON smoke bridge for bridge contract objects.

This module proves bridge request/response objects can survive a JSON
roundtrip. It does not run analysis, call AI providers, open sockets, send
HTTP requests, invoke subprocesses, or require real audio files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .bridge_contract import (
    BridgeAIStatus,
    BridgeAnalysisRequest,
    BridgeAnalysisResponse,
    BridgeAnalysisStatus,
    BridgeReportStatus,
    BridgeStatus,
    bridge_request_from_dict,
    bridge_request_to_dict,
    bridge_response_from_dict,
    bridge_response_to_dict,
    create_bridge_response,
    sanitize_bridge_dict,
    validate_bridge_request_shape,
    validate_bridge_response_shape,
)


SMOKE_BRIDGE_VERSION = "file-json-smoke-v0"
_SAFE_JSON_ERROR = "Invalid bridge JSON."
_SAFE_MISSING_FILE_ERROR = "Bridge JSON file not found."


def write_bridge_request_json(request: BridgeAnalysisRequest, path: str | Path) -> None:
    """Write a sanitized request JSON file at the caller-provided path."""
    issues = validate_bridge_request_shape(request)
    if issues:
        raise ValueError("Invalid bridge request shape.")
    _write_json_object(bridge_request_to_dict(request), path)


def read_bridge_request_json(path: str | Path) -> BridgeAnalysisRequest:
    """Read, sanitize, and validate a request JSON file."""
    data = _read_json_object(path)
    request = bridge_request_from_dict(sanitize_bridge_dict(data))
    issues = validate_bridge_request_shape(request)
    if issues:
        raise ValueError("Invalid bridge request JSON shape.")
    return request


def write_bridge_response_json(response: BridgeAnalysisResponse, path: str | Path) -> None:
    """Write a sanitized response JSON file at the caller-provided path."""
    issues = validate_bridge_response_shape(response)
    if issues:
        raise ValueError("Invalid bridge response shape.")
    _write_json_object(bridge_response_to_dict(response), path)


def read_bridge_response_json(path: str | Path) -> BridgeAnalysisResponse:
    """Read, sanitize, and validate a response JSON file."""
    data = _read_json_object(path)
    response = bridge_response_from_dict(sanitize_bridge_dict(data))
    issues = validate_bridge_response_shape(response)
    if issues:
        raise ValueError("Invalid bridge response JSON shape.")
    return response


def create_smoke_response_from_request(request: BridgeAnalysisRequest) -> BridgeAnalysisResponse:
    """Create a limited smoke response without executing real analysis."""
    issues = validate_bridge_request_shape(request)
    if issues:
        raise ValueError("Invalid bridge request shape.")

    report_status = BridgeReportStatus.UNAVAILABLE if request.write_reports else BridgeReportStatus.NOT_REQUESTED
    return create_bridge_response(
        request_id=request.request_id,
        bridge_status=BridgeStatus.LIMITED,
        analysis_status=BridgeAnalysisStatus.UNAVAILABLE,
        ai_status=BridgeAIStatus.NO_AI_CONFIGURED,
        report_status=report_status,
        mode=request.mode,
        lens=request.lens,
        source_label=request.source_label,
        analysis_availability="unavailable",
        analysis_result={},
        interpretation_packet={},
        ai_result={},
        validation_result={"smoke_only": True},
        reports=(),
        limitations=(
            "File/JSON bridge smoke only; factual analysis is unavailable.",
            "Real analysis, AI interpretation, reports, backend, plugin, and provider calls are not executed.",
        ),
        warnings=(),
        fallback_reason="Real analysis is not executed by the file/JSON bridge smoke runner.",
        latency_ms=0,
        bridge_version=SMOKE_BRIDGE_VERSION,
        metadata={"requested_metric_families": request.requested_metric_families},
    )


def roundtrip_bridge_request_json(request: BridgeAnalysisRequest, path: str | Path) -> BridgeAnalysisRequest:
    """Write and read a bridge request through sanitized JSON."""
    write_bridge_request_json(request, path)
    return read_bridge_request_json(path)


def roundtrip_bridge_response_json(response: BridgeAnalysisResponse, path: str | Path) -> BridgeAnalysisResponse:
    """Write and read a bridge response through sanitized JSON."""
    write_bridge_response_json(response, path)
    return read_bridge_response_json(path)


def _write_json_object(data: Mapping[str, Any], path: str | Path) -> None:
    sanitized = sanitize_bridge_dict(data)
    Path(path).write_text(json.dumps(sanitized, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json_object(path: str | Path) -> dict[str, Any]:
    json_path = Path(path)
    if not json_path.exists():
        raise FileNotFoundError(_SAFE_MISSING_FILE_ERROR)
    try:
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(_SAFE_JSON_ERROR) from exc
    if not isinstance(loaded, dict):
        raise ValueError(_SAFE_JSON_ERROR)
    return loaded
