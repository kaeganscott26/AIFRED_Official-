"""Shared AI adapter interfaces and structured result objects.

These interfaces define adapter shape only. They do not call providers, load
models, generate interpretation prose, or create metric-threshold responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class AIAdapterType(str, Enum):
    """Future AI adapter types."""

    OPENAI = "openai"
    LOCAL = "local"
    NO_AI = "no_ai"


class AIAdapterStatus(str, Enum):
    """Structured adapter result status values."""

    READY = "ready"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    ERROR = "error"
    NO_AI_CONFIGURED = "no_ai_configured"


@dataclass(frozen=True)
class AIInterpretationResult:
    """Structured AI-layer result or fallback state."""

    adapter_name: str
    adapter_type: AIAdapterType
    status: AIAdapterStatus
    response_text: str = ""
    used_metric_families: tuple[str, ...] = field(default_factory=tuple)
    source_label: str | None = None
    mode: str | None = None
    limitations: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    fallback_reason: str | None = None
    latency_ms: float | None = None
    raw_response_available: bool = False


@dataclass(frozen=True)
class AIAdapterCapability:
    """Static capability/fallback state for an adapter."""

    adapter_name: str
    adapter_type: AIAdapterType
    available: bool
    reason: str
    supports_streaming: bool = False
    supports_local: bool = False
    requires_api_key: bool = False


class AIAdapter(Protocol):
    """Protocol implemented by future adapter stubs and real adapters."""

    def get_capability(self) -> AIAdapterCapability:
        """Return factual adapter capability without calling providers."""
        ...

    def interpret(self, packet: Any) -> AIInterpretationResult:
        """Return a structured result or fallback state."""
        ...


def packet_value(packet: Any, key: str, default: Any = None) -> Any:
    """Read a value from a packet-like object without interpreting it."""
    if isinstance(packet, dict):
        return packet.get(key, default)
    return getattr(packet, key, default)


def packet_metric_families(packet: Any) -> tuple[str, ...]:
    """Return metric-family names from a packet-like object."""
    families = packet_value(packet, "metric_families", ())
    return tuple(str(getattr(family, "value", family)) for family in families)


def packet_sequence(packet: Any, key: str) -> tuple[str, ...]:
    """Return a packet sequence field as strings."""
    value = packet_value(packet, key, ())
    if value is None:
        return ()
    return tuple(str(item) for item in value)
