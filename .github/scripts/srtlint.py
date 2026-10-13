"""Style-guide warnings for .srt files.

These are warnings, not merge blockers -- the README notes conventions are
still evolving and much of the existing corpus predates them. Kept as a
separate module from srtfmt.py so the rule set can grow without touching the
parser. No runtime dependency on srtfmt -- see the TYPE_CHECKING import
below -- so srtfmt.py can import this module without a circular import.

Stdlib only.
"""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from srtfmt import Cue

MAX_LINE_WIDTH = 17.5
MIN_DURATION_MS = 400
MIN_DURATION_LONG_MS = 750
LONG_TEXT_CHAR_THRESHOLD = 3

_MARKUP_RE = re.compile(r"\{\\[^}]*\}|</?[a-zA-Z][^>]*>")
_ITALIC_TAG_RE = re.compile(r"</?i>|\{\\i[01]?\}", re.IGNORECASE)
_STANDARD_TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$")


class LintWarning(NamedTuple):
    """One style-guide warning. rule is a short title shared by every warning
    of the same kind, so callers can group them."""

    rule: str
    cue_number: int | None
    lineno: int
    message: str

    def __str__(self) -> str:
        return f"{location(self.cue_number, self.lineno)} — {self.message}"


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


def _lint_line_length(cue: Cue) -> list[LintWarning]:
    warnings = []
    for line, lineno in zip(cue.text, cue.text_line_nos):
        width = _display_width(_visible_text(line))
        if width > MAX_LINE_WIDTH:
            warnings.append(
                LintWarning(
                    "Line too long",
                    cue.number,
                    lineno,
                    f"this line is {_fmt_width(width)} characters. The limit is {MAX_LINE_WIDTH}.",
                )
            )
    return warnings


def _lint_duration(cue: Cue) -> list[LintWarning]:
    duration = cue.end_ms - cue.start_ms
    char_count = sum(len(_visible_text(line)) for line in cue.text)
    threshold = MIN_DURATION_LONG_MS if char_count >= LONG_TEXT_CHAR_THRESHOLD else MIN_DURATION_MS
    if duration < threshold:
        return [
            LintWarning(
                "Subtitle too short",
                cue.number,
                cue.timestamp_line_no,
                f"cue lasts {duration}ms. Minimum is {threshold}ms.",
            )
        ]
    return []


def _lint_ending_punctuation(cue: Cue) -> list[LintWarning]:
    if not cue.text:
        return []
    last_line = _visible_text(cue.text[-1]).rstrip()
    if last_line and last_line[-1] in "。.":
        return [
            LintWarning(
                "Ends in a period",
                cue.number,
                cue.text_line_nos[-1],
                f"subtitle ends in '{last_line[-1]}'. Subtitles should not end in a period.",
            )
        ]
    return []


def _lint_double_ellipsis(cue: Cue) -> list[LintWarning]:
    return [
        LintWarning(
            "Double ellipsis",
            cue.number,
            lineno,
            "uses '……' where a single '…' is required.",
        )
        for line, lineno in zip(cue.text, cue.text_line_nos)
        if "……" in line
    ]


def _lint_middle_dot(cue: Cue) -> list[LintWarning]:
    return [
        LintWarning(
            "Middle dot",
            cue.number,
            lineno,
            "contains a middle dot '·', which is never used.",
        )
        for line, lineno in zip(cue.text, cue.text_line_nos)
        if "·" in line
    ]


def _lint_italics(cue: Cue) -> list[LintWarning]:
    return [
        LintWarning(
            "Italics",
            cue.number,
            lineno,
            "contains an italic tag; italics are never used.",
        )
        for line, lineno in zip(cue.text, cue.text_line_nos)
        if _ITALIC_TAG_RE.search(line)
    ]


def _lint_timestamp_format(cue: Cue) -> list[LintWarning]:
    # Every common player reads '.' separators, unpadded hours and odd
    # spacing around '-->', so these are worth tidying but never blocking.
    # srtfmt.py --write fixes all of them.
    if not cue.timestamp_text or _STANDARD_TIMESTAMP_RE.match(cue.timestamp_text):
        return []
    return [
        LintWarning(
            "Nonstandard timestamp",
            cue.number,
            cue.timestamp_line_no,
            f"timestamp '{cue.timestamp_text}' isn't in the standard "
            "'00:00:00,000 --> 00:00:00,000' form.",
        )
    ]


def _lint_out_of_order(prev: Cue, cue: Cue) -> list[LintWarning]:
    # Often deliberate (overlapping on-screen text listed after the dialogue
    # it overlaps), so a warning, not an error. Worth a look because it can
    # also mean a cue was pasted in the wrong place.
    if cue.start_ms >= prev.start_ms:
        return []
    return [
        LintWarning(
            "Out of order",
            cue.number,
            cue.timestamp_line_no,
            f"starts before cue {prev.number}, which comes before it in the file. "
            "Fine if the overlap is intentional.",
        )
    ]


def lint_items(cues: list[Cue]) -> list[LintWarning]:
    """Run every style-guide rule over the given cues, in file order.

    Warnings, not errors -- callers should never fail a build on these."""
    warnings: list[LintWarning] = []
    for idx, cue in enumerate(cues):
        if idx > 0:
            warnings.extend(_lint_out_of_order(cues[idx - 1], cue))
        warnings.extend(_lint_timestamp_format(cue))
        warnings.extend(_lint_line_length(cue))
        warnings.extend(_lint_duration(cue))
        warnings.extend(_lint_ending_punctuation(cue))
        warnings.extend(_lint_double_ellipsis(cue))
        warnings.extend(_lint_middle_dot(cue))
        warnings.extend(_lint_italics(cue))
    return warnings


def lint(cues: list[Cue]) -> list[str]:
    """lint_items(), formatted as 'Cue 12 (line 47) — message' strings."""
    return [str(w) for w in lint_items(cues)]
