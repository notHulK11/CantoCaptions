"""Tests for normalize_pr.py.

Only the file-rewriting core is covered here -- the git/gh orchestration
around it is thin shell-outs that would need a live GitHub PR to exercise
meaningfully.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from normalize_pr import normalize_paths

SEQUENTIAL = b"1\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n"
CANONICAL = b"1000\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n"


class NormalizePathsTests(unittest.TestCase):
    def test_editor_renumbered_file_is_rewritten_to_canonical(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Subtitles").mkdir()
            rel = "Subtitles/a.srt"
            (root / rel).write_bytes(SEQUENTIAL)

            changed, failed = normalize_paths([rel], root)

            self.assertEqual(changed, [rel])
            self.assertEqual(failed, [])
            self.assertEqual((root / rel).read_bytes(), CANONICAL)

    def test_already_canonical_file_is_not_reported_as_changed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Subtitles").mkdir()
            rel = "Subtitles/a.srt"
            (root / rel).write_bytes(CANONICAL)

            changed, failed = normalize_paths([rel], root)

            self.assertEqual(changed, [])
            self.assertEqual(failed, [])
            self.assertEqual((root / rel).read_bytes(), CANONICAL)

    def test_deleted_path_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            changed, failed = normalize_paths(["Subtitles/gone.srt"], root)
            self.assertEqual(changed, [])
            self.assertEqual(failed, [])

    def test_unparseable_file_is_reported_and_left_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Subtitles").mkdir()
            rel = "Subtitles/broken.srt"
            raw = b"1\nnot a timestamp\n\xe5\x96\x82\n"
            (root / rel).write_bytes(raw)

            changed, failed = normalize_paths([rel], root)

            self.assertEqual(changed, [])
            self.assertEqual(len(failed), 1)
            self.assertEqual(failed[0][0], rel)
            self.assertIn("unparseable timestamp", failed[0][1])
            self.assertEqual((root / rel).read_bytes(), raw)

    def test_one_broken_file_does_not_block_the_others(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Subtitles").mkdir()
            (root / "Subtitles/good.srt").write_bytes(SEQUENTIAL)
            (root / "Subtitles/broken.srt").write_bytes(b"1\nnope\n\xe5\x96\x82\n")

            changed, failed = normalize_paths(
                ["Subtitles/good.srt", "Subtitles/broken.srt"], root
            )

            self.assertEqual(changed, ["Subtitles/good.srt"])
            self.assertEqual([f[0] for f in failed], ["Subtitles/broken.srt"])
            self.assertEqual((root / "Subtitles/good.srt").read_bytes(), CANONICAL)

    def test_result_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Subtitles").mkdir()
            rel = "Subtitles/a.srt"
            (root / rel).write_bytes(SEQUENTIAL)

            normalize_paths([rel], root)
            changed, _ = normalize_paths([rel], root)

            self.assertEqual(changed, [])

    def test_unicode_and_space_heavy_filename_is_handled(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Subtitles").mkdir()
            rel = "Subtitles/早晨 大家 (1989) -- 最佳.srt"
            (root / rel).write_bytes(SEQUENTIAL)

            changed, failed = normalize_paths([rel], root)

            self.assertEqual(changed, [rel])
            self.assertEqual(failed, [])


if __name__ == "__main__":
    unittest.main()
