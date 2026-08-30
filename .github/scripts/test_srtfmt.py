"""Tests for srtfmt.py: parser correctness and the idempotency property.

Stdlib unittest + random, deliberately -- no third-party test runner is
guaranteed to be installed for a script that itself has no dependencies
beyond stdlib. The property test seeds `random` for reproducibility.
"""

from __future__ import annotations

import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import srtlint
from srtfmt import (
    Cue,
    SrtParseError,
    assign_ids,
    check_file,
    decode_srt,
    diagnose,
    format_timestamp,
    normalize_bytes,
    normalize_text,
    parse,
    serialize,
    write_file,
)

SRTFMT_PATH = Path(__file__).resolve().parent / "srtfmt.py"


class ParseTests(unittest.TestCase):
    def test_basic_two_cue_file(self):
        text = (
            "1\n00:00:01,000 --> 00:00:04,000\n早晨\n\n"
            "2\n00:00:05,120 --> 00:00:08,400\n你食咗飯未呀\n"
        )
        cues = parse(text)
        self.assertEqual([c.start_ms for c in cues], [1000, 5120])
        self.assertEqual([c.end_ms for c in cues], [4000, 8400])
        self.assertEqual(cues[0].text, ["早晨"])

    def test_dot_millisecond_separator(self):
        text = "1\n00:00:01.000 --> 00:00:04.000\n喂\n"
        cues = parse(text)
        self.assertEqual(cues[0].start_ms, 1000)

    def test_missing_hour_zero_padding(self):
        text = "1\n1:00:01,000 --> 1:00:04,000\n喂\n"
        cues = parse(text)
        self.assertEqual(cues[0].start_ms, 3_601_000)

    def test_missing_cue_id(self):
        text = "00:00:01,000 --> 00:00:04,000\n喂\n\n00:00:05,000 --> 00:00:06,000\n哦\n"
        cues = parse(text)
        self.assertEqual(len(cues), 2)

    def test_non_sequential_duplicate_ids_are_ignored(self):
        text = "99\n00:00:01,000 --> 00:00:04,000\n喂\n\n99\n00:00:05,000 --> 00:00:06,000\n哦\n"
        cues = parse(text)
        self.assertEqual(len(cues), 2)

    def test_zero_blank_lines_between_cues(self):
        text = "1\n00:00:01,000 --> 00:00:04,000\n喂\n2\n00:00:05,000 --> 00:00:06,000\n哦\n"
        cues = parse(text)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].text, ["喂"])

    def test_multiple_blank_lines_between_cues(self):
        text = "1\n00:00:01,000 --> 00:00:04,000\n喂\n\n\n\n2\n00:00:05,000 --> 00:00:06,000\n哦\n"
        cues = parse(text)
        self.assertEqual(len(cues), 2)

    def test_multiline_cue_preserved(self):
        text = "1\n00:00:01,000 --> 00:00:04,000\n-兩蚊\n-哦，好嘅\n"
        cues = parse(text)
        self.assertEqual(cues[0].text, ["-兩蚊", "-哦，好嘅"])

    def test_override_tag_preserved_verbatim(self):
        text = "1\n00:00:01,000 --> 00:00:04,000\n{\\an8}吓？你做咩啊？\n"
        cues = parse(text)
        self.assertEqual(cues[0].text, ["{\\an8}吓？你做咩啊？"])

    def test_digit_only_text_line_not_confused_with_id(self):
        # Cue text that is itself a bare number should not be mistaken for
        # a following cue's ID line, since the line after it is not a
        # timestamp line.
        text = "1\n00:00:01,000 --> 00:00:04,000\n42\n"
        cues = parse(text)
        self.assertEqual(cues[0].text, ["42"])

    def test_unparseable_timestamp_is_hard_failure(self):
        text = "1\nnot a timestamp\n喂\n"
        with self.assertRaises(SrtParseError):
            parse(text)

    def test_cue_with_no_text_is_hard_failure(self):
        text = "1\n00:00:01,000 --> 00:00:04,000\n\n2\n00:00:05,000 --> 00:00:06,000\n哦\n"
        with self.assertRaises(SrtParseError):
            parse(text)

    def test_end_before_start_is_hard_failure(self):
        text = "1\n00:00:04,000 --> 00:00:01,000\n喂\n"
        with self.assertRaises(SrtParseError):
            parse(text)

    def test_out_of_order_cues_is_hard_failure(self):
        text = (
            "1\n00:00:05,000 --> 00:00:06,000\n哦\n\n"
            "2\n00:00:01,000 --> 00:00:04,000\n喂\n"
        )
        with self.assertRaises(SrtParseError):
            parse(text)

    def test_decode_utf8_bom(self):
        raw = b"\xef\xbb\xbf1\n00:00:01,000 --> 00:00:04,000\n\xe5\x96\x82\n"
        text = decode_srt(raw)
        self.assertFalse(text.startswith("﻿"))
        self.assertTrue(text.startswith("1\n"))

    def test_decode_utf16_le_bom(self):
        raw = "1\n00:00:01,000 --> 00:00:04,000\n喂\n".encode("utf-16-le")
        raw = b"\xff\xfe" + raw
        text = decode_srt(raw)
        self.assertTrue(text.startswith("1\n"))

    def test_crlf_and_lone_cr_normalized(self):
        text = decode_srt(b"1\r\n00:00:01,000 --> 00:00:04,000\r\n\xe5\x96\x82\r")
        self.assertNotIn("\r", text)


