"""No-AI fallback adapter.

This adapter returns factual fallback state only. It does not interpret metrics,
generate advice, or pretend that AI is available.
"""

from __future__ import annotations

from typing import Any

from .base import (
    AIAdapterCapability,
    AIAdapterStatus,
    AIAdapterType,
    AIInterpretationResult,
    packet_metric_families,
    packet_sequence,
    packet_value,
)

_FALLBACK_TEXT = "AI interpretation is unavailable. Factual metrics and reports remain available."
_AI_UNAVAILABLE_LIMITATION = "AI interpretation is unavailable."


class NoAIAdapter:
    """Factual no-AI fallback adapter."""

    adapter_name = "NoAIAdapter"
    adapter_type = AIAdapterType.NO_AI

    def __init__(self, fallback_enabled: bool = True) -> None:
        self.fallback_enabled = bool(fallback_enabled)

    def get_capability(self) -> AIAdapterCapability:
        """Return whether no-AI fallback is enabled."""
        return AIAdapterCapability(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            available=self.fallback_enabled,
            reason="No-AI fallback is enabled." if self.fallback_enabled else "No-AI fallback is disabled.",
            supports_streaming=False,
            supports_local=False,
            requires_api_key=False,
        )

    def interpret(self, packet: Any) -> AIInterpretationResult:
        """Return structured fallback state without interpreting packet facts."""
        packet_limitations = packet_sequence(packet, "limitations")
        packet_warnings = packet_sequence(packet, "warnings")
        missing_required = _missing_required_packet_fields(packet)
        limitations = (*packet_limitations, _AI_UNAVAILABLE_LIMITATION)
        if missing_required:
            limitations = (*limitations, f"Missing packet fields: {', '.join(missing_required)}")

        status = AIAdapterStatus.NO_AI_CONFIGURED if not missing_required else AIAdapterStatus.LIMITED
        if not self.fallback_enabled:
            status = AIAdapterStatus.UNAVAILABLE

        return AIInterpretationResult(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            status=status,
            response_text=_FALLBACK_TEXT if self.fallback_enabled else "",
            used_metric_families=packet_metric_families(packet),
            source_label=packet_value(packet, "source_label"),
            mode=packet_value(packet, "mode"),
            limitations=limitations,
            warnings=packet_warnings,
            fallback_reason="No AI adapter is configured; factual fallback state returned.",
            raw_response_available=False,
        )


def _missing_required_packet_fields(packet: Any) -> tuple[str, ...]:
    required = (
        "question",
        "mode",
        "source_label",
        "confidence",
        "freshness",
        "availability",
        "metric_families",
        "facts",
        "limitations",
        "warnings",
        "metadata",
    )
    return tuple(field for field in required if packet_value(packet, field) is None)
