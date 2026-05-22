"""AI adapter interface stubs for the AIFRED AI layer."""

from .base import AIAdapter, AIAdapterCapability, AIAdapterStatus, AIAdapterType, AIInterpretationResult
from .local_adapter import LocalAIAdapter
from .no_ai_adapter import NoAIAdapter
from .openai_adapter import OpenAIAdapter
from .router import AdapterRouter

__all__ = [
    "AIAdapter",
    "AIAdapterCapability",
    "AIAdapterStatus",
    "AIAdapterType",
    "AIInterpretationResult",
    "AdapterRouter",
    "LocalAIAdapter",
    "NoAIAdapter",
    "OpenAIAdapter",
]