class AssignIdsTests(unittest.TestCase):
    def test_ids_equal_start_ms(self):
        cues = [Cue(1000, 4000, ["a"]), Cue(5120, 8400, ["b"])]
        self.assertEqual(assign_ids(cues), [1000, 5120])

    def test_zero_start_promoted_to_one(self):
        cues = [Cue(0, 500, ["a"])]
        self.assertEqual(assign_ids(cues), [1])

    def test_collision_increments_by_one(self):
        # {\an8} overlapping dialogue: two cues sharing a start time.
        cues = [
            Cue(1000, 2000, ["a"]),
            Cue(1000, 2000, ["b"]),
            Cue(1001, 3000, ["c"]),
        ]
        self.assertEqual(assign_ids(cues), [1000, 1001, 1002])

    def test_zero_start_collision_chain(self):
        cues = [Cue(0, 500, ["a"]), Cue(0, 500, ["b"]), Cue(1, 500, ["c"])]
        self.assertEqual(assign_ids(cues), [1, 2, 3])


class SerializeTests(unittest.TestCase):
    def test_canonical_shape(self):
        cues = [Cue(1000, 4000, ["早晨"]), Cue(5120, 8400, ["你食咗飯未呀"])]
        out = serialize(cues, assign_ids(cues))
        self.assertEqual(
            out,
            "1000\n00:00:01,000 --> 00:00:04,000\n早晨\n\n"
            "5120\n00:00:05,120 --> 00:00:08,400\n你食咗飯未呀\n",
        )

    def test_trailing_whitespace_stripped(self):
        cues = [Cue(1000, 4000, ["喂  \t"])]
        out = serialize(cues, assign_ids(cues))
        self.assertIn("喂\n", out)
        self.assertNotIn("喂  \t", out)

    def test_single_trailing_newline_no_blank_cue(self):
        cues = [Cue(1000, 4000, ["a"]), Cue(2000, 3000 + 4000, ["b"])]
        out = serialize(cues, assign_ids(cues))
        self.assertTrue(out.endswith("b\n"))
        self.assertFalse(out.endswith("\n\n"))


