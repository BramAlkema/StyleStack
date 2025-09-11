#!/usr/bin/env python3
"""Tests that missing modules trigger logger warnings in build.py."""

import importlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestMissingModuleWarnings(unittest.TestCase):
    """Verify warnings are logged when optional modules are unavailable."""

    def test_missing_modules_emit_warnings(self):
        """Ensure missing optional modules emit warnings via logger."""
        real_import = __import__

        def mocked_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith("tools"):
                raise ImportError("Mocked missing module")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=mocked_import):
            if "build" in sys.modules:
                del sys.modules["build"]
            with self.assertLogs("build", level="WARNING") as cm:
                importlib.import_module("build")

        joined = "\n".join(cm.output)
        self.assertIn("Could not import OOXML Extension Variable System components", joined)
        self.assertIn("Could not import JSON-to-OOXML Processing Engine", joined)

        if "build" in sys.modules:
            del sys.modules["build"]


if __name__ == "__main__":
    unittest.main()
