"""Validation helpers for factual state and failure handling.

Responsibility:
    Validate file inputs and basic factual state without generating metrics or
    advice.
"""

from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import Any

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".wave"}


class AifredValidationError(ValueError):
    """Base validation error for Python Truth Layer input problems."""


class UnsupportedAudioFormatError(AifredValidationError):
    """Raised when an audio file extension is not currently supported."""


class MissingAudioFileError(AifredValidationError):
    """Raised when an expected audio file does not exist."""


class UnsupportedWavEncodingError(AifredValidationError):
    """Raised when a WAV encoding or sample width is not supported."""


class InvalidAudioBufferError(AifredValidationError):
    """Raised when decoded audio samples are not valid for metric calculation."""


def is_supported_audio_extension(path: str | PathLike[str]) -> bool:
    """Return whether `path` uses a supported audio extension."""
    return Path(path).suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS


def validate_audio_file_path(path: str | PathLike[str]) -> Path:
    """Validate that `path` exists, is a file, and is a supported WAV input."""
    candidate = Path(path).expanduser()
    if not candidate.exists():
        raise MissingAudioFileError(f"Audio file does not exist: {candidate.name or '<unknown>'}")
    if candidate.is_dir():
        raise AifredValidationError(f"Expected an audio file, got a directory: {candidate.name}")
    if not is_supported_audio_extension(candidate):
        raise UnsupportedAudioFormatError(f"Unsupported audio format: {candidate.suffix or '<none>'}")
    return candidate.resolve()


def validate_metric_result(metric_result: dict[str, Any]) -> dict[str, Any]:
    """Validate that a metric result is available, unavailable, stale, or limited."""
    state = metric_result.get("state")
    if state not in {"available", "unavailable", "stale", "limited"}:
        raise AifredValidationError("Metric result must declare a valid state.")
    if state == "available" and "value" not in metric_result:
        raise AifredValidationError("Available metric results must include a value.")
    return {"valid": True, "state": state}


def validate_mode_boundaries(state: dict[str, Any]) -> dict[str, Any]:
    """Validate Analyze, Reference, and Compare mode boundaries."""
    mode = state.get("mode")
    if mode not in {"analyze", "reference", "compare"}:
        raise AifredValidationError("Unsupported analysis mode.")
    if mode == "compare" and "reference_context" in state:
        raise AifredValidationError("Compare Mode must not include reference context.")
    if mode == "analyze" and "reference_context" in state:
        raise AifredValidationError("Analyze Mode must not include default reference context.")
    return {"valid": True, "mode": mode}


def validate_report_context(report_context: dict[str, Any]) -> dict[str, Any]:
    """Validate report context before writing user-facing reports."""
    required = {"mode", "source_label", "confidence", "limitations"}
    missing = sorted(required - set(report_context))
    if missing:
        raise AifredValidationError(f"Report context missing required fields: {', '.join(missing)}")
    return {"valid": True, "missing": []}