class CheckFileTests(unittest.TestCase):
    def test_canonical_file_passes(self):
        raw = b"1000\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n"
        ok, reasons = check_file(raw)
        self.assertTrue(ok)
        self.assertEqual(reasons, [])

    def test_hard_parse_failure_reports_single_human_readable_reason(self):
        raw = "1\nnot a timestamp\n喂\n".encode("utf-8")
        ok, reasons = check_file(raw)
        self.assertFalse(ok)
        self.assertEqual(len(reasons), 1)
        self.assertIn("unparseable timestamp", reasons[0])

    def test_utf8_bom_is_flagged(self):
        raw = b"\xef\xbb\xbf1\n00:00:01,000 --> 00:00:04,000\n\xe5\x96\x82\n"
        ok, reasons = check_file(raw)
        self.assertFalse(ok)
        self.assertTrue(any("UTF-8 with a BOM" in r for r in reasons))

    def test_utf16_is_flagged(self):
        body = "1\n00:00:01,000 --> 00:00:04,000\n喂\n"
        raw = b"\xff\xfe" + body.encode("utf-16-le")
        ok, reasons = check_file(raw)
        self.assertFalse(ok)
        self.assertTrue(any("UTF-16" in r for r in reasons))

    def test_crlf_is_flagged(self):
        raw = b"1\r\n00:00:01,000 --> 00:00:04,000\r\n\xe5\x96\x82\r\n"
        ok, reasons = check_file(raw)
        self.assertFalse(ok)
        self.assertTrue(any("CRLF" in r for r in reasons))

    def test_missing_trailing_newline_is_not_flagged(self):
        # No parser cares, and which convention a file ends up with is an
        # artifact of whatever editor last saved it, not a contributor
        # mistake -- --write fixes it silently.
        raw = b"1000\n00:00:01,000 --> 00:00:04,000\n\xe5\x96\x82"
        ok, reasons = check_file(raw)
        self.assertTrue(ok, reasons)

    def test_trailing_blank_lines_are_not_flagged(self):
        raw = b"1000\n00:00:01,000 --> 00:00:04,000\n\xe5\x96\x82\n\n\n"
        ok, reasons = check_file(raw)
        self.assertTrue(ok, reasons)

    def test_a_single_cue_with_any_id_value_passes(self):
        # No previous cue to compare against, so nothing can be "out of
        # order" -- an arbitrary ID on a lone cue is not a failure.
        raw = b"99\n00:00:01,000 --> 00:00:04,000\n\xe5\x96\x82\n"
        ok, reasons = check_file(raw)
        self.assertTrue(ok, reasons)

    def test_missing_cue_id_is_not_flagged(self):
        raw = b"00:00:01,000 --> 00:00:04,000\n\xe5\x96\x82\n"
        ok, reasons = check_file(raw)
        self.assertTrue(ok, reasons)

    def test_dot_separator_is_flagged(self):
        raw = b"1000\n00:00:01.000 --> 00:00:04.000\n\xe5\x96\x82\n"
        ok, reasons = check_file(raw)
        self.assertFalse(ok)
        self.assertTrue(any("millisecond separator" in r for r in reasons))

    def test_unpadded_hour_is_flagged(self):
        raw = b"3601000\n1:00:01,000 --> 1:00:04,000\n\xe5\x96\x82\n"
        ok, reasons = check_file(raw)
        self.assertFalse(ok)
        self.assertTrue(any("zero-padded" in r for r in reasons))

    def test_trailing_whitespace_on_text_line_is_flagged(self):
        raw = "1000\n00:00:01,000 --> 00:00:04,000\n喂  \n".encode("utf-8")
        ok, reasons = check_file(raw)
        self.assertFalse(ok)
        self.assertTrue(any("trailing whitespace" in r for r in reasons))

    def test_wrong_blank_line_count_is_flagged(self):
        raw = (
            "1000\n00:00:01,000 --> 00:00:04,000\n喂\n\n\n"
            "5000\n00:00:05,000 --> 00:00:06,000\n哦\n"
        ).encode("utf-8")
        ok, reasons = check_file(raw)
        self.assertFalse(ok)
        self.assertTrue(any("blank line(s) before this cue" in r for r in reasons))

    def _sequential_blocks(self, n: int, t0: int = 1000, step: int = 2000) -> list[str]:
        blocks = []
        t = t0
        for idx in range(1, n + 1):
            blocks.append(f"{idx}\n{format_timestamp(t)} --> {format_timestamp(t + 500)}\n喂")
            t += step
        return blocks

    def test_editor_renumbered_plain_sequential_ids_pass(self):
        # The core scenario this component exists to handle: a contributor
        # opens a canonical file in an ordinary subtitle editor, fixes one
        # line, and saves -- the editor renumbers every cue 1..N as a side
        # effect. That must not fail the PR check; --write silently fixes
        # IDs on merge to main regardless of what they were.
        raw = ("\n\n".join(self._sequential_blocks(50)) + "\n").encode("utf-8")
        ok, reasons = check_file(raw)
        self.assertTrue(ok, reasons)

    def test_arbitrary_but_strictly_ascending_ids_pass(self):
        # IDs need not be canonical *or* plain sequential -- just well-ordered.
        blocks = [
            f"{cue_id}\n{format_timestamp(t)} --> {format_timestamp(t + 500)}\n喂"
            for cue_id, t in [(5, 1000), (12, 3000), (47, 5000)]
        ]
        raw = ("\n\n".join(blocks) + "\n").encode("utf-8")
        ok, reasons = check_file(raw)
        self.assertTrue(ok, reasons)

    def test_transposed_id_is_flagged_as_out_of_order(self):
        # Regression: a file that is otherwise plain sequential (as any
        # editor would leave it) but has a couple of cue IDs hand-edited into
        # a mistake (duplicated / transposed) must still surface those
        # specific lines, even though plain renumbering elsewhere is fine.
        blocks = self._sequential_blocks(10)
        blocks[4] = blocks[4].replace("5\n", "3\n", 1)  # duplicate of cue 3's ID
        blocks[6] = blocks[6].replace("7\n", "8\n", 1)  # transposed with cue 8
        blocks[7] = blocks[7].replace("8\n", "7\n", 1)
        raw = ("\n\n".join(blocks) + "\n").encode("utf-8")

        ok, reasons = check_file(raw)
        self.assertFalse(ok)

        order_lines = [r for r in reasons if "not greater than the previous" in r]
        self.assertEqual(len(order_lines), 2, reasons)
        self.assertTrue(any("cue ID is 3" in r for r in order_lines))
        self.assertTrue(any("cue ID is 7" in r for r in order_lines))

    def test_diagnose_on_canonical_input_is_empty(self):
        cues = parse("1000\n00:00:01,000 --> 00:00:04,000\n喂\n")
        ids = assign_ids(cues)
        raw = serialize(cues, ids).encode("utf-8")
        self.assertEqual(diagnose(raw, cues), [])


