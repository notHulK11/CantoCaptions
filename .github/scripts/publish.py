#!/usr/bin/env python3
"""Run the subtitle checks, commit, and push (or open a PR) in one command.

For anyone working in a local clone -- maintainers pushing to main, and
contributors opening a pull request with --pr. Handles the whole loop:

  1. finds the .srt files you've changed under Subtitles/
  2. normalizes them (encoding, line endings, spacing, cue numbering)
  3. blocks on anything a human has to fix, and shows style warnings
  4. commits just those files
  5. pushes to main, or opens a pull request with --pr

Usage:
    python3 .github/scripts/publish.py -m "Add Ninja Hattori E8"
    python3 .github/scripts/publish.py -m "Fix timing" --pr
    python3 .github/scripts/publish.py -m "..." --yes        # no confirmation
    python3 .github/scripts/publish.py -m "..." --no-normalize

Only --pr needs the GitHub CLI (`gh`); everything else is git + Python 3.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

import srtlint
from srtfmt import SrtParseError, check_file, decode_srt, parse, write_file

REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_SHOWN = 10


def _git(*args: str, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=capture, text=True, check=check
    )


def changed_srt_paths(status_output: str) -> list[str]:
    """Parse `git status --porcelain -z` output into .srt paths under Subtitles/.

    NUL-separated so this repo's spaces and Chinese characters survive intact;
    git would otherwise quote and escape them.
    """
    entries = status_output.split("\0")
    paths: list[str] = []
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4:
            continue
        status, path = entry[:2], entry[3:]
        # A rename or copy is followed by its source path as a separate field.
        if status[0] in ("R", "C"):
            i += 1
        if path.startswith("Subtitles/") and path.endswith(".srt"):
            paths.append(path)
    return paths


def _show(items: list[str], indent: str = "  ") -> None:
    for item in items[:MAX_SHOWN]:
        print(f"{indent}{item}")
    if len(items) > MAX_SHOWN:
        print(f"{indent}... and {len(items) - MAX_SHOWN} more")


def _explain_push_failure(stderr: str, branch: str) -> int:
    """Say why the server refused the push, and what to do about it.

    The three causes need three different answers, and guessing wrong wastes
    the user's time: no write access and a protected branch are both fixed by
    opening a pull request, while a stale branch is fixed by pulling. Only the
    last one is helped by `git pull --rebase`.
    """
    lower = stderr.lower()
    denied = (
        ("permission" in lower and "denied" in lower)
        or "403" in lower
        or "write access" in lower
    )
    protected = "protected branch" in lower or "gh006" in lower
    stale = (
        "non-fast-forward" in lower
        or "fetch first" in lower
        or "updates were rejected" in lower
    )

    if denied or protected:
        # The commit is fine, it just can't go to this branch. Roll it back so
        # the edits are staged again and a --pr run can pick them straight up.
        undo = _git("reset", "--soft", "HEAD~1", capture=True, check=False)
        print()
        if protected and not denied:
            print(f"`{branch}` is a protected branch, so it cannot be pushed to directly.")
        else:
            print(f"You do not have permission to push to `{branch}` on this repository.")
        print()
        if undo.returncode == 0:
            print("Nothing was pushed, and the commit has been rolled back, so your")
            print("edits are exactly as they were. Open a pull request instead:")
            print()
            print('    python3 .github/scripts/publish.py -m "your message" --pr')
        else:
            print("Nothing was pushed. Your commit is still here locally.")
        print()
        print("If you believe you should have write access, ask a maintainer.")
        return 1

    print()
    print("Committed locally, but the server rejected the push.")
    if stale:
        print(f"`{branch}` moved on without you, most likely the normalize bot")
        print("committing after your last pull. Run:")
        print()
        print("    git pull --rebase && git push")
    elif stderr.strip():
        print("git reported:")
        print()
        for line in stderr.strip().splitlines():
            print(f"  {line}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="publish.py",
        description="Check, commit, and push subtitle changes in one step.",
    )
    parser.add_argument("-m", "--message", help="Commit message.")
    parser.add_argument(
        "--pr", action="store_true", help="Open a pull request instead of pushing to main."
    )
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Check only; don't rewrite files. Use before the repo-wide migration.",
    )
    args = parser.parse_args(argv)

    if args.pr and shutil.which("gh") is None:
        print("error: --pr needs the GitHub CLI (`gh`), which isn't installed.")
        print("Install it from https://cli.github.com, then run `gh auth login`.")
        print("Or drop --pr to commit and push directly.")
        return 2

    status = _git(
        "status", "--porcelain", "-z", "--untracked-files=all", capture=True
    ).stdout
    paths = [p for p in changed_srt_paths(status) if (REPO_ROOT / p).exists()]

    if not paths:
        print("No changed subtitle files under Subtitles/. Nothing to do.")
        return 0

    print(f"{len(paths)} changed subtitle file(s):")
    _show(paths)

    # 1. Normalize.
    reformatted: list[str] = []
    if not args.no_normalize:
        for rel in paths:
            path = REPO_ROOT / rel
            try:
                canonical, did_change = write_file(path.read_bytes())
            except SrtParseError:
                continue  # reported as a blocking problem below
            if did_change:
                path.write_bytes(canonical)
                reformatted.append(rel)
        if reformatted:
            print()
            print(f"Normalized {len(reformatted)} file(s):")
            _show(reformatted)

    # 2. Block on anything a human has to fix.
    blocking: list[tuple[str, list[str]]] = []
    warnings: list[str] = []
    for rel in paths:
        raw = (REPO_ROOT / rel).read_bytes()
        ok, reasons = check_file(raw)
        if not ok:
            blocking.append((rel, reasons))
            continue
        try:
            cues = parse(decode_srt(raw))
        except SrtParseError:
            continue
        warnings.extend(f"{rel}: {w}" for w in srtlint.lint(cues))

    if blocking:
        print()
        print(f"{len(blocking)} file(s) have problems that need fixing:")
        for rel, reasons in blocking:
            print(f"  {rel}")
            _show(reasons, indent="    ")
        print()
        print("Nothing has been committed. Fix these and run again.")
        return 1

    if warnings:
        print()
        print(f"{len(warnings)} style warning(s). These don't block anything:")
        _show(warnings)

    # 3. Confirm.
    message = args.message
    if not message:
        message = input("\nCommit message: ").strip()
        if not message:
            print("Aborted: empty commit message.")
            return 1

    destination = "a new pull request" if args.pr else "main"
    print()
    print(f"About to commit {len(paths)} file(s) and push to {destination}.")
    other = len([e for e in status.split("\0") if e]) - len(paths)
    if other > 0:
        print(f"({other} other changed file(s) will be left uncommitted.)")

    if not args.yes:
        if input("Continue? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Aborted. Your files keep any normalization already applied.")
            return 1

    # 4. Commit and publish.
    original_branch = _git("rev-parse", "--abbrev-ref", "HEAD", capture=True).stdout.strip()
    if args.pr:
        branch = f"srt-{int(time.time())}"
        _git("checkout", "-b", branch, capture=True)

    _git("add", "--", *paths)
    _git("commit", "-m", message, capture=True)

    if args.pr:
        push = _git("push", "-u", "origin", branch, capture=True, check=False)
        if push.returncode != 0:
            print("\nCould not push the branch:")
            print(push.stderr.strip())
            return 1
        subprocess.run(
            ["gh", "pr", "create", "--fill"], cwd=REPO_ROOT, check=False
        )
        _git("checkout", original_branch, capture=True)
        print(f"\nDone. (Returned you to `{original_branch}`.)")
        return 0

    push = _git("push", capture=True, check=False)
    if push.returncode != 0:
        return _explain_push_failure(push.stderr, original_branch)

    print("\nDone. Pushed to main.")
    print("The normalize bot may add a follow-up commit; `git pull` before your next edit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
