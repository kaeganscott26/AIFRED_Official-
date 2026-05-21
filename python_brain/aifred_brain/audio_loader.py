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
from .validation import UnsupportedWavEncodingError, validate_audio_file_path


@dataclass(frozen=True)
class AudioMetadata:
    """Safe WAV metadata without full local path exposure or sample data."""

    path_display: str
    sample_rate: int
    channels: int
    sample_width_bytes: int
    frame_count: int
    duration_seconds: float


@dataclass(frozen=True)
class AudioBuffer:
    """Decoded PCM sample data for factual level metrics only."""

    metadata: AudioMetadata
    samples: tuple[float, ...]
    channels: int
    sample_rate: int
    frame_count: int


AudioInput = AudioBuffer | AudioMetadata


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


def _decode_8_bit_pcm(raw: bytes) -> tuple[float, ...]:
    return tuple((sample - 128) / 128.0 for sample in raw)


def _decode_signed_pcm(raw: bytes, sample_width: int) -> tuple[float, ...]:
    if sample_width not in {2, 3, 4}:
        raise UnsupportedWavEncodingError(f"Unsupported WAV sample width: {sample_width} bytes")

    samples: list[float] = []
    bits = sample_width * 8
    positive_scale = float((1 << (bits - 1)) - 1)
    negative_scale = float(1 << (bits - 1))

    for offset in range(0, len(raw), sample_width):
        chunk = raw[offset:offset + sample_width]
        if len(chunk) != sample_width:
            raise UnsupportedWavEncodingError("WAV data ended mid-sample.")
        value = int.from_bytes(chunk, byteorder="little", signed=True)
        scale = negative_scale if value < 0 else positive_scale
        samples.append(max(-1.0, min(1.0, value / scale)))
    return tuple(samples)


def load_wav_buffer(path: str | PathLike[str]) -> AudioBuffer:
    """Load normalized PCM samples from an approved WAV file.

    Samples are interleaved by channel and normalized to roughly -1.0..1.0.
    No metrics are calculated here.
    """
    audio_path = validate_audio_file_path(path)
    metadata = load_wav_metadata(audio_path)

    with wave.open(str(audio_path), "rb") as wav_file:
        if wav_file.getcomptype() != "NONE":
            raise UnsupportedWavEncodingError(f"Unsupported WAV compression: {wav_file.getcomptype()}")
        sample_width = wav_file.getsampwidth()
        raw = wav_file.readframes(wav_file.getnframes())

    if sample_width == 1:
        samples = _decode_8_bit_pcm(raw)
    elif sample_width in {2, 3, 4}:
        samples = _decode_signed_pcm(raw, sample_width)
    else:
        raise UnsupportedWavEncodingError(f"Unsupported WAV sample width: {sample_width} bytes")

    return AudioBuffer(
        metadata=metadata,
        samples=samples,
        channels=metadata.channels,
        sample_rate=metadata.sample_rate,
        frame_count=metadata.frame_count,
    )


def load_audio_file(path: str | PathLike[str], *, source_label: str) -> AudioInput:
    """Load an approved WAV file as decoded PCM buffer for level metrics."""
    _ = source_label
    return load_wav_buffer(path)


def validate_audio_input(audio: AudioInput) -> dict[str, Any]:
    """Validate loaded audio before metric calculation."""
    metadata = audio.metadata if isinstance(audio, AudioBuffer) else audio
    return {
        "valid": metadata.sample_rate > 0 and metadata.channels > 0 and metadata.frame_count >= 0,
        "sample_rate": metadata.sample_rate,
        "channels": metadata.channels,
        "duration_seconds": metadata.duration_seconds,
    }
