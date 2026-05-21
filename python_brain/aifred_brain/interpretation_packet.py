"""Interpretation packet interface for AI input facts.

Responsibility:
    Package verified facts, mode, source labels, selected metrics, and
    limitations for the later AI interpretation layer.

This module must not generate the final AI response.
"""

from __future__ import annotations

from typing import Any


def build_interpretation_packet(
    *,
    analysis_state: dict[str, Any],
    selected_metrics: dict[str, Any],
    user_question: str | None,
) -> dict[str, Any]:
    """Build a factual packet for downstream interpretation."""
    raise NotImplementedError("Interpretation packet building is not implemented yet.")


def validate_interpretation_packet(packet: dict[str, Any]) -> dict[str, Any]:
    """Validate packet source labels, mode boundaries, and limitations."""
    raise NotImplementedError("Interpretation packet validation is not implemented yet.")

