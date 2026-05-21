"""Audio loading interface for the Python Truth Layer.

Responsibility:
    Load approved audio inputs into a factual analysis-ready representation.

This module must not perform interpretation, produce advice, expose private
paths in user-facing state, or return fake audio data.
"""

from __future__ import annotations

from os import PathLike
from typing import Any


class AudioInput:
    """Contract placeholder for loaded audio input metadata and sample access."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("AudioInput data model is not implemented yet.")


def load_audio_file(path: str | PathLike[str], *, source_label: str) -> AudioInput:
    """Load an approved audio file for factual analysis."""
    raise NotImplementedError("Audio loading is not implemented yet.")


def validate_audio_input(audio: AudioInput) -> dict[str, Any]:
    """Validate loaded audio before metric calculation."""
    raise NotImplementedError("Audio validation is not implemented yet.")

