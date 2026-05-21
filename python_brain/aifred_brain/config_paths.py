"""Configuration path interface for portable local paths.

Responsibility:
    Define contracts for safe, portable path discovery and report destinations.

This module must not hardcode developer-machine paths.
"""

from __future__ import annotations

from os import PathLike
from typing import Any


def resolve_reports_directory(*, project_directory: str | PathLike[str] | None = None) -> str:
    """Resolve an approved report directory according to the report contract."""
    raise NotImplementedError("Report directory resolution is not implemented yet.")


def validate_portable_path(path: str | PathLike[str]) -> dict[str, Any]:
    """Validate that a path is portable and safe for intended use."""
    raise NotImplementedError("Portable path validation is not implemented yet.")

