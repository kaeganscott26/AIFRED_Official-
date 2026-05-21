"""Tests for `aifred_brain.validation`.

- metric result validation
- mode boundary validation
- report context validation
- unavailable, stale, limited, and valid states
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.validation import (  # noqa: E402
    MissingAudioFileError,
    UnsupportedAudioFormatError,
    is_supported_audio_extension,
    validate_audio_file_path,
    validate_metric_result,
    validate_mode_boundaries,
)


class ValidationContractTests(unittest.TestCase):
    def test_supported_wav_extensions(self) -> None:
        self.assertTrue(is_supported_audio_extension("mix.wav"))
        self.assertTrue(is_supported_audio_extension("mix.WAVE"))

    def test_unsupported_extension_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mix.mp3"
            path.write_bytes(b"not audio")
            with self.assertRaises(UnsupportedAudioFormatError):
                validate_audio_file_path(path)

    def test_missing_audio_file_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(MissingAudioFileError):
                validate_audio_file_path(Path(tmp) / "missing.wav")

    def test_directory_rejected_when_file_expected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(Exception):
                validate_audio_file_path(Path(tmp))

    def test_available_metric_requires_value(self) -> None:
        with self.assertRaises(Exception):
            validate_metric_result({"state": "available"})

    def test_compare_mode_rejects_reference_context(self) -> None:
        with self.assertRaises(Exception):
            validate_mode_boundaries({"mode": "compare", "reference_context": {}})
