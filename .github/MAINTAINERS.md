# Maintainer guide

This is for the handful of people who review and merge pull requests. If you
just want to submit subtitles, see [`CONTRIBUTING.md`](../CONTRIBUTING.md)
instead.

## Cue numbering

Cues in an `.srt` file are numbered `1, 2, 3...` in file order, the same way
every subtitle editor saves them. Nothing renumbers files automatically.

(For a while, cue numbers were set to each cue's start time in milliseconds.
That was rolled back with [`renumber.py`](scripts/renumber.py), which changes
only the number lines and nothing else, so cue order and Subtitle Edit
bookmarks are unaffected.)

If you ever need to renumber a file by hand without touching anything else:

```sh
python3 .github/scripts/renumber.py "Subtitles/path/to/file.srt"          # dry run
python3 .github/scripts/renumber.py --write "Subtitles/path/to/file.srt"
```

## One-time setup

You need **git** and **Python 3**. The **GitHub CLI** is only needed for
`publish.py --pr`.

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

## Committing your own subtitle work

When you've added or edited subtitles yourself, `publish.py` runs the checks,
commits, and pushes, all in one command:

```sh
git pull
python3 .github/scripts/publish.py -m "Add Ninja Hattori E8"
```

It finds the `.srt` files you've changed under `Subtitles/`, tidies them,
refuses to commit anything that's actually broken, shows style warnings, then
commits just those files and pushes to `main`. It'll show you what it's about
to do and ask before pushing.

| Option | What it does |
| --- | --- |
| `--pr` | Open a pull request instead of pushing straight to `main` (needs `gh`). |
| `--yes` | Skip the confirmation prompt. |
| `--no-normalize` | Check only; don't tidy or renumber anything. |

Files that aren't subtitles are deliberately left alone. If you also edited
`README.md`, commit that yourself. It'll tell you when it's leaving something
behind.

Using `publish.py` is optional. Committing with plain git, or uploading on
GitHub, works just as well.

## What runs automatically

**On every pull request, and on pushes to `main`**, the `.srt` files that
changed are checked. Nothing is ever modified or committed by this check.

- **Errors** fail the check (and send the usual GitHub failure email). They're
  reserved for files that are actually broken:
  - not saved as UTF-8 (or saved as UTF-16, which GitHub can't diff)
  - a timestamp line that can't be read, often from a stray blank line
    inside a subtitle
  - an empty subtitle
  - a subtitle that ends before it starts
  - a file with no subtitles in it at all
- **Warnings** never fail anything. They appear as annotations on the PR and
  on the run's summary page, grouped so each kind of issue shows up once per
  file:
  - line too long, subtitle too short, ending in a period, `……`, `·`, italics
    (from the style guide in the [README](../README.md))
  - a cue that starts before the one above it (often intentional, for
    overlapping on-screen text)
  - a nonstandard timestamp such as `00:00:01.000`

Everything else (a UTF-8 BOM, Windows line endings, trailing spaces, extra
blank lines, cue numbers that skip or repeat) is harmless to every player and
isn't reported at all.
