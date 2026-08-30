"""Style-guide warnings for canonical .srt files (Component 3 of
docs/srt-canonicalization-spec.md).

These are warnings, not merge blockers -- the README notes conventions are
still evolving and much of the existing corpus predates them. Kept as a
separate module from srtfmt.py so the rule set can grow without touching the
normalizer. No runtime dependency on srtfmt -- see the TYPE_CHECKING import
below -- so srtfmt.py can import this module without a circular import.

Stdlib only.
"""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from srtfmt import Cue

MAX_LINE_WIDTH = 17.5
MIN_DURATION_MS = 400
MIN_DURATION_LONG_MS = 750
LONG_TEXT_CHAR_THRESHOLD = 3

_MARKUP_RE = re.compile(r"\{\\[^}]*\}|</?[a-zA-Z][^>]*>")
_ITALIC_TAG_RE = re.compile(r"</?i>|\{\\i[01]?\}", re.IGNORECASE)


def location(cue_number: int | None, lineno: int) -> str:
    """Format the "where" half of a message, as 'Cue 12 (line 47)'.

    Cue numbers are what a subtitle editor shows against each block, so they
    are how someone reviewing in one actually navigates. The line number stays
    alongside because CI anchors its inline annotations by line, and because
    anyone opening the file in a text editor still needs it. Problems that sit
    between cues have no cue number and fall back to the line alone.
    """
    if cue_number is None:
        return f"Line {lineno}"
    return f"Cue {cue_number} (line {lineno})"


def _visible_text(line: str) -> str:
    """Strip override tags ({\\an8}, <i>...) that aren't displayed text."""
    return _MARKUP_RE.sub("", line)


def _display_width(text: str) -> float:
    """Full-width (CJK) characters count as 1, half-width as 0.5 -- matching
    the style guide's fractional 17.5-character line limit."""
    return sum(
        1.0 if unicodedata.east_asian_width(ch) in ("W", "F") else 0.5 for ch in text
    )


def _fmt_width(width: float) -> str:
    return f"{width:g}"


def _lint_line_length(cue: Cue) -> list[str]:
    warnings = []
    for line, lineno in zip(cue.text, cue.text_line_nos):
        width = _display_width(_visible_text(line))
        if width > MAX_LINE_WIDTH:
            warnings.append(
                f"{location(cue.number, lineno)} — this line is "
                f"{_fmt_width(width)} characters. The limit is {MAX_LINE_WIDTH}."
            )
    return warnings


def _lint_duration(cue: Cue) -> list[str]:
    duration = cue.end_ms - cue.start_ms
    char_count = sum(len(_visible_text(line)) for line in cue.text)
    threshold = MIN_DURATION_LONG_MS if char_count >= LONG_TEXT_CHAR_THRESHOLD else MIN_DURATION_MS
    if duration < threshold:
        return [
            f"{location(cue.number, cue.timestamp_line_no)} — cue lasts "
            f"{duration}ms. Minimum is {threshold}ms."
        ]
    return []


def _lint_ending_punctuation(cue: Cue) -> list[str]:
    if not cue.text:
        return []
    last_line = _visible_text(cue.text[-1]).rstrip()
    if last_line and last_line[-1] in "。.":
        return [
            f"{location(cue.number, cue.text_line_nos[-1])} — subtitle ends in "
            f"'{last_line[-1]}'. Subtitles should not end in a period."
        ]
    return []


def _lint_double_ellipsis(cue: Cue) -> list[str]:
    return [
        f"{location(cue.number, lineno)} — uses '……' where a single '…' is required."
        for line, lineno in zip(cue.text, cue.text_line_nos)
        if "……" in line
    ]


def _lint_middle_dot(cue: Cue) -> list[str]:
    return [
        f"{location(cue.number, lineno)} — contains a middle dot '·', which is never used."
        for line, lineno in zip(cue.text, cue.text_line_nos)
        if "·" in line
    ]


def _lint_italics(cue: Cue) -> list[str]:
    return [
        f"{location(cue.number, lineno)} — contains an italic tag; italics are never used."
        for line, lineno in zip(cue.text, cue.text_line_nos)
        if _ITALIC_TAG_RE.search(line)
    ]


def lint(cues: list[Cue]) -> list[str]:
    """Run every style-guide rule over the given cues and return warnings.

    Warnings, not errors -- callers should never fail a build on these."""
    warnings: list[str] = []
    for cue in cues:
        warnings.extend(_lint_line_length(cue))
        warnings.extend(_lint_duration(cue))
        warnings.extend(_lint_ending_punctuation(cue))
        warnings.extend(_lint_double_ellipsis(cue))
        warnings.extend(_lint_middle_dot(cue))
        warnings.extend(_lint_italics(cue))
    return warnings
