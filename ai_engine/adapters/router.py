"""Adapter router stub for Phase 4B.

The router selects among stub adapters using configuration and capability. It
does not call providers, read secrets, contact endpoints, or load models.
"""

from __future__ import annotations

from pathlib import PurePath, PureWindowsPath
import re
from typing import Any

from ai_engine.config.adapter_config import AIAdapterConfig, PreferredAdapter

from .base import AIAdapter, AIAdapterStatus, AIAdapterType, AIInterpretationResult, packet_value
from .local_adapter import LocalAIAdapter
from .no_ai_adapter import NoAIAdapter
from .openai_adapter import OpenAIAdapter

_PRIVATE_PATH_PATTERN = re.compile(
    r"(?P<path>(?:[A-Za-z]:\\|/)[^\s\"'<>|]+)"
)


class AdapterRouter:
    """Select a configured adapter without provider calls."""

    def __init__(
        self,
        config: AIAdapterConfig | None = None,
        *,
        openai_adapter: AIAdapter | None = None,
        local_adapter: AIAdapter | None = None,
        no_ai_adapter: AIAdapter | None = None,
    ) -> None:
        self.config = config or AIAdapterConfig()
        self.openai_adapter = openai_adapter or OpenAIAdapter()
        self.local_adapter = local_adapter or LocalAIAdapter(self.config.local_settings)
        self.no_ai_adapter = no_ai_adapter or NoAIAdapter(self.config.no_ai_fallback_enabled)

    def select_adapter(self) -> AIAdapter | None:
        """Return the first configured available adapter."""
        preferred = self.config.preferred_adapter
        if preferred == PreferredAdapter.OPENAI:
            return self._available_or_fallback(self.openai_adapter)
        if preferred == PreferredAdapter.LOCAL:
            return self._available_or_fallback(self.local_adapter)
        if preferred == PreferredAdapter.NO_AI:
            return self.no_ai_adapter if self.config.no_ai_fallback_enabled else None
        return self._select_auto()

    def interpret(self, packet: Any) -> AIInterpretationResult:
        """Route interpretation to the selected adapter or return unavailable."""
        adapter = self.select_adapter()
        if adapter is None:
            return AIInterpretationResult(
                adapter_name="AdapterRouter",
                adapter_type=AIAdapterType.NO_AI,
                status=AIAdapterStatus.UNAVAILABLE,
                source_label=_safe_optional_text(packet_value(packet, "source_label")),
                mode=_safe_optional_text(packet_value(packet, "mode")),
                limitations=("No AI adapter is available.",),
                fallback_reason="No configured adapter capability is available.",
            )
        return adapter.interpret(packet)

    def _select_auto(self) -> AIAdapter | None:
        if self.config.openai_enabled and self.openai_adapter.get_capability().available:
            return self.openai_adapter
        if self.config.local_enabled and self.local_adapter.get_capability().available:
            return self.local_adapter
        if self.config.no_ai_fallback_enabled:
            return self.no_ai_adapter
        return None

    def _available_or_fallback(self, adapter: AIAdapter) -> AIAdapter | None:
        if adapter.get_capability().available:
            return adapter
        if self.config.no_ai_fallback_enabled:
            return self.no_ai_adapter
        return adapter


def _safe_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(getattr(value, "value", value))
    text = text.replace("-999", "[unavailable]")
    return _PRIVATE_PATH_PATTERN.sub(_redact_path_match, text)


def _redact_path_match(match: re.Match[str]) -> str:
    raw_path = match.group("path").rstrip(".,;:)")
    trailing = match.group("path")[len(raw_path):]
    try:
        filename = PureWindowsPath(raw_path).name or PurePath(raw_path).name
    except ValueError:
        filename = "redacted"
    return f"[redacted path]/{filename}{trailing}"
