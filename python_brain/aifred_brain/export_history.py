"""Export history interface for preserving factual session records.

Responsibility:
    Define contracts for storing and retrieving approved factual export history.

This module must not collect private paths or user identity by default.
"""

from __future__ import annotations

from typing import Any


def append_export_record(history: list[dict[str, Any]], record: dict[str, Any]) -> list[dict[str, Any]]:
    """Append a factual export record to an approved history structure."""
    raise NotImplementedError("Export history append is not implemented yet.")


def load_export_history(location_hint: str | None = None) -> list[dict[str, Any]]:
    """Load approved export history without exposing private paths."""
    raise NotImplementedError("Export history loading is not implemented yet.")

