#!/usr/bin/env python3
"""Renumber .srt cues 1, 2, 3... in file order, changing nothing else.

Byte-preserving by design: only the digits on each cue-number line change.
Encoding, BOM, line endings, whitespace, blank lines, timestamps, text and --
most importantly -- cue order and cue count are left exactly as they were.
That matters for Subtitle Edit's .SE.bookmarks files, which store each
bookmark as {"idx": N}, a 0-based *position* in the file rather than a cue
number: as long as no cue moves, every bookmark still points at the same cue.

This is deliberately not srtfmt.py's --write, which re-serializes the whole
file (stripping BOMs, converting line endings, collapsing blank lines). That
is fine for a file someone is actively tidying, but far too much to apply
across thousands of files at once.

A cue-number line is a line holding only digits that sits directly above a
timestamp line, and is either the first line of the file or follows a blank
line. If a file has a different number of those than it has timestamp lines
(a cue with no number, or a number with no blank line before it), it is
skipped and reported rather than guessed at.

Usage:
    python3 .github/scripts/renumber.py <file.srt>...        # dry run
    python3 .github/scripts/renumber.py --all                # dry run, every file under Subtitles/
    python3 .github/scripts/renumber.py --write <file.srt>...
    python3 .github/scripts/renumber.py --write --all

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from srtfmt import TIMESTAMP_RE

REPO_ROOT = Path(__file__).resolve().parents[2]
UTF8_BOM = b"\xef\xbb\xbf"
_NUMBER_LINE_RE = re.compile(r"^\s*\d+\s*$", re.ASCII)
_LINE_RE = re.compile(r"([^\r\n]*)(\r\n|\r|\n|$)")


class SkipFile(Exception):
    """The file can't be renumbered without guessing. Message is for a human."""


def _split_lines(text: str) -> list[tuple[str, str]]:
    """Split into (content, line ending) pairs, keeping each ending exactly.

    Not str.splitlines(): that also splits on form feeds, U+2028 and other
    characters that subtitle text may legitimately contain, and rejoining
    would then silently alter them.
    """
    lines = []
    for m in _LINE_RE.finditer(text):
        content, ending = m.groups()
        if not content and not ending:
            break  # the empty match at end of input
        lines.append((content, ending))
    return lines


def _number_line_indexes(lines: list[tuple[str, str]]) -> list[int]:
    indexes = []
    for i, (content, _) in enumerate(lines):
        if not _NUMBER_LINE_RE.match(content):
            continue
        if i + 1 >= len(lines) or not TIMESTAMP_RE.match(lines[i + 1][0].strip()):
            continue
        if i > 0 and lines[i - 1][0].strip():
            continue
        indexes.append(i)
    return indexes


def renumber_bytes(raw: bytes) -> bytes:
    """Return raw with cue numbers rewritten to 1..N. Raises SkipFile."""
    bom = UTF8_BOM if raw.startswith(UTF8_BOM) else b""
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise SkipFile("saved as UTF-16; only UTF-8 files are renumbered")
    try:
        text = raw[len(bom):].decode("utf-8")
    except UnicodeDecodeError:
        raise SkipFile("not valid UTF-8") from None

    lines = _split_lines(text)
    numbered = _number_line_indexes(lines)
    timestamps = sum(1 for content, _ in lines if TIMESTAMP_RE.match(content.strip()))
    if len(numbered) != timestamps:
        raise SkipFile(
            f"found {timestamps} timestamp lines but {len(numbered)} cue numbers; "
            "a cue is missing its number or the blank line before it"
        )

    for new_number, i in enumerate(numbered, start=1):
        content, ending = lines[i]
        lines[i] = (re.sub(r"\d+", str(new_number), content, count=1), ending)

    out = bom + "".join(content + ending for content, ending in lines).encode("utf-8")
    _verify(raw, out)
    return out


def _verify(before: bytes, after: bytes) -> None:
    """Belt and braces: prove the only lines that changed were cue numbers.

    Compares line by line on the raw bytes, independently of how
    renumber_bytes() found those lines, so a bug there can't slip a change
    to text, timing, or cue order into a file.
    """
    old = re.split(rb"\r\n|\r|\n", before)
    new = re.split(rb"\r\n|\r|\n", after)
    if len(old) != len(new):
        raise AssertionError("line count changed")
    for a, b in zip(old, new):
        if a == b:
            continue
        if not (re.fullmatch(rb"(\xef\xbb\xbf)?\s*\d+\s*", a) and re.fullmatch(rb"(\xef\xbb\xbf)?\s*\d+\s*", b)):
            raise AssertionError(f"a non-number line changed: {a!r} -> {b!r}")
        if re.sub(rb"\d+", b"", a) != re.sub(rb"\d+", b"", b):
            raise AssertionError(f"more than the digits changed: {a!r} -> {b!r}")


def _all_srt_paths() -> list[Path]:
    return sorted((REPO_ROOT / "Subtitles").rglob("*.srt"))


def _display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="renumber.py",
        description="Renumber .srt cues 1, 2, 3... in file order, changing nothing else.",
    )
    parser.add_argument("--write", action="store_true", help="Rewrite files (default: dry run).")
    parser.add_argument("--all", action="store_true", help="Every .srt file under Subtitles/.")
    parser.add_argument("paths", nargs="*", help="Paths to .srt files.")
    args = parser.parse_args(argv)
    # Paths and messages contain CJK text and emoji; a Windows console piped
    # to a file defaults to cp1252, which would crash on them.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")

    if args.all == bool(args.paths):
        parser.error("pass either --all or one or more paths")
    paths = _all_srt_paths() if args.all else [Path(p) for p in args.paths]

    changed: list[Path] = []
    skipped: list[tuple[Path, str]] = []
    for path in paths:
        raw = path.read_bytes()
        try:
            out = renumber_bytes(raw)
        except SkipFile as e:
            skipped.append((path, str(e)))
            continue
        if out == raw:
            continue
        changed.append(path)
        if args.write:
            path.write_bytes(out)

    verb = "Renumbered" if args.write else "Would renumber"
    print(f"{verb} {len(changed)} of {len(paths)} file(s).")
    for path in changed:
        print(f"  {_display(path)}")
    if skipped:
        print(f"\nSkipped {len(skipped)} file(s) that need a human to look at them:")
        for path, reason in skipped:
            print(f"  {_display(path)}")
            print(f"    {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
