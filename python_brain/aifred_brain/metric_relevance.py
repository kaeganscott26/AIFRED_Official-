"""Metric relevance interface for selecting evidence.

Responsibility:
    Select relevant factual metrics based on user question, active mode, source
    state, available data, and risk context.

This module must not dump every metric or generate final advice.
"""

from __future__ import annotations

from typing import Any


def select_relevant_metrics(
    *,
    user_question: str | None,
    mode: str,
    available_metrics: dict[str, Any],
    source_state: dict[str, Any],
) -> list[str]:
    """Select metric keys that are relevant to the current decision."""
    raise NotImplementedError("Metric relevance selection is not implemented yet.")


def explain_relevance_selection(selected_metrics: list[str]) -> list[dict[str, Any]]:
    """Create factual metadata explaining why metric evidence was selected."""
    raise NotImplementedError("Metric relevance explanation is not implemented yet.")

