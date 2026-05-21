"""Compare Mode interface for Mix A vs Mix B facts only.

Responsibility:
    Define contracts for direct A/B factual deltas without invoking hidden
    reference targets or global pools.
"""

from __future__ import annotations

from typing import Any


def compare_mix_a_to_mix_b(mix_a_state: dict[str, Any], mix_b_state: dict[str, Any]) -> dict[str, Any]:
    """Calculate factual deltas between Mix A and Mix B."""
    raise NotImplementedError("A/B comparison is not implemented yet.")


def validate_compare_context(context: dict[str, Any]) -> dict[str, Any]:
    """Validate that Compare Mode contains only A/B context."""
    raise NotImplementedError("Compare context validation is not implemented yet.")

