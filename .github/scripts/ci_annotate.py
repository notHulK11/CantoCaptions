"""CI glue for the srt-check workflow: check a set of .srt files and emit
GitHub Actions workflow commands (::error / ::warning) so results show up as
inline annotations -- readable by a contributor who has never used git.

Built to be quiet. Only problems that make a file broken for every viewer
are errors and fail the check (see srtfmt.check_file). Style-guide issues
are warnings that never fail anything, and are grouped to one annotation per
rule per file -- a 1,000-cue upload with 40 long lines gets one "Line too
long" warning saying so, not 40. The full breakdown goes to the run's job
summary page instead of the annotation list.

Kept separate from srtfmt.py's own CLI, which prints plain text for someone
running it locally. Calls check_file()/lint_items() directly rather than
parsing that CLI's stdout, since annotations need structured data.

Usage: ci_annotate.py --paths-file <file>
  <file> holds NUL-separated paths (see the workflow: `git diff -z
  --name-only`). NUL-separated, not newline-separated, because this repo's
  filenames routinely contain spaces and non-ASCII characters that git's
  ordinary --name-only output would otherwise quote/escape.

Stdlib only.
"""

from __future__ import annotations

import os
import re
import sys
import traceback
from pathlib import Path

import srtlint
from srtfmt import SrtParseError, check_file, decode_srt, parse

MAX_CUES_LISTED = 5
MAX_SUMMARY_ROWS = 200

# Parse errors start with "line N: ". Pull the line out to anchor the
# annotation on it; the rest of the message stands on its own.
_LINE_PREFIX_RE = re.compile(r"^line (\d+): (.*)$", re.DOTALL)


def _read_paths(paths_file: str) -> list[str]:
    data = Path(paths_file).read_bytes()
    return [p.decode("utf-8") for p in data.split(b"\0") if p]


def _escape_data(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(value: str) -> str:
    # Properties are comma-separated key=value pairs ending at '::', so a
    # filename containing ',' or ':' would otherwise be cut short.
    return _escape_data(value).replace(":", "%3A").replace(",", "%2C")


def _emit(command: str, path: str, message: str, line: int = 1, title: str | None = None) -> None:
    props = f"file={_escape_property(path)},line={line}"
    if title:
        props += f",title={_escape_property(title)}"
    print(f"::{command} {props}::{_escape_data(message)}")


def _emit_error(path: str, reason: str) -> None:
    m = _LINE_PREFIX_RE.match(reason)
    if m:
        _emit("error", path, m.group(2), line=int(m.group(1)), title="Broken subtitle file")
    else:
        _emit("error", path, reason, title="Broken subtitle file")


def _group_by_rule(items: list[srtlint.LintWarning]) -> dict[str, list[srtlint.LintWarning]]:
    groups: dict[str, list[srtlint.LintWarning]] = {}
    for item in items:
        groups.setdefault(item.rule, []).append(item)
    return groups


def _emit_warnings(path: str, items: list[srtlint.LintWarning]) -> None:
    for rule, group in _group_by_rule(items).items():
        first = group[0]
        message = f"Cue {first.cue_number} — {first.message}"
        if len(group) > 1:
            others = [str(w.cue_number) for w in group[1 : 1 + MAX_CUES_LISTED]]
            more = ", …" if len(group) - 1 > MAX_CUES_LISTED else ""
            message += f" ({len(group) - 1} more like this in this file: cues {', '.join(others)}{more})"
        _emit("warning", path, message, line=first.lineno, title=rule)


def _write_summary(rows: list[tuple[str, list[str], list[srtlint.LintWarning]]], checked: int) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    out = ["### Subtitle check", ""]
    if not rows:
        out.append(f"All {checked} changed subtitle file(s) look good.")
    else:
        out.append(
            "Errors mean the file is broken and needs fixing. Warnings are "
            "style-guide suggestions from the README and never block anything."
        )
        out += ["", "| File | Errors | Warnings |", "| --- | --- | --- |"]
        for path, errors, warnings in rows[:MAX_SUMMARY_ROWS]:
            name = path.replace("|", "\\|")
            error_text = "<br>".join(e.replace("|", "\\|") for e in errors) or "—"
            counts = ", ".join(f"{rule} ×{len(g)}" for rule, g in _group_by_rule(warnings).items())
            out.append(f"| {name} | {error_text} | {counts or '—'} |")
        if len(rows) > MAX_SUMMARY_ROWS:
            out.append(f"\n…and {len(rows) - MAX_SUMMARY_ROWS} more file(s).")
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def _check_one(path: str) -> tuple[list[str], list[srtlint.LintWarning]]:
    raw = Path(path).read_bytes()
    ok, errors = check_file(raw)
    try:
        cues = parse(decode_srt(raw))
    except SrtParseError:
        return errors, []  # already reported as an error
    return errors, srtlint.lint_items(cues)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "--paths-file":
        print("usage: ci_annotate.py --paths-file <file>", file=sys.stderr)
        return 2

    paths = _read_paths(argv[1])
    rows: list[tuple[str, list[str], list[srtlint.LintWarning]]] = []
    exit_code = 0
    for path in paths:
        try:
            errors, warnings = _check_one(path)
        except Exception:
            # A bug in this checker is not the contributor's problem, so it
            # must not fail their check -- say so and move on.
            traceback.print_exc()
            _emit(
                "warning",
                path,
                "This file could not be checked because of a bug in the checker. "
                "The details are in the job log.",
                title="Check skipped",
            )
            continue

        if not errors and not warnings:
            continue
        rows.append((path, errors, warnings))
        print(f"{path}: {len(errors)} error(s), {len(warnings)} style warning(s)")
        for reason in errors:
            _emit_error(path, reason)
        _emit_warnings(path, warnings)
        if errors:
            exit_code = 1

    _write_summary(rows, len(paths))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