class CheckCliTests(unittest.TestCase):
    def _run(self, *paths: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SRTFMT_PATH), "--check", *(str(p) for p in paths)],
            capture_output=True,
            text=True,
        )

    def test_canonical_file_exits_zero_with_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "canonical.srt"
            path.write_bytes(b"1000\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_non_canonical_file_exits_one_and_reports(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.srt"
            path.write_bytes(b"\xef\xbb\xbf1\n00:00:01,000 --> 00:00:04,000\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn(str(path), result.stdout)
            self.assertIn("BOM", result.stdout)

    def test_mixed_files_exit_one_and_only_report_the_bad_one(self):
        with tempfile.TemporaryDirectory() as d:
            good = Path(d) / "good.srt"
            good.write_bytes(b"1000\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n")
            bad = Path(d) / "bad.srt"
            bad.write_bytes(b"1\nnot a timestamp\n\xe5\x96\x82\n")
            result = self._run(good, bad)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn(str(good), result.stdout)
            self.assertIn(str(bad), result.stdout)


class WriteFileTests(unittest.TestCase):
    def test_canonical_input_is_reported_unchanged(self):
        raw = b"1000\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n"
        canonical, changed = write_file(raw)
        self.assertFalse(changed)
        self.assertEqual(canonical, raw)

    def test_sequential_ids_are_rewritten_to_start_time_derived(self):
        # Unlike --check, --write fully canonicalizes IDs -- this is where
        # editor-renumbered files actually get fixed on merge to main.
        raw = b"1\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n"
        canonical, changed = write_file(raw)
        self.assertTrue(changed)
        self.assertTrue(canonical.startswith(b"1000\n"))

    def test_hard_parse_failure_raises(self):
        raw = b"1\nnot a timestamp\n\xe5\x96\x82\n"
        with self.assertRaises(SrtParseError):
            write_file(raw)


class WriteCliTests(unittest.TestCase):
    def _run(self, *paths: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SRTFMT_PATH), "--write", *(str(p) for p in paths)],
            capture_output=True,
            text=True,
        )

    def test_canonical_file_is_untouched_and_silent(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "canonical.srt"
            raw = b"1000\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n"
            path.write_bytes(raw)
            mtime_before = path.stat().st_mtime_ns
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(path.stat().st_mtime_ns, mtime_before)
            self.assertEqual(path.read_bytes(), raw)

    def test_non_canonical_file_is_rewritten_and_reported(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "messy.srt"
            path.write_bytes(
                b"\xef\xbb\xbf1\r\n00:00:01.000 --> 00:00:04.000\r\n\xe5\x96\x82\r\n"
            )
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertIn("reformatted", result.stdout)
            self.assertIn(str(path), result.stdout)
            self.assertEqual(
                path.read_bytes(),
                "1000\n00:00:01,000 --> 00:00:04,000\n喂\n".encode("utf-8"),
            )

    def test_write_output_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "messy.srt"
            path.write_bytes(b"1\n00:00:01.000 --> 00:00:04.000\n\xe5\x96\x82\n")
            self._run(path)
            once = path.read_bytes()
            result = self._run(path)
            self.assertEqual(result.stdout, "")  # nothing left to reformat
            self.assertEqual(path.read_bytes(), once)

    def test_hard_parse_failure_is_reported_and_left_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "broken.srt"
            raw = b"1\nnot a timestamp\n\xe5\x96\x82\n"
            path.write_bytes(raw)
            result = self._run(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn(str(path), result.stdout)
            self.assertEqual(path.read_bytes(), raw)


class LintTests(unittest.TestCase):
    def _cues(self, text: str) -> list[Cue]:
        return parse(text)

    def test_canonical_short_cue_has_no_warnings(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:04,000\n喂\n")
        self.assertEqual(srtlint.lint(cues), [])

    def test_long_line_is_flagged(self):
        # 18 full-width characters, over the 17.5 limit.
        text = "早" * 18
        cues = self._cues(f"1000\n00:00:01,000 --> 00:00:05,000\n{text}\n")
        warnings = srtlint.lint(cues)
        self.assertTrue(any("18 characters" in w and "17.5" in w for w in warnings))

    def test_half_width_characters_count_as_half(self):
        # 35 ASCII characters == 17.5 width exactly -- must NOT be flagged
        # (the rule is "longer than 17.5", not "17.5 or more").
        text = "a" * 35
        cues = self._cues(f"1000\n00:00:01,000 --> 00:00:05,000\n{text}\n")
        self.assertEqual(srtlint.lint(cues), [])

    def test_short_cue_under_400ms_is_flagged(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:01,100\n喂\n")
        warnings = srtlint.lint(cues)
        self.assertTrue(any("100ms" in w and "400ms" in w for w in warnings))

    def test_longer_text_needs_750ms(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:01,500\n早晨大家\n")
        warnings = srtlint.lint(cues)
        self.assertTrue(any("500ms" in w and "750ms" in w for w in warnings))

    def test_short_text_only_needs_400ms(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:01,500\n喂\n")
        self.assertEqual(srtlint.lint(cues), [])

    def test_trailing_period_is_flagged(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:04,000\n我個名叫Tom。\n")
        warnings = srtlint.lint(cues)
        self.assertTrue(any("ends in" in w and "。" in w for w in warnings))

    def test_trailing_ascii_period_is_flagged(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:04,000\nOK.\n")
        warnings = srtlint.lint(cues)
        self.assertTrue(any("ends in" in w for w in warnings))

    def test_ellipsis_is_not_flagged(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:04,000\n係啊…\n")
        self.assertEqual(srtlint.lint(cues), [])

    def test_double_ellipsis_is_flagged(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:04,000\n係啊……\n")
        warnings = srtlint.lint(cues)
        self.assertTrue(any("……" in w for w in warnings))

    def test_middle_dot_is_flagged(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:04,000\n哈利·波特\n")
        warnings = srtlint.lint(cues)
        self.assertTrue(any("middle dot" in w for w in warnings))

    def test_italic_html_tag_is_flagged(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:04,000\n<i>喂</i>\n")
        warnings = srtlint.lint(cues)
        self.assertTrue(any("italic" in w for w in warnings))

    def test_italic_ass_tag_is_flagged(self):
        cues = self._cues("1000\n00:00:01,000 --> 00:00:04,000\n{\\i1}喂{\\i0}\n")
        warnings = srtlint.lint(cues)
        self.assertTrue(any("italic" in w for w in warnings))

    def test_override_tag_is_not_counted_toward_line_length_or_flagged_as_italic(self):
        # {\an8} is a position override, not italics, and shouldn't count
        # toward the visible-character line-length limit.
        cues = self._cues("1000\n00:00:01,000 --> 00:00:05,000\n{\\an8}喂\n")
        self.assertEqual(srtlint.lint(cues), [])

    def test_parse_error_propagates_to_caller(self):
        with self.assertRaises(SrtParseError):
            self._cues("1\nnot a timestamp\n喂\n")


class LintCliTests(unittest.TestCase):
    def _run(self, *paths: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SRTFMT_PATH), "--lint", *(str(p) for p in paths)],
            capture_output=True,
            text=True,
        )

    def test_lint_never_fails_the_build(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.srt"
            path.write_bytes(b"1000\n00:00:01,000 --> 00:00:01,100\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertIn("100ms", result.stdout)

    def test_clean_cue_produces_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "clean.srt"
            path.write_bytes(b"1000\n00:00:01,000 --> 00:00:04,000\n\xe6\x97\xa9\xe6\x99\xa8\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_hard_parse_failure_is_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "broken.srt"
            path.write_bytes(b"1\nnot a timestamp\n\xe5\x96\x82\n")
            result = self._run(path)
            self.assertEqual(result.returncode, 0)
            self.assertIn("skipped", result.stdout)


# --- Idempotency property test -------------------------------------------
#
# normalize(normalize(x)) == normalize(x) is the property most likely to
# break subtly (spec, "Idempotency requirement"). Rather than pull in a
# third-party property-testing library for a stdlib-only component, this
# generates many randomized-but-valid cue sequences, renders each one with
# randomized *malformed* framing (BOM, line endings, separators, ID scheme,
# blank-line count, trailing whitespace), and checks that normalizing twice
# is the same as normalizing once.

CJK_WORDS = ["早晨", "食咗飯未呀", "喂", "哦，好嘅", "{\\an8}吓？你做咩啊？", "-兩蚊", "-啊，嚟"]


def _random_cue_sequence(rng: random.Random, count: int) -> list[Cue]:
    cues = []
    t = rng.randint(0, 2000)
    for _ in range(count):
        t += rng.randint(0, 5000)
        start = t
        end = start + rng.randint(400, 3000)
        num_lines = rng.choice([1, 1, 1, 2])
        text = [rng.choice(CJK_WORDS) for _ in range(num_lines)]
        cues.append(Cue(start, end, text))
        t = end
        if rng.random() < 0.15 and cues:
            # Occasionally add a same-start-time overlap cue (background dialogue).
            cues.append(Cue(start, end, [rng.choice(CJK_WORDS)]))
    return cues


def _render_malformed(rng: random.Random, cues: list[Cue]) -> bytes:
    """Render a valid cue sequence as a deliberately non-canonical .srt file."""
    sep = rng.choice([",", "."])
    pad_hours = rng.choice([True, False])
    arrow_spacing = rng.choice([" --> ", "-->", "  -->  "])
    blank_lines = rng.choice([1, 1, 0, 2, 3])
    id_scheme = rng.choice(["sequential", "random", "missing", "duplicate"])
    trailing_ws = rng.choice([True, False])
    trailing_newline = rng.choice([True, False])

    def ts(ms: int) -> str:
        h, rem = divmod(ms, 3_600_000)
        m, rem = divmod(rem, 60_000)
        s, msec = divmod(rem, 1000)
        h_str = f"{h:02d}" if pad_hours else str(h)
        return f"{h_str}:{m:02d}:{s:02d}{sep}{msec:03d}"

    blocks = []
    for idx, cue in enumerate(cues):
        lines = []
        if id_scheme == "sequential":
            lines.append(str(idx + 1))
        elif id_scheme == "random":
            lines.append(str(rng.randint(1, 999)))
        elif id_scheme == "duplicate":
            lines.append("1")
        # "missing": no ID line at all.
        lines.append(f"{ts(cue.start_ms)}{arrow_spacing}{ts(cue.end_ms)}")
        for line in cue.text:
            lines.append(line + ("   " if trailing_ws else ""))
        blocks.append("\n".join(lines))

    body = ("\n" * (blank_lines + 1)).join(blocks)
    if trailing_newline:
        body += "\n"
    if rng.random() < 0.3:
        # CRLF conversion must happen before encoding -- doing it on already
        # -encoded UTF-16 bytes would corrupt multi-byte characters.
        body = body.replace("\n", "\r\n")

    encoding = rng.choice(["utf-8", "utf-8-bom", "utf-16-le", "utf-16-be"])
    if encoding == "utf-8":
        raw = body.encode("utf-8")
    elif encoding == "utf-8-bom":
        raw = b"\xef\xbb\xbf" + body.encode("utf-8")
    elif encoding == "utf-16-le":
        raw = b"\xff\xfe" + body.encode("utf-16-le")
    else:
        raw = b"\xfe\xff" + body.encode("utf-16-be")

    return raw


class IdempotencyPropertyTest(unittest.TestCase):
    TRIALS = 300

    def test_normalize_is_idempotent_on_randomized_malformed_input(self):
        rng = random.Random(1234567)
        for trial in range(self.TRIALS):
            cues = _random_cue_sequence(rng, rng.randint(1, 12))
            raw = _render_malformed(rng, cues)

            once = normalize_bytes(raw)
            twice = normalize_bytes(once)

            self.assertEqual(
                once,
                twice,
                f"trial {trial}: normalize(normalize(x)) != normalize(x)\n"
                f"input={raw!r}\nonce={once!r}\ntwice={twice!r}",
            )

    def test_normalize_text_is_idempotent_directly(self):
        rng = random.Random(7654321)
        for trial in range(self.TRIALS):
            cues = _random_cue_sequence(rng, rng.randint(1, 12))
            raw = _render_malformed(rng, cues)
            text = decode_srt(raw)
            once = normalize_text(text)
            twice = normalize_text(once)
            self.assertEqual(once, twice, f"trial {trial}: text-level idempotency broke")

    def test_canonical_output_round_trips_through_format_timestamp(self):
        # Sanity check tying format_timestamp to the regex parse() relies on.
        for ms in [0, 1, 999, 1000, 59_999, 3_600_000, 12_345_678]:
            self.assertEqual(
                parse(f"1\n{format_timestamp(ms)} --> {format_timestamp(ms + 1000)}\n喂\n")[
                    0
                ].start_ms,
                ms,
            )


if __name__ == "__main__":
    unittest.main()
