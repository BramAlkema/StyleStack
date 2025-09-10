#!/usr/bin/env python3
"""Tests for the safe_zip_dir helper in build.py."""

import hashlib
import tempfile
from pathlib import Path
import unittest

import build


class TestSafeZipDirDeterminism(unittest.TestCase):
    """Verify that safe_zip_dir produces deterministic archives."""

    def test_repeated_runs_have_same_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            src_dir = tmp_path / "src"
            src_dir.mkdir()
            (src_dir / "file.txt").write_text("content")

            out1 = tmp_path / "out1.zip"
            out2 = tmp_path / "out2.zip"

            context1 = build.BuildContext(src_dir, out1, tmp_path)
            build.safe_zip_dir(src_dir, out1, context1)
            hash1 = hashlib.sha256(out1.read_bytes()).hexdigest()

            context2 = build.BuildContext(src_dir, out2, tmp_path)
            build.safe_zip_dir(src_dir, out2, context2)
            hash2 = hashlib.sha256(out2.read_bytes()).hexdigest()

            self.assertEqual(hash1, hash2)


if __name__ == "__main__":
    unittest.main()
