# Maintainer guide

This is for the handful of people who review and merge pull requests. If you
just want to submit subtitles, see [`CONTRIBUTING.md`](../CONTRIBUTING.md)
instead.

## Why you need this

To make Github diffs much easier to review, we change cue numbers in an 
`.srt` file (the `1`, `2`, `3`... line above each timestamp) to the cue's 
start time in milliseconds. This way, inserting one cue changes one line of 
the diff instead of renumbering everything after it. (And yes, this file 
is still in valid SRT format)

Unfortunately, most subtitle editors will renumber every cue back to 
`1, 2, 3...`. So we need a maintainer to run a script to normalize the cue IDs
most of the time.

`normalize_pr.py` is the command we've created to fix this. It renumbers the 
PR's files back to the canonical form and pushes that to the contributor's branch, 
so the GitHub diff shows only what actually changed.

## One-time setup

You need **git**, the **GitHub CLI**, and **Python 3**.

**Windows** (in PowerShell):

```powershell
winget install --id Git.Git
winget install --id GitHub.cli
winget install --id Python.Python.3.12
```

**macOS** (needs [Homebrew](https://brew.sh)):

```sh
brew install git gh python
```

**Linux** (Debian/Ubuntu):

```sh
sudo apt install git python3
```

For `gh` on Linux, follow
[the official install instructions](https://github.com/cli/cli/blob/trunk/docs/install_linux.md).

Then sign in to GitHub once, and grab a copy of the repo:

```sh
gh auth login
git clone https://github.com/notHulK11/CantoCaptions.git
cd CantoCaptions
```

## Reviewing a pull request

From inside your `CantoCaptions` folder, with the PR's number:

```sh
git checkout main
git pull
python3 .github/scripts/normalize_pr.py 123
```

It will show you what it's about to change and ask for confirmation. Say `y`,
then refresh the PR on GitHub. The diff should now show only the
contributor's real changes. Review and merge as normal.

Add `--yes` to skip the confirmation prompt once you trust it.

## Committing your own subtitle work

When you've added or edited subtitles yourself, `publish.py` runs the checks,
commits, and pushes, all in one command:

```sh
git pull
python3 .github/scripts/publish.py -m "Add Ninja Hattori E8"
```

It finds the `.srt` files you've changed under `Subtitles/`, normalizes them,
refuses to commit anything that's actually broken, shows style warnings, then
commits just those files and pushes to `main`. It'll show you what it's about
to do and ask before pushing.

| Option | What it does |
| --- | --- |
| `--pr` | Open a pull request instead of pushing straight to `main` (needs `gh`). |
| `--yes` | Skip the confirmation prompt. |
| `--no-normalize` | Check only; don't rewrite anything. |

Files that aren't subtitles are deliberately left alone. If you also edited
`README.md`, commit that yourself. It'll tell you when it's leaving something
behind.

## Things it will tell you

**"you have uncommitted changes"**: you have edits of your own sitting in
the folder. Commit or stash them first; this stops your work from getting
mixed into someone else's PR.

**"could not be parsed and were left untouched"**: the file is broken in a
way that needs a human (overlapping timestamps, an empty subtitle, a cue that
ends before it starts). Ask the contributor to fix it; the automated check on
the PR will describe the problem too.

**"Could not push to the contributor's branch"**: either they unchecked
"Allow edits by maintainers" when opening the PR, or their fork belongs to a
GitHub organization, which GitHub doesn't allow maintainer edits on at all.
Ask them to re-open the PR with that box checked, or just review the noisy
diff as-is. Nothing is broken; it's only the diff that stays messy.

## What runs automatically

- **On every pull request** (and on direct pushes to `main`): the subtitle
  files are checked for encoding problems, timestamp problems, and
  style-guide issues. Results appear as annotations on the PR. This never
  modifies any file.
- **After anything merges to `main`**: subtitle formatting is normalized
  automatically and committed by `github-actions[bot]`. This means your local
  `main` will be one commit behind after a merge. Just `git pull` before
  starting anything new.
