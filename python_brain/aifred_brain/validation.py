"""Validation interface for factual state and failure handling.

Responsibility:
    Define contracts for validating metrics, source labels, mode boundaries,
    freshness state, and report readiness.
"""

from __future__ import annotations

from typing import Any


def validate_metric_result(metric_result: dict[str, Any]) -> dict[str, Any]:
    """Validate that a metric result is available, unavailable, stale, or limited."""
    raise NotImplementedError("Metric result validation is not implemented yet.")


def validate_mode_boundaries(state: dict[str, Any]) -> dict[str, Any]:
    """Validate Analyze, Reference, and Compare mode boundaries."""
    raise NotImplementedError("Mode boundary validation is not implemented yet.")


def validate_report_context(report_context: dict[str, Any]) -> dict[str, Any]:
    """Validate report context before writing user-facing reports."""
    raise NotImplementedError("Report context validation is not implemented yet.")

