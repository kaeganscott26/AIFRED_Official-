"""OpenAI adapter stub.

This adapter understands safe OpenAI configuration state, but it does not call
OpenAI, import provider SDKs, read API key values, or generate interpretation
prose.
"""

from __future__ import annotations

from pathlib import PurePath, PureWindowsPath
import re
from typing import Any

from ai_engine.config.openai_config import (
    OpenAIAdapterSettings,
    OpenAIConfigCheck,
    OpenAIConfigStatus,
    check_openai_config,
    create_default_openai_settings,
)

from .base import (
    AIAdapterCapability,
    AIAdapterStatus,
    AIAdapterType,
    AIInterpretationResult,
    packet_metric_families,
    packet_sequence,
    packet_value,
)

_CONFIGURED_STUB_TEXT = "OpenAI adapter is configured structurally, but provider calls are not implemented in this phase."
_INCOMPLETE_CONFIG_TEXT = "OpenAI adapter is unavailable because configuration is incomplete."
_DISABLED_CONFIG_TEXT = "OpenAI adapter is unavailable because OpenAI is disabled."
_PRIVATE_PATH_PATTERN = re.compile(
    r"(?P<path>(?:[A-Za-z]:\\|/)[^\s\"'<>|]+)"
)


class OpenAIAdapter:
    """Safe OpenAI adapter placeholder."""

    adapter_name = "OpenAIAdapter"
    adapter_type = AIAdapterType.OPENAI

    def __init__(
        self,
        settings: OpenAIAdapterSettings | None = None,
        *,
        config_check: OpenAIConfigCheck | None = None,
    ) -> None:
        self.settings = settings or create_default_openai_settings()
        self._config_check = config_check

    def get_capability(self) -> AIAdapterCapability:
        """Return unavailable capability without provider calls or secret reads."""
        check = self._safe_config_check()
        return AIAdapterCapability(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            available=False,
            reason=self._capability_reason(check),
            requires_api_key=True,
        )

    def interpret(self, packet: Any) -> AIInterpretationResult:
        """Return structured stub state without calling OpenAI."""
        check = self._safe_config_check()
        configured = check.status == OpenAIConfigStatus.READY
        status_text = _CONFIGURED_STUB_TEXT if configured else _INCOMPLETE_CONFIG_TEXT
        return AIInterpretationResult(
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            status=AIAdapterStatus.LIMITED if configured else AIAdapterStatus.UNAVAILABLE,
            response_text=status_text,
            used_metric_families=_safe_metric_families(packet),
            source_label=_safe_optional_text(packet_value(packet, "source_label")),
            mode=_safe_optional_text(packet_value(packet, "mode")),
            limitations=(*_safe_sequence(packet, "limitations"), status_text),
            warnings=_safe_sequence(packet, "warnings"),
            fallback_reason=status_text,
            raw_response_available=False,
        )

    def _safe_config_check(self) -> OpenAIConfigCheck:
        if self._config_check is not None:
            return self._config_check
        return check_openai_config(self.settings, environ={})

    def _capability_reason(self, check: OpenAIConfigCheck) -> str:
        if check.status == OpenAIConfigStatus.READY:
            return _CONFIGURED_STUB_TEXT
        if check.status == OpenAIConfigStatus.DISABLED:
            return _DISABLED_CONFIG_TEXT
        return _INCOMPLETE_CONFIG_TEXT


def _safe_metric_families(packet: Any) -> tuple[str, ...]:
    return tuple(_safe_text(family) for family in packet_metric_families(packet))


def _safe_sequence(packet: Any, key: str) -> tuple[str, ...]:
    return tuple(_safe_text(item) for item in packet_sequence(packet, key))


def _safe_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return _safe_text(value)


def _safe_text(value: Any) -> str:
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
