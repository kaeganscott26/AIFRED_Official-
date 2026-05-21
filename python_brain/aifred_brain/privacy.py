"""Privacy interface for safe analysis metadata.

Responsibility:
    Define contracts for removing private path, identity, and project metadata
    from user-facing or consent-controlled outputs.
"""

from __future__ import annotations

from typing import Any


def scrub_private_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove private metadata from approved factual payloads."""
    raise NotImplementedError("Private metadata scrubbing is not implemented yet.")


def require_consent_for_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Classify metadata that requires explicit consent before collection."""
    raise NotImplementedError("Consent classification is not implemented yet.")

