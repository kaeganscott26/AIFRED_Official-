"""Progress memory interface for factual trend preservation.

Responsibility:
    Define contracts for tracking approved progress trends across sessions.

This module must not become user profiling or hidden telemetry.
"""

from __future__ import annotations

from typing import Any


def update_progress_memory(memory: dict[str, Any], analysis_summary: dict[str, Any]) -> dict[str, Any]:
    """Update approved progress memory with factual analysis summary data."""
    raise NotImplementedError("Progress memory update is not implemented yet.")


def summarize_progress_trends(memory: dict[str, Any]) -> dict[str, Any]:
    """Summarize factual progress trends without generating advice."""
    raise NotImplementedError("Progress trend summary is not implemented yet.")

