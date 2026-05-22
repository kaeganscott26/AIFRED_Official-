"""OpenAI adapter stub.

No OpenAI calls, dependencies, API-key access, or response generation are
implemented in Phase 4B.
"""

from __future__ import annotations

from typing import Any

from .base import AIAdapterCapability, AIAdapterStatus, AIAdapterType, AIInterpretationResult, packet_value


class OpenAIAdapter:
    """Unavailable OpenAI adapter placeholder."""

    adapter_name = "OpenAIAdapter"
    adapter_type = AIAdapterType.OPENAI

    def get_capability(self) -> AIAdapterCapability:
        """Return unavailable capability without checking API keys."""
        return AIAdapterCapability(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            available=False,
            reason="OpenAI adapter is not implemented in Phase 4B.",
            requires_api_key=True,
        )

    def interpret(self, packet: Any) -> AIInterpretationResult:
        """Return structured unavailable state without calling OpenAI."""
        return AIInterpretationResult(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            status=AIAdapterStatus.UNAVAILABLE,
            source_label=packet_value(packet, "source_label"),
            mode=packet_value(packet, "mode"),
            limitations=("OpenAI interpretation is not implemented in Phase 4B.",),
            fallback_reason="OpenAI adapter unavailable; no provider call was attempted.",
        )
