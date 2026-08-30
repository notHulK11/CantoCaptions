"""CI glue for the srt-check workflow: list .srt files under Subtitles/ that
changed between two commits, NUL-separated, for ci_annotate.py to consume.

NUL-separated (via `git diff -z`), not newline-separated, because this
repo's filenames routinely contain spaces and non-ASCII characters that
git's ordinary --name-only output would otherwise quote/escape.

Usage: find_changed_srts.py <base-sha> <head-sha> <output-file>

Stdlib only.
"""

from __future__ import annotations

import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 3:
        print("usage: find_changed_srts.py <base-sha> <head-sha> <output-file>", file=sys.stderr)
        return 2
    base, head, output_file = argv

    result = subprocess.run(
        ["git", "diff", "-z", "--name-only", "--diff-filter=ACMR", base, head, "--", "Subtitles"],
        capture_output=True,
        check=True,
    )
    paths = [p for p in result.stdout.split(b"\0") if p.endswith(b".srt")]

    with open(output_file, "wb") as f:
        f.write(b"\0".join(paths))

    print(f"found {len(paths)} changed .srt file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
