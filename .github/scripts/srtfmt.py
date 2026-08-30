"""Canonicalize .srt files: derive cue IDs from start time, normalize structure.

See docs/srt-canonicalization-spec.md for the full design. This module holds
the parser and normalizer core (decode -> parse -> assign IDs -> serialize).
The CLI (--check/--write/--lint) and the style-lint rule set are separate,
later pieces of the same component.

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
    id_line_no: int | None = None
    id_text: str | None = None
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


def _decode_bytes(raw: bytes) -> str:
    """Decode to text without touching line endings (used by decode_srt and diagnose)."""
    encoding = detect_encoding(raw)
    if encoding == "utf-16":
        return raw.decode("utf-16")
    if encoding == "utf-8-bom":
        return raw[3:].decode("utf-8")
    return raw.decode("utf-8")


def decode_srt(raw: bytes) -> str:
    """Decode raw file bytes, tolerating the encodings real subtitle editors emit."""
    text = _decode_bytes(raw)
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
    blank lines between cues, and the timestamp quirks handled by the
    timestamp regex. Cue IDs are read only to be discarded -- canonical IDs
    are always recomputed from start time.

    Raises SrtParseError on: an unparseable timestamp line, a cue with no
    text, an end time before its start time, or cues out of chronological
    order.
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
            raise SrtParseError(f"line {i + 1}: unparseable timestamp line: {lines[i]!r}")
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
            raise SrtParseError(f"line {timestamp_line_no}: cue has no text")

        cues.append(
            Cue(
                start_ms,
                end_ms,
                text_lines,
                id_line_no=id_line_no,
                id_text=id_text,
                timestamp_line_no=timestamp_line_no,
                timestamp_text=timestamp_text,
                blank_lines_before=blank_count,
                text_line_nos=text_line_nos,
            )
        )

    if not cues:
        raise SrtParseError("no cues found")

    for prev, cur in zip(cues, cues[1:]):
        if cur.start_ms < prev.start_ms:
            raise SrtParseError(
                "cues out of chronological order: cue starting at "
                f"{format_timestamp(cur.start_ms)} follows cue starting at "
                f"{format_timestamp(prev.start_ms)}"
            )

    return cues


def assign_ids(cues: list[Cue]) -> list[int]:
    """Derive canonical cue IDs from start time (see collision rule in the spec).

    Cues are processed in file order (== ascending start time, enforced by
    parse()). ID 0 is never used -- a cue starting at 00:00:00,000 is
    promoted to 1. Any other collision increments by 1 until free.
    """
    used: set[int] = set()
    ids = []
    for cue in cues:
        candidate = cue.start_ms if cue.start_ms != 0 else 1
        while candidate in used:
            candidate += 1
        used.add(candidate)
        ids.append(candidate)
    return ids


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


def _diagnose_timestamp_line(cue: Cue) -> list[str]:
    expected = f"{format_timestamp(cue.start_ms)} --> {format_timestamp(cue.end_ms)}"
    if cue.timestamp_text == expected:
        return []

    reasons = []
    m = TIMESTAMP_RE.match(cue.timestamp_text)
    if m:
        h1, _, _, _, h2, _, _, _ = m.groups()
        if len(h1) < 2 or len(h2) < 2:
            reasons.append(f"Line {cue.timestamp_line_no} — hour is not zero-padded.")
        if "." in cue.timestamp_text:
            reasons.append(
                f"Line {cue.timestamp_line_no} — uses '.' instead of ',' "
                "as the millisecond separator."
            )
        if not re.search(r"[,.]\d{3} --> \d", cue.timestamp_text):
            reasons.append(
                f"Line {cue.timestamp_line_no} — should have exactly one space "
                "on each side of '-->'."
            )
    if not reasons:
        reasons.append(
            f"Line {cue.timestamp_line_no} — timestamp formatting differs from canonical form."
        )
    return reasons


def _diagnose_id_order(cues: list[Cue]) -> list[str]:
    """Flag cue IDs that go backward or repeat -- never IDs that merely
    aren't start-time-derived.

    Cue ID canonicalization is deliberately NOT a --check failure: any
    subtitle editor renumbers cues sequentially on save, so a contributor who
    fixes one line of dialogue and saves will hand back a file with plain
    1..N IDs through no fault of their own. That's mechanical and lossless --
    the normalize-on-main job silently rewrites IDs to their canonical,
    start-time-derived form on every merge, so there is nothing here for a
    human to act on.

    What *is* worth flagging: an ID that is not greater than the previous
    cue's ID. A well-behaved renumbering (by a tool, or left untouched)
    always increases; a repeat or a drop usually means two cues were
    swapped, duplicated, or otherwise mis-edited by hand.
    """
    reasons = []
    prev_value: int | None = None
    prev_line: int | None = None
    for cue in cues:
        if cue.id_text is None or not cue.id_text.isdigit():
            continue
        value = int(cue.id_text)
        if prev_value is not None and value <= prev_value:
            reasons.append(
                f"Line {cue.id_line_no} — cue ID is {value}, which is not greater "
                f"than the previous cue's ID ({prev_value}, line {prev_line}). Cue "
                "numbers get renumbered automatically, but one that repeats or goes "
                "backward usually means two cues got swapped or duplicated by mistake."
            )
        prev_value = value
        prev_line = cue.id_line_no
    return reasons


def diagnose(raw: bytes, cues: list[Cue]) -> list[str]:
    """Explain, in human-readable terms, why a file fails --check.

    Cue ID canonicalization and end-of-file newline conventions are
    intentionally excluded (see _diagnose_id_order for IDs). A missing
    trailing newline or an extra trailing blank line has no effect on
    parsing in any real player, and which one a file has is largely an
    artifact of whatever editor last saved it -- not something a contributor
    did wrong. Both are silently corrected by --write on merge to main.
    Everything else here is something a human contributor needs to act on.
    """
    reasons: list[str] = []

    encoding = detect_encoding(raw)
    if encoding == "utf-16":
        reasons.append("File is saved as UTF-16. Please re-save as UTF-8 without a BOM.")
    elif encoding == "utf-8-bom":
        reasons.append(
            "File is saved as UTF-8 with a BOM. Please re-save as UTF-8 without a BOM."
        )

    pre_lf_text = _decode_bytes(raw)
    if "\r" in pre_lf_text:
        reasons.append("File uses CRLF or CR line endings. Line endings should be LF only.")

    text = pre_lf_text.replace("\r\n", "\n").replace("\r", "\n")

    for lineno, line in enumerate(text.split("\n"), start=1):
        if line != line.rstrip():
            reasons.append(f"Line {lineno} — has trailing whitespace.")

    reasons.extend(_diagnose_id_order(cues))

    for idx, cue in enumerate(cues):
        reasons.extend(_diagnose_timestamp_line(cue))

        if idx > 0 and cue.blank_lines_before != 1:
            reasons.append(
                f"Line {cue.timestamp_line_no} — {cue.blank_lines_before} blank line(s) "
                "before this cue; canonical form uses exactly 1."
            )

    return reasons


def check_file(raw: bytes) -> tuple[bool, list[str]]:
    """Check raw file bytes against everything --check enforces.

    This is deliberately looser than byte-equality with normalize_bytes():
    cue ID canonicalization is --write's job, not --check's (see
    _diagnose_id_order). Returns (passed, reasons). reasons is empty when
    passed; on a hard parse failure it holds a single human-readable error
    message.
    """
    try:
        cues = parse(decode_srt(raw))
    except SrtParseError as e:
        return False, [str(e)]

    reasons = diagnose(raw, cues)
    return not reasons, reasons


def write_file(raw: bytes) -> tuple[bytes, bool]:
    """Canonicalize raw file bytes fully, including cue IDs.

    Returns (canonical_bytes, changed). Unlike check_file(), this has no
    concept of "close enough" -- --write always produces the fully canonical
    form, including start-time-derived IDs. Raises SrtParseError on a hard
    parse failure; a file that fails to parse cannot be rewritten.
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
        prog="srtfmt.py", description="Canonicalize .srt files under Subtitles/."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check", action="store_true", help="Exit 1 on any non-canonical file; report why."
    )
    mode.add_argument("--write", action="store_true", help="Rewrite files in place.")
    mode.add_argument(
        "--lint", action="store_true", help="Print style-guide warnings; never fails."
    )
    parser.add_argument("paths", nargs="+", help="Paths to .srt files.")
    args = parser.parse_args(argv)

    if args.check:
        return _run_check(args.paths)
    if args.write:
        return _run_write(args.paths)
    return _run_lint(args.paths)


if __name__ == "__main__":
    sys.exit(main())
