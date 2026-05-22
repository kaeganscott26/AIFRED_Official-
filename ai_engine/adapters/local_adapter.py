"""Local AI adapter stub.

No Ollama calls, LM Studio calls, endpoint calls, local model loading, or
response generation are implemented in Phase 4B.
"""

from __future__ import annotations

from typing import Any

from .base import AIAdapterCapability, AIAdapterStatus, AIAdapterType, AIInterpretationResult, packet_value


class LocalAIAdapter:
    """Unavailable local AI adapter placeholder."""

    adapter_name = "LocalAIAdapter"
    adapter_type = AIAdapterType.LOCAL

    def get_capability(self) -> AIAdapterCapability:
        """Return unavailable capability without checking local endpoints."""
        return AIAdapterCapability(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            available=False,
            reason="Local AI adapter is not implemented in Phase 4B.",
            supports_local=True,
        )

    def interpret(self, packet: Any) -> AIInterpretationResult:
        """Return structured unavailable state without calling local AI."""
        return AIInterpretationResult(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            status=AIAdapterStatus.UNAVAILABLE,
            source_label=packet_value(packet, "source_label"),
            mode=packet_value(packet, "mode"),
            limitations=("Local AI interpretation is not implemented in Phase 4B.",),
            fallback_reason="Local AI adapter unavailable; no local model call was attempted.",
        )
