# CantoCaptions standards

These pages are the CantoCaptions standard for written Cantonese subtitles, and its single
source. Everything else is generated from them by
[cantocaptions-standards](../../cantocaptions-standards):
- the proofreading linter;
- the dataset's standardization score;
- the pipeline's text cleaning;
- the standards text the proofreading agents read.

To change a convention, change the page. Never edit a generated copy.

## Pages

| page | covers |
|---|---|
| [overview](overview.md) | why CantoCaptions has its own conventions, and what they started from |
| [particles](particles.md) | which character for each particle syllable and tone, and what each means |
| [compound-particles](compound-particles.md) | stacked particles |
| [interjections](interjections.md) | interjections |
| [affixes](affixes.md) | 阿, 親, 地, 下, 晒… |
| [pronouns](pronouns.md) | pronoun characters |
| [character-variants](character-variants.md) | the 1:1 Hong Kong character variants |
| [required-conventions](required-conventions.md) | required spellings beyond the 1:1 variants |
| [style-guide](style-guide.md) | formatting, timing, punctuation, untranscribed speech |
| [optional-characters](optional-characters.md) | recommended but optional characters |

## Writing a page

Start from [`_template.md`](_template.md). The tools read these pages, so keep them to plain
Markdown:

- **Front matter:** `title`, `summary` (one line; the agent's index shows it), `order` (where
  the page sits in the list) and `status`. `draft` pages are under review; `published` pages
  are the standard.
- **Headings:** one `# Title`, then `##` / `###` sections. Each heading's link anchor is how a
  rule cites its section, so keep headings unique within a page. Renaming a heading is fine:
  extraction picks up the change.
- **Tables** for anything with one row per form. A row such as
  `| ✅ selected | ❌ others | jyutping | explanation |` becomes a rule on its own. Separate
  several avoided forms with `、`.
- **Examples:** mark lines `✅` (correct) or `❌` (wrong), in a table cell or a list. Every
  generated tool is tested against them: a ✅ line must pass, a ❌ line must be caught.
- **Exceptions:** when an avoided form is right inside some word (打攪 keeps 攪), say so on the
  page with the word written out. Only exceptions written on a page reach the tools.
- **HTML:** only `<br>` (a line break inside a table cell) and `<!-- comments -->` (notes for
  reviewers, which are dropped from every copy). `ccstd check` refuses anything else.
- **Readings** in Jyutping (`ji1 go3`), wherever the right form depends on the sound.

After editing a page, run `uv run ccstd check` in cantocaptions-standards. Then run the
extraction (its README describes the steps).
