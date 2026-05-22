"""Safe OpenAI configuration boundary helpers.

This module stores and validates configuration references only. It does not
import the OpenAI SDK, read provider responses, call networks, or expose API key
values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
from typing import Mapping


class OpenAIConfigStatus(str, Enum):
    """OpenAI configuration readiness states."""

    READY = "ready"
    MISSING_API_KEY = "missing_api_key"
    DISABLED = "disabled"
    INVALID_CONFIG = "invalid_config"


@dataclass(frozen=True)
class OpenAIAdapterSettings:
    """Configuration references for the future OpenAI adapter."""

    enabled: bool = False
    model: str = "gpt-4.1-mini"
    api_key_env_var: str = "OPENAI_API_KEY"
    timeout_seconds: float = 10.0
    max_output_tokens: int | None = None


@dataclass(frozen=True)
class OpenAIConfigCheck:
    """Privacy-safe OpenAI config check result."""

    status: OpenAIConfigStatus
    enabled: bool
    api_key_env_var: str
    api_key_present: bool
    model: str
    timeout_seconds: float
    issues: tuple[str, ...] = ()


def create_default_openai_settings() -> OpenAIAdapterSettings:
    """Return default OpenAI settings without reading secrets."""
    return OpenAIAdapterSettings()


def validate_openai_settings(settings: OpenAIAdapterSettings) -> tuple[str, ...]:
    """Validate settings shape without reading provider credentials."""
    issues: list[str] = []
    if not str(settings.api_key_env_var).strip():
        issues.append("api_key_env_var must be non-empty.")
    if settings.timeout_seconds <= 0:
        issues.append("timeout_seconds must be positive.")
    if settings.enabled and not str(settings.model).strip():
        issues.append("model must be non-empty when OpenAI is enabled.")
    if settings.max_output_tokens is not None and settings.max_output_tokens <= 0:
        issues.append("max_output_tokens must be positive when provided.")
    return tuple(issues)


def check_openai_config(
    settings: OpenAIAdapterSettings,
    environ: Mapping[str, str] | None = None,
) -> OpenAIConfigCheck:
    """Return a safe OpenAI readiness check without exposing secret values."""
    issues = validate_openai_settings(settings)
    env = os.environ if environ is None else environ
    key_value = env.get(settings.api_key_env_var)
    key_present = mask_secret_presence(key_value)

    if issues:
        status = OpenAIConfigStatus.INVALID_CONFIG
    elif not settings.enabled:
        status = OpenAIConfigStatus.DISABLED
    elif not key_present:
        status = OpenAIConfigStatus.MISSING_API_KEY
    else:
        status = OpenAIConfigStatus.READY

    return OpenAIConfigCheck(
        status=status,
        enabled=settings.enabled,
        api_key_env_var=settings.api_key_env_var,
        api_key_present=key_present,
        model=settings.model,
        timeout_seconds=settings.timeout_seconds,
        issues=issues,
    )


def mask_secret_presence(value: str | None) -> bool:
    """Return only whether a secret-like value is present."""
    return bool(value and value.strip())


def safe_openai_config_summary(check: OpenAIConfigCheck) -> dict[str, object]:
    """Return a serializable config summary without secret values."""
    return {
        "status": check.status.value,
        "enabled": check.enabled,
        "api_key_env_var": check.api_key_env_var,
        "api_key_present": bool(check.api_key_present),
        "model": check.model,
        "timeout_seconds": check.timeout_seconds,
        "issues": list(check.issues),
    }

