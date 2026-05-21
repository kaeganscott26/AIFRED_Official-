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
from struct import pack

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.audio_loader import load_audio_file, load_wav_buffer, load_wav_metadata, validate_audio_input  # noqa: E402


def _write_tiny_wav(
    path: Path,
    *,
    channels: int = 2,
    sample_rate: int = 8000,
    frames: int = 16,
    sample_width: int = 2,
    values: tuple[int, ...] | None = None,
) -> None:
    if values is None:
        values = (0,) * channels * frames
    if sample_width == 1:
        raw = bytes(values)
    elif sample_width == 2:
        raw = b"".join(pack("<h", value) for value in values)
    elif sample_width == 3:
        raw = b"".join(int(value).to_bytes(3, byteorder="little", signed=True) for value in values)
    elif sample_width == 4:
        raw = b"".join(pack("<i", value) for value in values)
    else:
        raise ValueError("Test helper supports 1, 2, 3, or 4 byte samples.")

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(raw)


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

    def test_load_audio_file_returns_buffer_and_validates_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mono.wave"
            _write_tiny_wav(path, channels=1, sample_rate=4000, frames=4)
            audio = load_audio_file(path, source_label="File Analysis")
            validation = validate_audio_input(audio)

        self.assertEqual(audio.channels, 1)
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["sample_rate"], 4000)

    def test_loads_16_bit_synthetic_wav_into_normalized_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "samples.wav"
            _write_tiny_wav(
                path,
                channels=1,
                sample_rate=8000,
                frames=3,
                values=(-32768, 0, 32767),
            )
            buffer = load_wav_buffer(path)

        self.assertEqual(buffer.metadata.path_display, "samples.wav")
        self.assertEqual(buffer.samples[0], -1.0)
        self.assertEqual(buffer.samples[1], 0.0)
        self.assertEqual(buffer.samples[2], 1.0)
        self.assertEqual(buffer.sample_rate, 8000)
        self.assertEqual(buffer.channels, 1)
        self.assertEqual(buffer.frame_count, 3)

    def test_preserves_stereo_metadata_and_interleaved_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stereo.wav"
            _write_tiny_wav(
                path,
                channels=2,
                sample_rate=44100,
                frames=2,
                values=(32767, -32768, 0, 32767),
            )
            buffer = load_wav_buffer(path)

        self.assertEqual(buffer.channels, 2)
        self.assertEqual(buffer.frame_count, 2)
        self.assertEqual(len(buffer.samples), 4)
        self.assertEqual(buffer.samples[0], 1.0)
        self.assertEqual(buffer.samples[1], -1.0)

    def test_metadata_display_does_not_expose_parent_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "private_parent" / "safe_name.wav"
            path.parent.mkdir()
            _write_tiny_wav(path)
            buffer = load_wav_buffer(path)

        self.assertEqual(buffer.metadata.path_display, "safe_name.wav")
        self.assertNotIn("private_parent", buffer.metadata.path_display)
