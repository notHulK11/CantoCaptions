"""Tests for find_changed_srts.py: the git-diff glue used by the srt-check
workflow (docs/srt-canonicalization-spec.md Component 2)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FIND_CHANGED_PATH = Path(__file__).resolve().parent / "find_changed_srts.py"


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


class FindChangedSrtsTests(unittest.TestCase):
    def _make_repo(self, tmp: Path) -> Path:
        _git("init", "-q", cwd=tmp)
        _git("config", "user.email", "test@example.com", cwd=tmp)
        _git("config", "user.name", "Test", cwd=tmp)
        return tmp

    def test_only_srt_files_under_subtitles_are_reported(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(Path(d))
            (repo / "Subtitles").mkdir()
            (repo / "Subtitles" / "a.srt").write_text("x")
            (repo / "Subtitles" / "notes.txt").write_text("x")
            (repo / "README.md").write_text("x")
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "base", cwd=repo)
            base = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            (repo / "Subtitles" / "b.srt").write_text("y")
            (repo / "Subtitles" / "notes.txt").write_text("y")
            (repo / "README.md").write_text("y")
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "second", cwd=repo)
            head = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            out_file = repo / "changed.bin"
            result = subprocess.run(
                [sys.executable, str(FIND_CHANGED_PATH), base, head, str(out_file)],
                cwd=repo,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            paths = [p.decode("utf-8") for p in out_file.read_bytes().split(b"\0") if p]
            self.assertEqual(paths, ["Subtitles/b.srt"])

    def test_deleted_srt_file_is_not_reported(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(Path(d))
            (repo / "Subtitles").mkdir()
            (repo / "Subtitles" / "a.srt").write_text("x")
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "base", cwd=repo)
            base = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            (repo / "Subtitles" / "a.srt").unlink()
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "delete", cwd=repo)
            head = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            out_file = repo / "changed.bin"
            subprocess.run(
                [sys.executable, str(FIND_CHANGED_PATH), base, head, str(out_file)],
                cwd=repo,
                check=True,
            )
            paths = [p for p in out_file.read_bytes().split(b"\0") if p]
            self.assertEqual(paths, [])

    def test_filenames_with_spaces_and_unicode_are_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(Path(d))
            (repo / "Subtitles").mkdir()
            (repo / "Subtitles" / "empty.txt").write_text("x")
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "base", cwd=repo)
            base = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            tricky_name = "早晨 大家 (1989) -- 最佳.srt"
            (repo / "Subtitles" / tricky_name).write_text("y")
            _git("add", "-A", cwd=repo)
            _git("commit", "-q", "-m", "add tricky", cwd=repo)
            head = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            out_file = repo / "changed.bin"
            subprocess.run(
                [sys.executable, str(FIND_CHANGED_PATH), base, head, str(out_file)],
                cwd=repo,
                check=True,
            )
            paths = [p.decode("utf-8") for p in out_file.read_bytes().split(b"\0") if p]
            self.assertEqual(paths, [f"Subtitles/{tricky_name}"])


if __name__ == "__main__":
    unittest.main()
