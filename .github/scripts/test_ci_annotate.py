"""Tests for ci_annotate.py: the GitHub Actions annotation glue used by the
srt-check workflow."""

from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import ci_annotate

CI_ANNOTATE_PATH = Path(__file__).resolve().parent / "ci_annotate.py"


def _file_prop(path: Path) -> str:
    return f"file={ci_annotate._escape_property(str(path))}"


class CiAnnotateTests(unittest.TestCase):
    def _run(self, *paths: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"\0".join(str(p).encode("utf-8") for p in paths))
            paths_file = f.name
        try:
            return subprocess.run(
                [sys.executable, str(CI_ANNOTATE_PATH), "--paths-file", paths_file],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})},
            )
        finally:
            Path(paths_file).unlink()

    def test_clean_file_produces_no_annotations(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "clean.srt"
            path.write_bytes(b"1\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_cosmetic_issues_produce_no_annotations(self):
        # BOM, CRLF, trailing whitespace, odd cue numbers: none of it matters
        # to a player, so none of it should make noise.
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "messy.srt"
            path.write_bytes(
                b"\xef\xbb\xbf7\r\n00:00:01,000 --> 00:00:04,000\r\n\xe5\x96\x82  \r\n\r\n\r\n"
                b"7\r\n00:00:05,000 --> 00:00:06,000\r\n\xe5\x96\x82\r\n"
            )
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_broken_file_emits_error_on_the_offending_line(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.srt"
            path.write_bytes(b"1\n00:00:04,000 --> 00:00:01,000\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"::error {_file_prop(path)},line=2,", result.stdout)

    def test_encoding_error_without_a_line_number_defaults_to_one(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "utf16.srt"
            body = "1\n00:00:01,000 --> 00:00:04,000\n喂\n"
            path.write_bytes(b"\xff\xfe" + body.encode("utf-16-le"))
            result = self._run(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"::error {_file_prop(path)},line=1,", result.stdout)
            self.assertIn("UTF-16", result.stdout)

    def test_non_utf8_file_is_an_error_not_a_crash(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "big5.srt"
            path.write_bytes(b"1\n00:00:01,000 --> 00:00:04,000\n\xb3\xde\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("::error", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def test_lint_warning_emits_warning_and_does_not_fail(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "short.srt"
            path.write_bytes(b"1\n00:00:01,000 --> 00:00:01,100\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertIn(f"::warning {_file_prop(path)},line=2,title=Subtitle too short::", result.stdout)
            self.assertIn("100ms", result.stdout)

    def test_out_of_order_cues_warn_but_do_not_fail(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "overlap.srt"
            path.write_bytes(
                "1\n00:00:05,000 --> 00:00:06,000\n哦\n\n2\n00:00:01,000 --> 00:00:04,000\n喂\n".encode()
            )
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertIn("title=Out of order::", result.stdout)

    def test_repeated_warnings_are_grouped_into_one_annotation(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "long.srt"
            blocks = [
                f"{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},900\n{'早' * 18}" for i in range(1, 11)
            ]
            path.write_bytes(("\n\n".join(blocks) + "\n").encode("utf-8"))
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.count("title=Line too long"), 1, result.stdout)
            self.assertIn("9 more like this in this file: cues 2, 3, 4, 5, 6, …", result.stdout)

    def test_hard_parse_failure_emits_error_and_skips_lint(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "broken.srt"
            path.write_bytes(b"1\nnot a timestamp\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"::error {_file_prop(path)},line=2,", result.stdout)
            self.assertNotIn("::warning", result.stdout)

    def test_filenames_with_spaces_and_unicode_survive_nul_splitting(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "早晨 大家 (1989).srt"
            path.write_bytes(b"1\n00:00:01,000 --> 00:00:01,100\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertIn(str(path), result.stdout)

    def test_job_summary_lists_files_with_problems(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.srt"
            bad.write_bytes(b"1\n00:00:04,000 --> 00:00:01,000\n\xe5\x96\x82\n")
            short = Path(d) / "short.srt"
            short.write_bytes(b"1\n00:00:01,000 --> 00:00:01,100\n\xe5\x96\x82\n")
            summary = Path(d) / "summary.md"
            self._run(bad, short, env={"GITHUB_STEP_SUMMARY": str(summary)})
            text = summary.read_text(encoding="utf-8")
            self.assertIn(str(bad).replace("|", "\\|"), text)
            self.assertIn("is before start time", text)
            self.assertIn("Subtitle too short ×1", text)

    def test_checker_bug_warns_instead_of_failing(self):
        buf = io.StringIO()
        original = ci_annotate._check_one
        ci_annotate._check_one = lambda path: 1 / 0
        try:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"x.srt")
            with redirect_stdout(buf), redirect_stderr(io.StringIO()):
                code = ci_annotate.main(["--paths-file", f.name])
        finally:
            ci_annotate._check_one = original
            Path(f.name).unlink()
        self.assertEqual(code, 0)
        self.assertIn("::warning file=x.srt,line=1,title=Check skipped::", buf.getvalue())

    def test_percent_and_newline_in_message_are_escaped(self):
        # GitHub's workflow-command syntax is line-based, so a message
        # containing '%' or a raw newline must be escaped or it would
        # corrupt/truncate the annotation.
        buf = io.StringIO()
        with redirect_stdout(buf):
            ci_annotate._emit("error", "f.srt", "100% wrong\nline2", line=3)
        self.assertEqual(buf.getvalue(), "::error file=f.srt,line=3::100%25 wrong%0Aline2\n")

    def test_commas_and_colons_in_filenames_are_escaped(self):
        # Properties are comma-separated, so an unescaped ',' in a filename
        # would cut the path short and the annotation would land nowhere.
        buf = io.StringIO()
        with redirect_stdout(buf):
            ci_annotate._emit("warning", "Subtitles/Hello, World: 2.srt", "msg", title="A, B")
        self.assertEqual(
            buf.getvalue(),
            "::warning file=Subtitles/Hello%2C World%3A 2.srt,line=1,title=A%2C B::msg\n",
        )


if __name__ == "__main__":
    unittest.main()
