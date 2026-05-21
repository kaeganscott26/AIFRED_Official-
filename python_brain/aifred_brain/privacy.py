"""Privacy helpers for safe analysis metadata.

Responsibility:
    Remove or reduce private path, identity, and project metadata from
    user-facing or consent-controlled outputs.
"""

from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath
from typing import Any

_WINDOWS_ABSOLUTE_PATTERN = re.compile(r"(?i)\b[a-z]:[\\/][^\s\"'<>|]+")
_UNC_PATTERN = re.compile(r"\\\\[^\s\"'<>|]+")
_POSIX_ABSOLUTE_PATTERN = re.compile(r"(?<!\w)/(?:[^\s\"'<>|]+/)*[^\s\"'<>|]+")


def is_probably_private_path(value: str) -> bool:
    """Return whether `value` looks like a local absolute path."""
    if not value:
        return False

    text = str(value)
    if text.startswith("~"):
        return True
    if _WINDOWS_ABSOLUTE_PATTERN.search(text) or _UNC_PATTERN.search(text):
        return True
    if _POSIX_ABSOLUTE_PATTERN.search(text):
        return True

    try:
        if Path(text).expanduser().is_absolute():
            return True
    except (OSError, ValueError):
        return False

    return bool(PureWindowsPath(text).drive)


def safe_display_path(path: str | Path) -> str:
    """Return a safe display name for a path without exposing parent folders."""
    name = Path(path).name
    if not name:
        name = PureWindowsPath(str(path)).name
    return name or "<path>"


def redact_private_path(value: str) -> str:
    """Redact local absolute paths from a string while preserving filenames."""
    text = str(value)

    def replace_match(match: re.Match[str]) -> str:
        return f"<private-path>/{safe_display_path(match.group(0))}"

    text = _WINDOWS_ABSOLUTE_PATTERN.sub(replace_match, text)
    text = _UNC_PATTERN.sub(replace_match, text)
    text = _POSIX_ABSOLUTE_PATTERN.sub(replace_match, text)

    if is_probably_private_path(text) and text == value:
        return f"<private-path>/{safe_display_path(value)}"
    return text


def scrub_private_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove private metadata from approved factual payloads."""
    scrubbed: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, str):
            scrubbed[key] = redact_private_path(value)
        elif isinstance(value, dict):
            scrubbed[key] = scrub_private_metadata(value)
        elif isinstance(value, list):
            scrubbed[key] = [
                redact_private_path(item) if isinstance(item, str)
                else scrub_private_metadata(item) if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            scrubbed[key] = value
    return scrubbed


def require_consent_for_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Classify metadata that requires explicit consent before collection."""
    sensitive_keys = {"path", "file_path", "project_name", "user", "username", "email"}
    requires_consent = [
        key for key, value in metadata.items()
        if key.lower() in sensitive_keys or (isinstance(value, str) and is_probably_private_path(value))
    ]
    return {
        "requires_consent": bool(requires_consent),
        "fields": requires_consent,
    }
