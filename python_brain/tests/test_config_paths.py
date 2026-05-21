"""Tests for `aifred_brain.config_paths`.

- portable report path resolution
- no hardcoded developer paths
- safe fallback behavior
- user-chosen path handling
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aifred_brain.config_paths import (  # noqa: E402
    get_aifred_home,
    get_fixtures_dir,
    get_reports_dir,
    resolve_reports_directory,
)


class ConfigPathsContractTests(unittest.TestCase):
    def test_aifred_home_uses_environment_override_without_creating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            override = Path(tmp) / "custom-home"
            with patch.dict(os.environ, {"AIFRED_HOME": str(override)}):
                self.assertEqual(get_aifred_home(), override)
                self.assertFalse(override.exists())

    def test_aifred_home_create_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            override = Path(tmp) / "custom-home"
            with patch.dict(os.environ, {"AIFRED_HOME": str(override)}):
                self.assertTrue(get_aifred_home(create=True).is_dir())

    def test_reports_dir_uses_aifred_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"AIFRED_HOME": tmp}):
                self.assertEqual(get_reports_dir(), Path(tmp) / "Reports")

    def test_project_reports_directory_is_portable(self) -> None:
        project = Path("relative-project")
        self.assertEqual(resolve_reports_directory(project_directory=project), str(project / "AIFRED Reports"))

    def test_fixtures_dir_is_relative_to_python_brain(self) -> None:
        fixtures = get_fixtures_dir()
        self.assertEqual(fixtures.name, "fixtures")
        self.assertEqual(fixtures.parent.name, "python_brain")
