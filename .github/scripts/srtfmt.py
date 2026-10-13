"""Check and tidy .srt files: parse, number cues 1..N, normalize structure.

This module holds the parser and normalizer core (decode -> parse -> assign
IDs -> serialize) and a small CLI (--check/--write/--lint). The style-guide
rules live in srtlint.py.

--check is deliberately permissive: it fails only on problems that make a
file unreadable or wrong for every viewer (bad encoding, a broken timestamp,
an empty subtitle). Anything cosmetic or merely unconventional is either
ignored or left to srtlint's warnings.

Stdlib only, by design: this ships as a CI script, not a package.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import srtlint

TIMESTAMP_RE = re.compile(
    r"^(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})"
    r"\s*-->\s*"
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*$"
)
ID_LINE_RE = re.compile(r"^\d+$")


class SrtParseError(Exception):
    """Raised on a hard parse failure. Message is meant for a human, not a stack trace."""


@dataclass
class Cue:
    start_ms: int
    end_ms: int
    text: list[str] = field(default_factory=list)
    # Diagnostics-only metadata populated by parse(). Unused by assign_ids()
    # and serialize() -- they only need start_ms/end_ms/text -- but check_file()
    # needs the raw ID/timestamp text and line numbers to explain a diff.
    # number is the cue's 1-based position in the file, which is what subtitle
    # editors show against each block. Deliberately not id_text: a file's own
    # IDs may repeat, skip, or go backward, and the whole point is to give a
    # reviewer a number they can navigate to.
    id_line_no: int | None = None
    id_text: str | None = None
    number: int = 0
    timestamp_line_no: int = 0
    timestamp_text: str = ""
    blank_lines_before: int = 0
    text_line_nos: list[int] = field(default_factory=list)


def detect_encoding(raw: bytes) -> str:
    """Returns 'utf-16', 'utf-8-bom', or 'utf-8' based on a leading BOM."""
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return "utf-16"
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-bom"
    return "utf-8"


def decode_srt(raw: bytes) -> str:
    """Decode raw file bytes, tolerating the encodings real subtitle editors emit.

    Raises SrtParseError, not UnicodeDecodeError, on anything else (Big5, GBK
    and so on), so callers report it like any other broken file.
    """
    encoding = detect_encoding(raw)
    try:
        if encoding == "utf-16":
            text = raw.decode("utf-16")
        elif encoding == "utf-8-bom":
            text = raw[3:].decode("utf-8")
        else:
            text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise SrtParseError(
            "File is not saved as UTF-8 (it may be Big5 or GBK). "
            "Please re-save it as UTF-8."
        ) from None
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _to_ms(h: str, m: str, s: str, ms: str) -> int:
    return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1000 + int(ms)


def format_timestamp(total_ms: int) -> str:
    h, rem = divmod(total_ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse(text: str) -> list[Cue]:
    """Parse cue blocks from already-decoded, LF-normalized text.

    Tolerates non-sequential/duplicate/missing cue IDs, zero or multiple
    blank lines between cues, the timestamp quirks handled by the timestamp
    regex, and cues out of chronological order (legitimate SRT: overlapping
    on-screen text is often listed that way). Cue IDs are read only to be
    discarded; they are always renumbered 1..N in file order.

    Raises SrtParseError on: an unparseable timestamp line, a cue with no
    text, an end time before its start time, or a file with no cues at all.
    """
    lines = text.split("\n")
    n = len(lines)
    i = 0
    cues: list[Cue] = []

    def is_blank(idx: int) -> bool:
        return lines[idx].strip() == ""

    def looks_like_new_cue(idx: int) -> bool:
        """True if lines[idx] starts a new cue with no blank-line separator."""
        if idx >= n:
            return False
        stripped = lines[idx].strip()
        if TIMESTAMP_RE.match(stripped):
            return True
        return bool(
            ID_LINE_RE.match(stripped)
            and idx + 1 < n
            and TIMESTAMP_RE.match(lines[idx + 1].strip())
        )

    while i < n:
        blank_count = 0
        while i < n and is_blank(i):
            blank_count += 1
            i += 1
        if i >= n:
            break

        id_line_no: int | None = None
        id_text: str | None = None
        stripped = lines[i].strip()
        if ID_LINE_RE.match(stripped) and not TIMESTAMP_RE.match(stripped):
            id_line_no = i + 1
            id_text = stripped
            i += 1
            if i >= n:
                raise SrtParseError(
                    f"line {id_line_no}: cue ID with no following timestamp line"
                )

        timestamp_line_no = i + 1
        timestamp_text = lines[i].strip()
        m = TIMESTAMP_RE.match(timestamp_text)
        if not m:
            raise SrtParseError(
                f"line {i + 1}: unparseable timestamp line: {lines[i]!r}. "
                "Is there a blank line inside a subtitle, or a typo in the timestamp?"
            )
        start_ms = _to_ms(*m.groups()[0:4])
        end_ms = _to_ms(*m.groups()[4:8])
        if end_ms < start_ms:
            raise SrtParseError(
                f"line {i + 1}: end time {format_timestamp(end_ms)} is before "
                f"start time {format_timestamp(start_ms)}"
            )
        i += 1

        text_lines: list[str] = []
        text_line_nos: list[int] = []
        while i < n and not is_blank(i) and not looks_like_new_cue(i):
            text_lines.append(lines[i])
            text_line_nos.append(i + 1)
            i += 1

        if not text_lines:
            raise SrtParseError(
                f"line {timestamp_line_no}: cue has no text. "
                "Add its text, or delete the subtitle."
            )

        cues.append(
            Cue(
                start_ms,
                end_ms,
                text_lines,
                id_line_no=id_line_no,
                id_text=id_text,
                number=len(cues) + 1,
                timestamp_line_no=timestamp_line_no,
                timestamp_text=timestamp_text,
                blank_lines_before=blank_count,
                text_line_nos=text_line_nos,
            )
        )

    if not cues:
        raise SrtParseError("no cues found. The file is empty or isn't in SRT format.")

    return cues


def assign_ids(cues: list[Cue]) -> list[int]:
    """Number cues 1..N in file order -- what every subtitle editor writes.

    File order, never start time: reordering would break anything keyed to
    a cue's position, such as Subtitle Edit's .SE.bookmarks files.
    """
    return list(range(1, len(cues) + 1))


def serialize(cues: list[Cue], ids: list[int]) -> str:
    """Render cues to canonical .srt text: LF, one blank line between cues,
    no trailing whitespace, single trailing newline, no trailing blank cue."""
    blocks = []
    for cue_id, cue in zip(ids, cues):
        block_lines = [
            str(cue_id),
            f"{format_timestamp(cue.start_ms)} --> {format_timestamp(cue.end_ms)}",
        ]
        block_lines.extend(line.rstrip() for line in cue.text)
        blocks.append("\n".join(block_lines))
    return "\n\n".join(blocks) + "\n"


def normalize_text(text: str) -> str:
    """Full pipeline over already-decoded text: parse -> assign IDs -> serialize."""
    cues = parse(text)
    ids = assign_ids(cues)
    return serialize(cues, ids)


def normalize_bytes(raw: bytes) -> bytes:
    """Full pipeline from raw file bytes to canonical UTF-8 (no BOM) bytes."""
    return normalize_text(decode_srt(raw)).encode("utf-8")


def diagnose(raw: bytes, cues: list[Cue]) -> list[str]:
    """Explain, in human-readable terms, why a parseable file fails --check.

    Only encoding is checked here; parse() already rejects everything else
    that is actually broken. UTF-16 parses fine, but GitHub shows it as a
    binary file, so nobody can review changes to it.

    Everything else an editor might leave behind -- a UTF-8 BOM, CRLF line
    endings, trailing whitespace, extra blank lines, cue numbers that skip --
    is harmless to every real player and deliberately not reported.
    """
    if detect_encoding(raw) == "utf-16":
        return ["File is saved as UTF-16. Please re-save it as UTF-8."]
    return []


def check_file(raw: bytes) -> tuple[bool, list[str]]:
    """Check raw file bytes for problems serious enough to fail CI.

    Returns (passed, reasons). reasons is empty when passed; on a hard parse
    failure it holds a single human-readable error message.
    """
    try:
        cues = parse(decode_srt(raw))
    except SrtParseError as e:
        return False, [str(e)]

    reasons = diagnose(raw, cues)
    return not reasons, reasons


def write_file(raw: bytes) -> tuple[bytes, bool]:
    """Tidy raw file bytes fully: UTF-8, LF, one blank line between cues,
    no trailing whitespace, cues numbered 1..N.

    Returns (canonical_bytes, changed). Raises SrtParseError on a hard parse
    failure; a file that fails to parse cannot be rewritten. To renumber
    cues without touching anything else, use renumber.py instead.
    """
    canonical = normalize_bytes(raw)
    return canonical, canonical != raw


def _run_check(paths: list[str]) -> int:
    exit_code = 0
    for path_str in paths:
        raw = Path(path_str).read_bytes()
        ok, reasons = check_file(raw)
        if ok:
            continue
        exit_code = 1
        print(f"❌ {path_str}")
        for reason in reasons:
            print(f"  {reason}")
        print()
    return exit_code


def _run_write(paths: list[str]) -> int:
    exit_code = 0
    for path_str in paths:
        path = Path(path_str)
        raw = path.read_bytes()
        try:
            canonical, changed = write_file(raw)
        except SrtParseError as e:
            exit_code = 1
            print(f"❌ {path_str}: {e}")
            continue
        if changed:
            path.write_bytes(canonical)
            print(f"reformatted {path_str}")
    return exit_code


def _run_lint(paths: list[str]) -> int:
    for path_str in paths:
        raw = Path(path_str).read_bytes()
        try:
            cues = parse(decode_srt(raw))
        except SrtParseError as e:
            print(f"⚠️  {path_str}: skipped ({e})")
            print()
            continue
        warnings = srtlint.lint(cues)
        if not warnings:
            continue
        print(f"⚠️  {path_str}")
        for warning in warnings:
            print(f"  {warning}")
        print()
    return 0  # --lint is advisory only; it never fails the build.


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="srtfmt.py", description="Check and tidy .srt files under Subtitles/."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check", action="store_true", help="Exit 1 on any broken file; report why."
    )
    mode.add_argument("--write", action="store_true", help="Tidy files in place.")
    mode.add_argument(
        "--lint", action="store_true", help="Print style-guide warnings; never fails."
    )
    parser.add_argument("paths", nargs="+", help="Paths to .srt files.")
    args = parser.parse_args(argv)
    # Paths and messages contain CJK text and emoji; a Windows console piped
    # to a file defaults to cp1252, which would crash on them.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")

    if args.check:
        return _run_check(args.paths)
    if args.write:
        return _run_write(args.paths)
    return _run_lint(args.paths)


if __name__ == "__main__":
    sys.exit(main())
