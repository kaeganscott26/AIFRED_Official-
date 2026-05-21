"""Reference Mode interface for selected-target comparison facts.

Responsibility:
    Define contracts for comparing the current mix against an explicit selected
    reference, target, or approved reference pool.
"""

from __future__ import annotations

from typing import Any


def compare_to_reference(current_state: dict[str, Any], reference_state: dict[str, Any]) -> dict[str, Any]:
    """Calculate factual deltas against an explicit selected reference."""
    raise NotImplementedError("Reference comparison is not implemented yet.")


def validate_reference_context(context: dict[str, Any]) -> dict[str, Any]:
    """Validate that Reference Mode has an explicit selected target."""
    raise NotImplementedError("Reference context validation is not implemented yet.")

