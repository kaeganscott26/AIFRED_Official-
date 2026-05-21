"""Transient metric interface for factual punch and transient evidence.

Responsibility:
    Define contracts for transient density, transient contrast, punch evidence,
    and transient-loss flags.

This module must not fake punch readings or recommend processing chains.
"""

from __future__ import annotations

from typing import Any


def calculate_transient_metrics(audio: Any, *, window_seconds: float | None = None) -> dict[str, Any]:
    """Calculate transient facts for approved audio input."""
    raise NotImplementedError("Transient metric calculation is not implemented yet.")


def identify_transient_flags(transient_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """Create factual transient flags from verified transient metrics."""
    raise NotImplementedError("Transient flag detection is not implemented yet.")

