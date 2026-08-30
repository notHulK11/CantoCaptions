#!/usr/bin/env python3
"""Normalize a pull request's .srt files so GitHub's native diff stays readable.

Why this exists
---------------
Most subtitle editors renumber every cue on save. Once `main` is canonical
(start-time-derived cue IDs), a contributor who opens a file, fixes one line
of dialogue and saves hands back a file whose *every* cue ID differs from
main -- so GitHub renders a one-word typo fix as a whole-file diff.

GitHub's web diff cannot be customized to hide that: .gitattributes diff
drivers and textconv only affect diffs computed locally by git, never the
web UI. The only way to get a readable diff in the PR is to make the
branch's bytes canonical before review, which is what this does.

A GitHub Actions bot cannot do this job: the built-in GITHUB_TOKEN is scoped
to this repository and has no authority to push to a contributor's fork. A
maintainer can, using their own credentials, because fork PRs default to
"Allow edits by maintainers".

Usage
-----
    python3 .github/scripts/normalize_pr.py <pr-number> [--yes]

Requires git, the GitHub CLI (`gh`, authenticated once via `gh auth login`),
and Python 3. See .github/MAINTAINERS.md for setup.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from srtfmt import SrtParseError, write_file

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMIT_MESSAGE = "Normalize subtitle formatting"


def _git(*args: str, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=capture, text=True, check=check
    )


def _gh(*args: str, capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["gh", *args], cwd=REPO_ROOT, capture_output=capture, text=True, check=check
    )


def _missing_tool() -> str | None:
    for tool in ("git", "gh"):
        if shutil.which(tool) is None:
            return tool
    return None


def _worktree_is_dirty() -> bool:
    return bool(_git("status", "--porcelain", capture=True).stdout.strip())


def _pr_srt_files(pr: str) -> list[str]:
    """Changed .srt paths under Subtitles/, read from the API so this works
    before (and independently of) checking the branch out."""
    raw = _gh("pr", "view", pr, "--json", "files").stdout
    files = json.loads(raw).get("files", [])
    return [
        f["path"]
        for f in files
        if f["path"].startswith("Subtitles/") and f["path"].endswith(".srt")
    ]


def normalize_paths(paths: list[str], root: Path) -> tuple[list[str], list[tuple[str, str]]]:
    """Rewrite each path to canonical form. Returns (changed, failed).

    Paths deleted by the PR are skipped. A file that fails to parse is
    reported rather than guessed at -- the contributor has to fix those.
    """
    changed: list[str] = []
    failed: list[tuple[str, str]] = []
    for rel in paths:
        path = root / rel
        if not path.exists():
            continue
        raw = path.read_bytes()
        try:
            canonical, did_change = write_file(raw)
        except SrtParseError as e:
            failed.append((rel, str(e)))
            continue
        if did_change:
            path.write_bytes(canonical)
            changed.append(rel)
    return changed, failed


def _explain_push_failure(stderr: str) -> None:
    print()
    print("Could not push to the contributor's branch.")
    print()
    print("The usual causes:")
    print("  - The contributor unchecked 'Allow edits by maintainers' on the PR.")
    print("  - The fork is owned by an organization; GitHub does not permit")
    print("    maintainer edits on those, regardless of that checkbox.")
    print()
    print("Ask them to re-open the PR with that box checked, or just review the")
    print("noisy diff as-is. Your local changes have been left in place on the")
    print("PR branch in case you want to inspect them.")
    if stderr.strip():
        print()
        print("git said:")
        for line in stderr.strip().splitlines():
            print(f"  {line}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="normalize_pr.py",
        description="Normalize a PR's .srt files so GitHub's diff is readable.",
    )
    parser.add_argument("pr", help="Pull request number, e.g. 123")
    parser.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt before pushing."
    )
    args = parser.parse_args(argv)

    missing = _missing_tool()
    if missing:
        print(f"error: `{missing}` is not installed, or not on your PATH.")
        print("See .github/MAINTAINERS.md for setup instructions.")
        return 2

    if _worktree_is_dirty():
        print("error: you have uncommitted changes in this repository.")
        print("Commit or stash them first, so this script doesn't mix them into the PR.")
        return 2

    original_branch = _git("rev-parse", "--abbrev-ref", "HEAD", capture=True).stdout.strip()

    print(f"Looking up PR #{args.pr}...")
    try:
        paths = _pr_srt_files(args.pr)
    except subprocess.CalledProcessError as e:
        print(f"error: could not read PR #{args.pr}.")
        if e.stderr:
            print(e.stderr.strip())
        return 2

    if not paths:
        print("This PR doesn't change any .srt files under Subtitles/. Nothing to do.")
        return 0

    print(f"{len(paths)} subtitle file(s) changed in this PR.")
    print(f"Checking out PR #{args.pr}...")
    _gh("pr", "checkout", args.pr, capture=False)

    changed, failed = normalize_paths(paths, REPO_ROOT)

    if failed:
        print()
        print("These files could not be parsed and were left untouched.")
        print("The contributor needs to fix them:")
        for rel, reason in failed:
            print(f"  {rel}")
            print(f"    {reason}")

    if not changed:
        print()
        print("Every subtitle file in this PR is already canonical. Nothing to normalize.")
        _git("checkout", original_branch, capture=True)
        return 1 if failed else 0

    print()
    print(f"{len(changed)} file(s) would be reformatted:")
    for rel in changed:
        print(f"  {rel}")

    if not args.yes:
        print()
        answer = input("Commit and push this to the contributor's branch? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted. Reverting local changes.")
            _git("checkout", "--", *changed)
            _git("checkout", original_branch, capture=True)
            return 1

    _git("add", "--", *changed)
    _git("commit", "-m", COMMIT_MESSAGE, capture=True)

    push = _git("push", capture=True, check=False)
    if push.returncode != 0:
        _explain_push_failure(push.stderr)
        return 1

    print()
    print("Pushed. Refresh the PR on GitHub. The diff should now show only")
    print("the contributor's actual changes.")
    _git("checkout", original_branch, capture=True)
    print(f"(Returned you to `{original_branch}`.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
