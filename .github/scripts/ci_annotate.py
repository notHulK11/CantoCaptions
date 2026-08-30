"""CI glue for the srt-check workflow: run --check and --lint over a set of
files and emit GitHub Actions workflow commands (::error / ::warning) so
results show up as inline PR annotations -- readable by a contributor who
has never used git, per docs/srt-canonicalization-spec.md Component 2.

Kept separate from srtfmt.py's own CLI, which prints plain text for a
maintainer running it locally. Calls check_file()/lint() directly rather
than parsing that CLI's stdout, since the annotation format needs the
file/line/message split as structured data, not text to re-parse.

Usage: ci_annotate.py --paths-file <file>
  <file> holds NUL-separated paths (see the workflow: `git diff -z
  --name-only`). NUL-separated, not newline-separated, because this repo's
  filenames routinely contain spaces and non-ASCII characters that git's
  ordinary --name-only output would otherwise quote/escape.

Stdlib only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import srtlint
from srtfmt import SrtParseError, check_file, decode_srt, parse

# Messages carry their location as either "Cue 12 (line 47)" or, for problems
# between cues, a bare "Line 47". The line is pulled out to anchor the
# annotation; the cue number stays in the visible text, since that is what a
# reviewer needs to find the cue in a subtitle editor.
_LOCATION_RE = re.compile(r"^(?:Cue (\d+) \(line (\d+)\)|Line (\d+)) — (.*)$")


def _read_paths(paths_file: str) -> list[str]:
    data = Path(paths_file).read_bytes()
    return [p.decode("utf-8") for p in data.split(b"\0") if p]


def _emit(command: str, path: str, message: str, line: int = 1) -> None:
    # GitHub workflow-command values must have %, \r, \n percent-escaped.
    escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::{command} file={path},line={line}::{escaped}")


def _emit_reasons(command: str, path: str, reasons: list[str]) -> None:
    for reason in reasons:
        m = _LOCATION_RE.match(reason)
        if not m:
            _emit(command, path, reason)
            continue
        cue_number, cue_line, bare_line, message = m.groups()
        if cue_number:
            message = f"Cue {cue_number} — {message}"
        _emit(command, path, message, line=int(cue_line or bare_line))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "--paths-file":
        print("usage: ci_annotate.py --paths-file <file>", file=sys.stderr)
        return 2

    paths = _read_paths(argv[1])
    exit_code = 0
    for path_str in paths:
        raw = Path(path_str).read_bytes()

        ok, reasons = check_file(raw)
        if not ok:
            exit_code = 1
            _emit_reasons("error", path_str, reasons)

        try:
            cues = parse(decode_srt(raw))
        except SrtParseError:
            continue  # already reported as a --check error above

        _emit_reasons("warning", path_str, srtlint.lint(cues))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
