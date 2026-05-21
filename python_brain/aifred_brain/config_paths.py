"""Configuration path utilities for portable local paths.

Responsibility:
    Resolve safe, portable AIFRED user-data, report, and fixture paths.

This module must not hardcode developer-machine paths or create directories
unless the caller explicitly asks with `create=True`.
"""

from __future__ import annotations

import os
from os import PathLike
from pathlib import Path
from typing import Any

AIFRED_HOME_ENV = "AIFRED_HOME"


def ensure_directory(path: Path) -> Path:
    """Create `path` and return it.

    Directory creation is intentionally explicit so path resolution functions do
    not mutate the filesystem by default.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_aifred_home(create: bool = False) -> Path:
    """Resolve the default AIFRED user-data directory.

    `AIFRED_HOME` may override the default for tests and portable installs.
    Without an override, this uses the current user's home directory without
    embedding any personal path in source.
    """
    override = os.environ.get(AIFRED_HOME_ENV)
    home = Path(override).expanduser() if override else Path.home() / ".aifred"
    return ensure_directory(home) if create else home


def get_reports_dir(create: bool = False) -> Path:
    """Resolve the default AIFRED reports directory."""
    reports_dir = get_aifred_home(create=False) / "Reports"
    return ensure_directory(reports_dir) if create else reports_dir


def get_fixtures_dir() -> Path:
    """Resolve the repository fixture directory relative to `python_brain/`."""
    return Path(__file__).resolve().parents[1] / "fixtures"


def resolve_reports_directory(*, project_directory: str | PathLike[str] | None = None) -> str:
    """Resolve an approved report directory according to the report contract."""
    if project_directory is not None:
        return str(Path(project_directory).expanduser() / "AIFRED Reports")
    return str(get_reports_dir(create=False))


def validate_portable_path(path: str | PathLike[str]) -> dict[str, Any]:
    """Validate that a path is portable and safe for intended use."""
    candidate = Path(path).expanduser()
    return {
        "path": candidate,
        "is_absolute": candidate.is_absolute(),
        "exists": candidate.exists(),
        "is_dir": candidate.is_dir(),
    }
