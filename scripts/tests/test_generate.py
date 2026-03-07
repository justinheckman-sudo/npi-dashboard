#!/usr/bin/env python3
"""
test_generate.py — Unit tests for scripts/generate.py
Run: python -m unittest discover scripts/tests
"""
import unittest
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


class TestGeneratorAbort(unittest.TestCase):
    """GEN-01: Generator must abort on invalid YAML, writing nothing."""

    def test_abort_on_forbidden_key(self):
        """Generator exits non-zero and does NOT write index.html when YAML has forbidden key (e.g., 'rag')."""
        # Create a temp dir with a poisoned programs.yaml
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Copy repo structure to temp location
            shutil.copytree(REPO_ROOT / "data", tmpdir / "data")
            shutil.copy(REPO_ROOT / "validate_programs.py", tmpdir / "validate_programs.py")
            if (REPO_ROOT / "templates").exists():
                shutil.copytree(REPO_ROOT / "templates", tmpdir / "templates")
            # Poison the YAML: inject forbidden 'rag' key into first program
            yaml_path = tmpdir / "data" / "programs.yaml"
            content = yaml_path.read_text()
            poisoned = content.replace("  id:", "  rag: red\n  id:", 1)
            yaml_path.write_text(poisoned)
            # Run generator from temp dir
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "generate.py")],
                capture_output=True, text=True, cwd=tmpdir
            )
            self.assertNotEqual(result.returncode, 0, "Generator should exit non-zero on invalid YAML")
            self.assertFalse((tmpdir / "index.html").exists(), "Generator must NOT write index.html on invalid YAML")


class TestProgramsCount(unittest.TestCase):
    """GEN-01: Generator output must contain exactly 6 programs matching YAML source."""

    def test_programs_count_in_output(self):
        """Generated index.html contains 'const PROGRAMS' with 6 programs."""
        result = subprocess.run(
            [sys.executable, "scripts/generate.py"],
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        self.assertEqual(result.returncode, 0, f"Generator failed: {result.stdout}\n{result.stderr}")
        index_html = (REPO_ROOT / "index.html").read_text()
        self.assertIn("const PROGRAMS", index_html, "index.html must contain 'const PROGRAMS'")
        # Count program id entries — each program object has a top-level "id" key
        import re
        ids = re.findall(r'"id":\s*"[^"]+"', index_html)
        self.assertEqual(len(ids), 6, f"Expected 6 program entries, found {len(ids)}")

    def test_w3_fields_mapped(self):
        """W3 program in output has lastGate, nextGate.criteria as list (not string)."""
        result = subprocess.run(
            [sys.executable, "scripts/generate.py"],
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        self.assertEqual(result.returncode, 0)
        index_html = (REPO_ROOT / "index.html").read_text()
        self.assertIn('"lastGate"', index_html)
        self.assertIn('"nextGate"', index_html)
        self.assertIn('"criteria"', index_html)
        # criteria must be an array — look for the list opening after "criteria":
        import re
        criteria_match = re.search(r'"criteria":\s*\[', index_html)
        self.assertIsNotNone(criteria_match, "criteria must be a JSON array, not a string")


if __name__ == "__main__":
    unittest.main()
