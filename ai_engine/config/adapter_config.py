"""AI adapter configuration dataclasses.

This module stores config references only. It does not read environment
variables, inspect endpoints, call providers, or load local models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PreferredAdapter(str, Enum):
    """Preferred adapter selection mode."""

    AUTO = "auto"
    OPENAI = "openai"
    LOCAL = "local"
    NO_AI = "no_ai"


@dataclass(frozen=True)
class AIAdapterConfig:
    """Configuration references for future adapter selection."""

    preferred_adapter: PreferredAdapter = PreferredAdapter.AUTO
    openai_enabled: bool = False
    local_enabled: bool = False
    no_ai_fallback_enabled: bool = True
    timeout_seconds: float = 10.0
    openai_model: str | None = None
    local_model: str | None = None
    local_endpoint: str | None = None
    api_key_env_var: str = "OPENAI_API_KEY"
