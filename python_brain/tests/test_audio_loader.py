"""Tests for `aifred_brain.audio_loader`.

- safe audio loading from approved fixtures
- sample rate, channel count, duration, and source labels
- private path scrubbing
- invalid/unavailable input handling
"""

import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.audio_loader import load_audio_file, load_wav_metadata, validate_audio_input  # noqa: E402


def _write_tiny_wav(path: Path, *, channels: int = 2, sample_rate: int = 8000, frames: int = 16) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * channels * frames)


class AudioLoaderContractTests(unittest.TestCase):
    def test_load_wav_metadata_from_synthetic_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.wav"
            _write_tiny_wav(path, channels=2, sample_rate=8000, frames=16)
            metadata = load_wav_metadata(path)

        self.assertEqual(metadata.path_display, "synthetic.wav")
        self.assertEqual(metadata.sample_rate, 8000)
        self.assertEqual(metadata.channels, 2)
        self.assertEqual(metadata.sample_width_bytes, 2)
        self.assertEqual(metadata.frame_count, 16)
        self.assertAlmostEqual(metadata.duration_seconds, 16 / 8000)

    def test_load_audio_file_returns_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mono.wave"
            _write_tiny_wav(path, channels=1, sample_rate=4000, frames=4)
            metadata = load_audio_file(path, source_label="File Analysis")
            validation = validate_audio_input(metadata)

        self.assertEqual(metadata.channels, 1)
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["sample_rate"], 4000)
