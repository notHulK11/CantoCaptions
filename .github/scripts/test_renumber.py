"""Tests for renumber.py: cue numbers change, and nothing else does."""

from __future__ import annotations

import unittest

from renumber import SkipFile, renumber_bytes


class RenumberTests(unittest.TestCase):
    def test_start_time_ids_become_sequential(self):
        raw = (
            "1000\n00:00:01,000 --> 00:00:04,000\n早晨\n\n"
            "5120\n00:00:05,120 --> 00:00:08,400\n你食咗飯未呀\n"
        ).encode("utf-8")
        self.assertEqual(
            renumber_bytes(raw),
            (
                "1\n00:00:01,000 --> 00:00:04,000\n早晨\n\n"
                "2\n00:00:05,120 --> 00:00:08,400\n你食咗飯未呀\n"
            ).encode("utf-8"),
        )

    def test_already_sequential_is_unchanged(self):
        raw = b"1\n00:00:01,000 --> 00:00:04,000\na\n\n2\n00:00:05,000 --> 00:00:06,000\nb\n"
        self.assertEqual(renumber_bytes(raw), raw)

    def test_file_order_is_kept_even_when_out_of_chronological_order(self):
        # Subtitle Edit bookmarks are 0-based positions, so cues must never move.
        raw = b"9\n00:00:05,000 --> 00:00:06,000\nlater\n\n3\n00:00:01,000 --> 00:00:02,000\nearlier\n"
        self.assertEqual(
            renumber_bytes(raw),
            b"1\n00:00:05,000 --> 00:00:06,000\nlater\n\n2\n00:00:01,000 --> 00:00:02,000\nearlier\n",
        )

    def test_bom_crlf_whitespace_and_blank_lines_are_preserved(self):
        raw = (
            b"\xef\xbb\xbf500\r\n00:00:01.000-->00:00:04.000\r\ntext  \r\n\r\n\r\n"
            b"900\r\n00:00:05,000 --> 00:00:06,000\r\nmore\r\n\r\n"
        )
        self.assertEqual(
            renumber_bytes(raw),
            b"\xef\xbb\xbf1\r\n00:00:01.000-->00:00:04.000\r\ntext  \r\n\r\n\r\n"
            b"2\r\n00:00:05,000 --> 00:00:06,000\r\nmore\r\n\r\n",
        )

    def test_digit_only_subtitle_text_is_not_renumbered(self):
        raw = b"1000\n00:00:01,000 --> 00:00:04,000\n42\n\n2000\n00:00:05,000 --> 00:00:06,000\n7\n"
        out = renumber_bytes(raw)
        self.assertEqual(
            out, b"1\n00:00:01,000 --> 00:00:04,000\n42\n\n2\n00:00:05,000 --> 00:00:06,000\n7\n"
        )

    def test_empty_cue_keeps_its_position(self):
        # An empty cue is still a cue to Subtitle Edit; skipping it would
        # shift every bookmark after it.
        raw = b"10\n00:00:01,000 --> 00:00:02,000\n\n20\n00:00:03,000 --> 00:00:04,000\nb\n"
        self.assertEqual(
            renumber_bytes(raw),
            b"1\n00:00:01,000 --> 00:00:02,000\n\n2\n00:00:03,000 --> 00:00:04,000\nb\n",
        )

    def test_cue_without_a_number_is_skipped(self):
        raw = b"1\n00:00:01,000 --> 00:00:02,000\na\n\n00:00:03,000 --> 00:00:04,000\nb\n"
        with self.assertRaises(SkipFile):
            renumber_bytes(raw)

    def test_number_with_no_blank_line_before_it_is_skipped(self):
        raw = b"1\n00:00:01,000 --> 00:00:02,000\na\n5\n00:00:03,000 --> 00:00:04,000\nb\n"
        with self.assertRaises(SkipFile):
            renumber_bytes(raw)

    def test_non_utf8_is_skipped(self):
        with self.assertRaises(SkipFile):
            renumber_bytes(b"1\n00:00:01,000 --> 00:00:02,000\n\xb3\xde\n")

    def test_utf16_is_skipped(self):
        body = "5\n00:00:01,000 --> 00:00:02,000\na\n"
        with self.assertRaises(SkipFile):
            renumber_bytes(b"\xff\xfe" + body.encode("utf-16-le"))

    def test_no_trailing_newline_is_preserved(self):
        raw = b"7\n00:00:01,000 --> 00:00:02,000\na"
        self.assertEqual(renumber_bytes(raw), b"1\n00:00:01,000 --> 00:00:02,000\na")

    def test_unicode_line_separators_in_text_are_not_treated_as_line_breaks(self):
        raw = "7\n00:00:01,000 --> 00:00:02,000\na b\x0cc\n".encode("utf-8")
        self.assertEqual(
            renumber_bytes(raw), "1\n00:00:01,000 --> 00:00:02,000\na b\x0cc\n".encode("utf-8")
        )


if __name__ == "__main__":
    unittest.main()
