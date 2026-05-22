"""Safe local AI adapter configuration boundary helpers.

This module stores and validates configuration references only. It does not
call Ollama, call LM Studio, send HTTP requests, load local models, or generate
AI interpretation responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from ipaddress import ip_address
from urllib.parse import SplitResult, urlsplit, urlunsplit


class LocalProviderType(str, Enum):
    """Supported local adapter provider reference types."""

    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    CUSTOM = "custom"


class LocalConfigStatus(str, Enum):
    """Local adapter configuration readiness states."""

    READY = "ready"
    DISABLED = "disabled"
    MISSING_MODEL = "missing_model"
    MISSING_ENDPOINT = "missing_endpoint"
    INVALID_CONFIG = "invalid_config"


@dataclass(frozen=True)
class LocalAdapterSettings:
    """Configuration references for a future local AI adapter."""

    enabled: bool = False
    provider: LocalProviderType = LocalProviderType.OLLAMA
    model: str = ""
    endpoint: str = "http://127.0.0.1:11434"
    timeout_seconds: float = 10.0
    supports_streaming: bool = False


@dataclass(frozen=True)
class LocalConfigCheck:
    """Privacy-safe local adapter config check result."""

    status: LocalConfigStatus
    enabled: bool
    provider: LocalProviderType
    model: str
    endpoint: str
    timeout_seconds: float
    issues: tuple[str, ...] = ()


def create_default_ollama_settings() -> LocalAdapterSettings:
    """Return default Ollama settings without contacting the endpoint."""
    return LocalAdapterSettings(
        provider=LocalProviderType.OLLAMA,
        endpoint="http://127.0.0.1:11434",
    )


def create_default_lm_studio_settings() -> LocalAdapterSettings:
    """Return default LM Studio settings without contacting the endpoint."""
    return LocalAdapterSettings(
        provider=LocalProviderType.LM_STUDIO,
        endpoint="http://127.0.0.1:1234/v1",
    )


def validate_local_settings(settings: LocalAdapterSettings) -> tuple[str, ...]:
    """Validate local settings shape without calling a provider."""
    issues: list[str] = []
    if settings.timeout_seconds <= 0:
        issues.append("timeout_seconds must be positive.")
    if not isinstance(settings.provider, LocalProviderType):
        issues.append("provider must be a LocalProviderType value.")

    endpoint = str(settings.endpoint).strip()
    if endpoint:
        endpoint_issue = _validate_endpoint_reference(endpoint, settings.provider)
        if endpoint_issue:
            issues.append(endpoint_issue)

    return tuple(issues)


def check_local_config(settings: LocalAdapterSettings) -> LocalConfigCheck:
    """Return a safe local adapter readiness check without provider calls."""
    issues = validate_local_settings(settings)
    model_present = bool(str(settings.model).strip())
    endpoint_present = bool(str(settings.endpoint).strip())

    if issues:
        status = LocalConfigStatus.INVALID_CONFIG
    elif not settings.enabled:
        status = LocalConfigStatus.DISABLED
    elif not model_present:
        status = LocalConfigStatus.MISSING_MODEL
    elif not endpoint_present:
        status = LocalConfigStatus.MISSING_ENDPOINT
    else:
        status = LocalConfigStatus.READY

    return LocalConfigCheck(
        status=status,
        enabled=settings.enabled,
        provider=settings.provider,
        model=settings.model,
        endpoint=_safe_endpoint_summary(settings.endpoint),
        timeout_seconds=settings.timeout_seconds,
        issues=issues,
    )


def safe_local_config_summary(check: LocalConfigCheck) -> dict[str, object]:
    """Return a serializable local config summary without credentials."""
    return {
        "status": check.status.value,
        "enabled": check.enabled,
        "provider": check.provider.value,
        "model": check.model,
        "endpoint": _safe_endpoint_summary(check.endpoint),
        "timeout_seconds": check.timeout_seconds,
        "issues": list(check.issues),
    }


def _validate_endpoint_reference(endpoint: str, provider: LocalProviderType) -> str | None:
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        return "endpoint must be an HTTP(S) URL reference."
    if parsed.username is not None or parsed.password is not None:
        return "endpoint must not contain embedded credentials."
    if provider != LocalProviderType.CUSTOM and not _is_local_host(parsed.hostname):
        return "endpoint must be local unless provider is CUSTOM."
    return None


def _is_local_host(hostname: str) -> bool:
    normalized = hostname.strip().lower().strip("[]")
    if normalized == "localhost":
        return True
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def _safe_endpoint_summary(endpoint: str) -> str:
    text = str(endpoint).strip()
    if not text:
        return ""
    parsed = urlsplit(text)
    if not parsed.netloc:
        return text
    host = parsed.hostname or ""
    netloc = host
    if ":" in host and not host.startswith("["):
        netloc = f"[{host}]"
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    return urlunsplit(
        SplitResult(
            scheme=parsed.scheme,
            netloc=netloc,
            path=parsed.path,
            query=parsed.query,
            fragment=parsed.fragment,
        )
    )
