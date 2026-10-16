---
title: Subtitle style guide
summary: Formatting, timing, punctuation, and what is left untranscribed.
order: 90
status: draft
---

# Subtitle style guide

<!-- Seeded 2026-10-15 from README.md. Review, then set status: published. -->

This section details how the subtitles should look. In general, Traditional characters are used as opposed to simplified characters, since they can always be converted to the latter with relative ease.

## General Guiding Principles

The goal of these subtitles is to be as useful to learners as possible. The goal is *NOT* to be as faithful to the literal utterances as spoken by the actors or voice actors. Put another way, we want to capture intended, correct speech, and not misspeaks or agrammatical speech. Furthermore, while the subtitles do aim at comprehensive coverage of what is said, grunts, yells, laughter, and miscellaneous expressive noises should in general be transcribed sparingly. Such subtitles, broadly speaking, don't contribute to building understanding of the language. To this end, it is recommended to transcribe most interjections only in so far as they form form part of a longer utterance (directly precedes or follows dialogue). Notable exceptions include 喂 which is always transcribed.

## Formatting
- .srt format
- single line max length is 17.5 characters

The .srt subtitle format is chosen because of its wide-ranging compatibility especially with language learning tools such as pop-up dictionaries.

## Timing
- lines should begin 0-50ms before speech.
- lines should slightly trail the end of speech (roughly 350ms) by default
	- exceptions: start of more speech or a shot change
- lines that end within roughly 50ms or less of a shot change should end right on the shot change
- lines that are trailing should end on a shot change if within 500ms of one
- lines with a length of 3 characters or more need a minimum duration of 750ms
	- exceptions: interrupted speech or a shot change (though generally allow at least 500ms)

## Punctuation

| Explanation                                                                                                                                                 | Examples                                |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| Written or background info is enclosed in Chinese parentheses.                                                                                              | （三年前）                                   |
| The titles (of works, shows, movies, etc.) are enclosed in Chinese double arrow brackets.                                                                        | 《進擊的巨人》                                 |
| Secondary titles are separated with a Chinese colon.                                                                                                        | 《哈利波特：神秘的魔法石》                           |
| Episode titles are enclosed in Chinese square brackets.                                                                                                        | ［那一天：西甘希娜淪陷2］                           |
| Miscellaneous titles, such as in on-screen text are enclosed with lenticular brackets.                                                                      | 【Subtopic】                             |
| Foreign speech is prefaced with the name of the language in Cantonese inside lenticular brackets, followed by a Cantonese translation. Mandarin and English do not count as foreign speech, so they do not need to be tagged.                                                                      | 【日語】有冇搞錯？                             |
| When written text is read out loud, enclose the text in Chinese quote brackets.                                   | 上面刻住「非戰不屈」                        |
| A Chinese comma is placed after all SFP, except when followed by 你 without a pause.                                                                         | ❌ 好啦我明喇。<br>✅ 好啦，我明喇<br>❌ 好春廢啊，你<br>✅ 好春廢啊你 |
| Multiple speaker dialogue uses two lines and dialogue that begins with a hyphen without a following space.                                                  | -speaker 1<br>-speaker 2                |
| When a question is followed by the name of who is being addressed, then the addressee should be enclosed by the question mark. | ❌ 你點啊？阿明<br>✅ 呢點啊，阿明？               |
| When a 定係 question is split across multiple subtitle lines, add a question mark to both. Otherwise, use a single question mark. | 你今日想食日本嘢吖？<br>定係想食茶餐廳啊？ <br><br> 你今日想食日本嘢吖，定係想食茶餐廳啊？      |
| Only 1 Chinese ellipsis character is used, never 2.                                                                    | ❌ ……<br>✅ …                               |
| Repetition of a one-character word once should be transcribed fully. If repeated more than once, use a trailing Chinese ellipsis character.                 | ✅ 喂喂            |
| Repetition of a two-character once can either be abbreviated with a Chinese ellipsis or not depending on the speed and length of the subtitle line. Faster pacing and tighter line-length constraints favor usage of an ellipsis.      | ✅ 係啊，係啊<br>✅ 係啊…             |
| Quick repetition of any word more than 2 times a trailing Chinese ellipsis character.                                                     | ❌ 喂喂喂<br>✅ 喂…             |
| Adjectives can be repeated.                                                              | ✅ 好多好多陪                  |
| In the case of interrupted speech, a Chinese ellipsis character is used to mark where the speaker is cut off and a new line begins with the new speech.     | -點解你…<br>-唔知啊                           |
| In the case of trailing speech, a Chinese ellipsis character is used.                                                                                      | ❌佢唔可以嘅話~~<br>✅佢唔可以嘅話…                   |
| In the case of stammering, the start is separated by a Chinese ellipsis, but this is only done once.                                                        | ❌ 只只不過<br>❌ 只…只…只不過<br>✅ 只…只不過             |
| When listing with 同 or 同埋, Chinese list comma is used on the elements that are not connected with the conjunction.                                          | A、B、C同埋D                                |
| Subtitles never end in a period and Chinese period is never used.                                                                                           | ❌ 我個名叫Tom。<br>✅ 我個名叫Tom                   |
| The middle period is never used.                                                                                                                            | ❌ 哈利·波特<br>✅ 哈利波特                         |
| Italics are never used.                                                                                                                                     |                                         |
| English follows typical English casing rules. English words are capitalized at the start of a line but otherwise lowercased.       |      ✅你幾時開完meeting啊？<br>✅Meeting幾時開？                                   |

## Untranscribed Speech
In general, these subtitles are a learning resource. The goal is not to transcribe verbatim all utterances in their entirety. The goal is have a complete subtitle that contains information useful to the learner. We do not want to include very minor, incidental speech/sounds, or unintentionally incorrect speech. Sentence Final Particles are transcribed as accurately as possible to benefit the learner.

| Speech                                                  | Example                                    |
| ---------------------------------------------- | ------------------------------------------ |
| Background dialogue does not have to be subtitled. If subtitled and overlapping with main speech, use {\an8} tag to put speech on top                                        |    ✅`{\an8}`吓？你做咩啊？                          |
| The sound of hesitation, e.g. "uh" (a6 / e6), is only transcribed when drawn out and precedes a longer utterance. When directly following a word, it should not be transcribed and an ellipsis should be used instead. | ✅ 誒…你係邊個啊？<br>❌你誒…係邊個啊？<br>✅ 你…係邊個啊？<br>❌ 佢…誒…佢係…誒…我唔知<br>✅佢…佢係…我唔知 |
| The Chinese exclamation point is used sparingly. For example, for exceptionally loud/declarative yells or for emphasis among quieter speech, such as when calling someone's name. Even if a character is yelling, it's discouraged to end every line with an exclamation point.                 |                                            |
| Miscellaneous grunts, yells, screams, and the like are not transcribed.                                                                                                                                                                                                                         |                                            |
| Ah, oh, hmm, huh, mhmm and other acknowledgement noises are transcribed sparingly and primarily in the case that they form part of other utterances.                                                                                                                                            | ❌ 吓？<br>✅ 吓？你講咩啊？                            |
