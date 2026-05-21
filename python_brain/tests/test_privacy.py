"""Tests for `aifred_brain.privacy`.

- private metadata scrubbing
- consent classification
- no raw local paths in user-facing state
- no collection of private audio metadata by default
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.privacy import (  # noqa: E402
    is_probably_private_path,
    redact_private_path,
    safe_display_path,
    scrub_private_metadata,
)


class PrivacyContractTests(unittest.TestCase):
    def test_detects_windows_local_path(self) -> None:
        self.assertTrue(is_probably_private_path(r"C:\Users\Someone\Song.wav"))

    def test_detects_posix_local_path(self) -> None:
        self.assertTrue(is_probably_private_path("/home/someone/song.wav"))

    def test_safe_display_path_returns_only_name(self) -> None:
        self.assertEqual(safe_display_path(r"C:\Users\Someone\Song.wav"), "Song.wav")

    def test_redact_private_path_preserves_filename(self) -> None:
        redacted = redact_private_path(r"Loaded C:\Users\Someone\Song.wav for metadata")
        self.assertIn("<private-path>/Song.wav", redacted)
        self.assertNotIn(r"C:\Users\Someone", redacted)

    def test_scrub_private_metadata_is_recursive(self) -> None:
        scrubbed = scrub_private_metadata({"nested": {"path": "/home/user/session.wav"}})
        self.assertEqual(scrubbed["nested"]["path"], "<private-path>/session.wav")
