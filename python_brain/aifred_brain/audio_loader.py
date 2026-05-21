"""Safe WAV metadata loading for the Python Truth Layer.

Responsibility:
    Load approved WAV file metadata into a factual analysis-ready
    representation.

This module must not perform interpretation, produce advice, expose private
paths in user-facing state, return fake audio data, or compute DSP metrics.
"""

from __future__ import annotations

import wave
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any

from .privacy import safe_display_path
from .validation import validate_audio_file_path


@dataclass(frozen=True)
class AudioMetadata:
    """Safe WAV metadata without full local path exposure or sample data."""

    path_display: str
    sample_rate: int
    channels: int
    sample_width_bytes: int
    frame_count: int
    duration_seconds: float


AudioInput = AudioMetadata


def load_wav_metadata(path: str | PathLike[str]) -> AudioMetadata:
    """Load basic WAV metadata using the standard library only."""
    audio_path = validate_audio_file_path(path)
    with wave.open(str(audio_path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        frame_count = wav_file.getnframes()

    duration = frame_count / sample_rate if sample_rate else 0.0
    return AudioMetadata(
        path_display=safe_display_path(Path(audio_path)),
        sample_rate=sample_rate,
        channels=channels,
        sample_width_bytes=sample_width,
        frame_count=frame_count,
        duration_seconds=duration,
    )


def load_audio_file(path: str | PathLike[str], *, source_label: str) -> AudioInput:
    """Load an approved WAV file as metadata only for this phase."""
    _ = source_label
    return load_wav_metadata(path)


def validate_audio_input(audio: AudioInput) -> dict[str, Any]:
    """Validate loaded audio before metric calculation."""
    return {
        "valid": audio.sample_rate > 0 and audio.channels > 0 and audio.frame_count >= 0,
        "sample_rate": audio.sample_rate,
        "channels": audio.channels,
        "duration_seconds": audio.duration_seconds,
    }
