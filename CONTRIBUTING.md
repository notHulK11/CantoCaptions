# Contributing to CantoCaptions

Thank you for wanting to help! This repo is a collection of `.srt` subtitle
files. You do **not** need Git, a fork, or anything installed on your
computer to contribute a fix or a new file. All you need is the subtitle file
itself and you can contribute!

## The easiest way: upload directly on GitHub

1. Browse to the folder for the show or movie you want to change (or create
   a new one) under [`Subtitles/`](Subtitles).
2. Click **Add file → Upload files** to add a new file, or open an existing
   file and click the pencil/edit icon to change it.
3. Drag in your `.srt` file, or make your edits directly in the browser.
4. Scroll down, write a sentence describing what you changed, and click
   **Propose changes** (or **Commit changes**).

GitHub automatically creates a fork, a branch, and a pull request for you. A
maintainer will review it from there.

## Standards and Conventions

If you want your changes to be accepted quickly, make sure your subtitles 
adhere to the CantoCaptions standards and conventions, which you can find in 
the [`README.md`](README.md). We know some of the conventions are tricky, 
especially when it comes to final particles, so if you're not sure, don't 
worry!  You can still submit, and we will have a maintainer review and edit 
your files.

How you can make it easy for us:

* Subtitles should be in SRT (`.srt`) format.
* Use traditional Chinese characters.
* Use Chinese punctuation (`，`, not `,` and `…`, not `...`)
* Don't add spaces unless subtitling English words.
* Time your subtitles carefully. Lines should start right before the audio 
  starts and end after the audio ends.
* If a character or word with variants isn't listed in the [`README`](README.md),
  use the variant found on the [words.hk dictionary](https://words.hk).

## What happens after you submit

A Pull Request will get created to track your changes. On the Pull Request, an 
automated check will run against your files and and will flag lines if 
something needs fixing (wrong file encoding, a line that's too long, etc.).

If you just added the file and didn't run any scripts, a maintainer will run 
a process to normalize the line numbers in the SRT file (see 
[`MAINTAINERS.md`](./github/MAINTAINERS.md) to know how that works). This allows 
us to view changes to the file more clearly on Github.

## If you use Git locally

If you are familiar with Git, feel free to use the Standard GitHub flow: fork,
branch, commit, open a pull request against `main`. Once you add the file, you
can run our subtitle tools on it yourself. This is entirely optional, but it
catches most problems before a maintainer ever looks at your work.

All you need is Python 3. There is nothing to install and no dependencies.
Run these from the top of your copy of the repo.

**Check for problems** that would be flagged on your pull request (wrong file
encoding, malformed timestamps, cues that are out of order):

```sh
python3 .github/scripts/srtfmt.py --check "Subtitles/Movies/Original/Your Movie (1990)/your-file.srt"
```

**See style suggestions** based on the conventions in the
[`README`](README.md), such as line lengths, subtitle durations, and
punctuation:

```sh
python3 .github/scripts/srtfmt.py --lint "Subtitles/Movies/Original/Your Movie (1990)/your-file.srt"
```

**Tidy the file up automatically**, fixing encoding, line endings, spacing,
and subtitle numbering:

```sh
python3 .github/scripts/srtfmt.py --write "Subtitles/Movies/Original/Your Movie (1990)/your-file.srt"
```

Running `--write` before you commit is the most useful of the three: it makes
the diff on your pull request show only the lines you actually changed, which
makes review much faster.

A few notes:

* `--check` and `--lint` only read your file. `--write` edits it in place, so
  commit first if you want to be able to compare.
* You can pass several files at once, or use your shell's `*` wildcard:
  `python3 .github/scripts/srtfmt.py --check Subtitles/Movies/Original/*/*.srt`
* Put quotes around any path containing spaces or Chinese characters.
* If a file is broken in a way the tools can't safely guess at, they'll tell
  you what's wrong and leave the file alone rather than mangling it.


### Or do it all in one command

If you'd rather not run the tools one at a time, `publish.py` does the whole
loop for you: it tidies up the subtitle files you've changed, checks them,
commits them, and opens the pull request.

```sh
python3 .github/scripts/publish.py -m "Add Ninja Hattori E8" --pr
```

**Always include `--pr`.** Without it, the script pushes straight to `main` --
which, in your own fork, means your own copy of `main`. Your work would sit
there and never reach us.

This is the one tool that needs something installed: the
[GitHub CLI](https://cli.github.com) (`gh`), signed in once with
`gh auth login`. That's what opens the pull request for you.

A few things it does on purpose:

* It only ever commits `.srt` files under `Subtitles/`. Anything else you
  changed is left for you to commit yourself, and it'll say so.
* It won't commit a file that's actually broken. It tells you what needs
  fixing instead.
* Style suggestions (line lengths, durations, punctuation) are shown but never
  block you.

The pull request gets filled in from your commit message, so it's worth
mentioning the show and episode there. You can always add more detail on the
pull request page afterwards.

## Questions?

Join our [Discord](https://discord.gg/ybVe9KmrsG). Most contributors hang
out there and would be happy to provide support.
