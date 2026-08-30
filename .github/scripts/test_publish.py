"""Tests for publish.py.

Covers the git-status parsing (the fiddly part -- NUL-separated records,
rename entries carrying a second path) and the end-to-end commit/push flow
against a real local repo with a real remote.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from publish import changed_srt_paths

PUBLISH_PATH = Path(__file__).resolve().parent / "publish.py"
SCRIPTS_DIR = Path(__file__).resolve().parent

SEQUENTIAL = b"1\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n"
CANONICAL = b"1000\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n"


class ChangedSrtPathsTests(unittest.TestCase):
    def test_modified_added_and_untracked_are_all_picked_up(self):
        status = "\0".join([" M Subtitles/a.srt", "A  Subtitles/b.srt", "?? Subtitles/c.srt"]) + "\0"
        self.assertEqual(
            changed_srt_paths(status),
            ["Subtitles/a.srt", "Subtitles/b.srt", "Subtitles/c.srt"],
        )

    def test_non_srt_and_non_subtitles_paths_are_ignored(self):
        status = "\0".join([" M README.md", " M Subtitles/notes.txt", " M docs/x.srt"]) + "\0"
        self.assertEqual(changed_srt_paths(status), [])

    def test_rename_entry_consumes_its_source_path(self):
        # `git status -z` emits a rename as "R  <new>\0<old>\0" -- the source
        # must not be mistaken for a separate changed file.
        status = "R  Subtitles/new.srt\0Subtitles/old.srt\0 M Subtitles/other.srt\0"
        self.assertEqual(
            changed_srt_paths(status), ["Subtitles/new.srt", "Subtitles/other.srt"]
        )

    def test_unicode_and_space_heavy_paths_survive(self):
        rel = "Subtitles/早晨 大家 (1989) -- 最佳.srt"
        self.assertEqual(changed_srt_paths(f" M {rel}\0"), [rel])

    def test_empty_status_yields_nothing(self):
        self.assertEqual(changed_srt_paths(""), [])


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


class PublishEndToEndTests(unittest.TestCase):
    def _make_repo(self, d: str) -> Path:
        repo = Path(d) / "repo"
        (repo / ".github" / "scripts").mkdir(parents=True)
        for name in ("srtfmt.py", "srtlint.py", "publish.py"):
            (repo / ".github" / "scripts" / name).write_bytes((SCRIPTS_DIR / name).read_bytes())
        (repo / ".gitignore").write_text("__pycache__/\n*.pyc\n")
        (repo / "Subtitles").mkdir()
        _git("init", "-q", ".", cwd=repo)
        _git("config", "user.email", "t@e.com", cwd=repo)
        _git("config", "user.name", "T", cwd=repo)
        _git("add", "-A", cwd=repo)
        _git("commit", "-qm", "init", cwd=repo)

        remote = Path(d) / "remote.git"
        _git("init", "-q", "--bare", str(remote), cwd=Path(d))
        _git("remote", "add", "origin", str(remote), cwd=repo)
        branch = _git("rev-parse", "--abbrev-ref", "HEAD", cwd=repo).stdout.strip()
        _git("push", "-q", "-u", "origin", branch, cwd=repo)
        return repo

    def _publish(self, repo: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, ".github/scripts/publish.py", *args],
            cwd=repo,
            capture_output=True,
            text=True,
        )

    def test_normalizes_commits_and_pushes(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(d)
            (repo / "Subtitles" / "ep1.srt").write_bytes(SEQUENTIAL)

            result = self._publish(repo, "-m", "Add ep1", "--yes")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((repo / "Subtitles" / "ep1.srt").read_bytes(), CANONICAL)
            log = _git("log", "--oneline", "@{u}", cwd=repo).stdout
            self.assertIn("Add ep1", log)

    def test_nothing_to_do_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(d)
            result = self._publish(repo, "-m", "noop", "--yes")
            self.assertEqual(result.returncode, 0)
            self.assertIn("Nothing to do", result.stdout)

    def test_broken_file_blocks_the_commit(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(d)
            (repo / "Subtitles" / "broken.srt").write_bytes(b"1\nnope\n\xe5\x96\x82\n")

            result = self._publish(repo, "-m", "Add broken", "--yes")

            self.assertEqual(result.returncode, 1)
            self.assertIn("need fixing", result.stdout)
            self.assertIn("Nothing has been committed", result.stdout)
            log = _git("log", "--oneline", cwd=repo).stdout
            self.assertNotIn("Add broken", log)

    def test_non_srt_changes_are_left_uncommitted(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(d)
            (repo / "Subtitles" / "ep1.srt").write_bytes(CANONICAL)
            (repo / "README.md").write_text("unrelated edit")

            result = self._publish(repo, "-m", "Add ep1", "--yes")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            still_dirty = _git("status", "--porcelain", cwd=repo).stdout
            self.assertIn("README.md", still_dirty)

    def test_no_normalize_leaves_files_alone(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(d)
            (repo / "Subtitles" / "ep1.srt").write_bytes(SEQUENTIAL)

            result = self._publish(repo, "-m", "Add ep1", "--yes", "--no-normalize")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((repo / "Subtitles" / "ep1.srt").read_bytes(), SEQUENTIAL)

    def test_style_warnings_do_not_block(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(d)
            # 100ms cue: a lint warning, not a check failure.
            (repo / "Subtitles" / "ep1.srt").write_bytes(
                b"1000\n00:00:01,000 --> 00:00:01,100\n\xe5\x96\x82\n"
            )

            result = self._publish(repo, "-m", "Add ep1", "--yes")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("style warning", result.stdout)
            self.assertIn("Add ep1", _git("log", "--oneline", cwd=repo).stdout)


    def _reject_pushes(self, repo: Path, message: str) -> None:
        """Make the bare remote refuse pushes, the way GitHub does."""
        remote = (repo.parent / "remote.git" / "hooks" / "pre-receive")
        remote.write_text(f'#!/bin/sh\necho "{message}" >&2\nexit 1\n')
        remote.chmod(0o755)

    def test_no_write_access_rolls_back_and_points_at_pr(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(d)
            self._reject_pushes(
                repo, "remote: Permission to owner/repo.git denied to someone."
            )
            (repo / "Subtitles" / "ep1.srt").write_bytes(SEQUENTIAL)
            before = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            result = self._publish(repo, "-m", "Add ep1", "--yes")

            self.assertEqual(result.returncode, 1)
            self.assertIn("do not have permission", result.stdout)
            self.assertIn("--pr", result.stdout)
            # The wrong advice must not appear: rebasing cannot fix this.
            self.assertNotIn("git pull --rebase", result.stdout)
            # Commit rolled back, edits preserved so a --pr rerun finds them.
            self.assertEqual(_git("rev-parse", "HEAD", cwd=repo).stdout.strip(), before)
            self.assertIn("Subtitles/ep1.srt", _git("status", "--porcelain", cwd=repo).stdout)

    def test_protected_branch_rolls_back_and_points_at_pr(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(d)
            self._reject_pushes(
                repo, "remote: error: GH006: Protected branch update failed."
            )
            (repo / "Subtitles" / "ep1.srt").write_bytes(SEQUENTIAL)
            before = _git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            result = self._publish(repo, "-m", "Add ep1", "--yes")

            self.assertEqual(result.returncode, 1)
            self.assertIn("protected branch", result.stdout)
            self.assertNotIn("git pull --rebase", result.stdout)
            self.assertEqual(_git("rev-parse", "HEAD", cwd=repo).stdout.strip(), before)

    def test_stale_branch_keeps_the_commit_and_advises_rebase(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._make_repo(d)
            # Advance the remote behind our back, like the normalize bot does.
            other = Path(d) / "other"
            _git("clone", "-q", str(repo.parent / "remote.git"), str(other), cwd=Path(d))
            _git("config", "user.email", "b@e.com", cwd=other)
            _git("config", "user.name", "Bot", cwd=other)
            (other / "bot.txt").write_text("x")
            _git("add", "-A", cwd=other)
            _git("commit", "-qm", "Normalize subtitle formatting [skip ci]", cwd=other)
            _git("push", "-q", cwd=other)

            (repo / "Subtitles" / "ep1.srt").write_bytes(SEQUENTIAL)
            result = self._publish(repo, "-m", "Add ep1", "--yes")

            self.assertEqual(result.returncode, 1)
            self.assertIn("git pull --rebase", result.stdout)
            self.assertNotIn("do not have permission", result.stdout)
            # Commit is kept here: rebasing is the fix, so it must survive.
            self.assertIn("Add ep1", _git("log", "--oneline", cwd=repo).stdout)


if __name__ == "__main__":
    unittest.main()
