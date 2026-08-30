"""Tests for ci_annotate.py: the GitHub Actions annotation glue used by the
srt-check workflow (docs/srt-canonicalization-spec.md Component 2)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CI_ANNOTATE_PATH = Path(__file__).resolve().parent / "ci_annotate.py"


class CiAnnotateTests(unittest.TestCase):
    def _run(self, *paths: Path) -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"\0".join(str(p).encode("utf-8") for p in paths))
            paths_file = f.name
        try:
            return subprocess.run(
                [sys.executable, str(CI_ANNOTATE_PATH), "--paths-file", paths_file],
                capture_output=True,
                text=True,
            )
        finally:
            Path(paths_file).unlink()

    def test_canonical_file_produces_no_annotations(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "clean.srt"
            path.write_bytes(b"1000\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_check_failure_emits_error_with_line_number(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.srt"
            path.write_bytes(b"1\n00:00:04,000 --> 00:00:01,000\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"::error file={path},line=", result.stdout)

    def test_check_failure_without_a_line_number_defaults_to_one(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bom.srt"
            path.write_bytes(b"\xef\xbb\xbf1000\n00:00:01,000 --> 00:00:04,000\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"::error file={path},line=1::", result.stdout)
            self.assertIn("BOM", result.stdout)

    def test_lint_warning_emits_warning_and_does_not_fail(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "short.srt"
            path.write_bytes(b"1000\n00:00:01,000 --> 00:00:01,100\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertIn(f"::warning file={path},line=", result.stdout)
            self.assertIn("100ms", result.stdout)

    def test_hard_parse_failure_emits_error_and_skips_lint(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "broken.srt"
            path.write_bytes(b"1\nnot a timestamp\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"::error file={path},line=1::", result.stdout)
            self.assertNotIn("::warning", result.stdout)

    def test_filenames_with_spaces_and_unicode_survive_nul_splitting(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "早晨 大家 (1989).srt"
            path.write_bytes(b"1000\n00:00:01,000 --> 00:00:01,100\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertIn(str(path), result.stdout)

    def test_percent_and_newline_in_message_are_escaped(self):
        # GitHub's workflow-command syntax is line-based, so a message
        # containing '%' or a raw newline must be escaped or it would
        # corrupt/truncate the annotation.
        import io
        from contextlib import redirect_stdout

        import ci_annotate

        buf = io.StringIO()
        with redirect_stdout(buf):
            ci_annotate._emit("error", "f.srt", "100% wrong\nline2", line=3)
        self.assertEqual(buf.getvalue(), "::error file=f.srt,line=3::100%25 wrong%0Aline2\n")


if __name__ == "__main__":
    unittest.main()
