# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An Obsidian vault that is a biblical studies database — a work in progress. The goal is a complete, interlinked Greek (LXX/GNT) and Hebrew Bible where every verse, word, and lexicon entry is a navigable note. Content is created both manually in Obsidian and via external scripts.

## Directory structure and data model

```
Bible/          Verse notes — the "study layer" that embeds source texts
Greek/          Source texts and lexicon (LXX for OT, GNT for NT)
Hebrew/         Source texts and lexicon (OT only; Lexicon planned, not yet built)
templates/      Templater JS templates
Home.md         Dashboard (DataviewJS + Hebcal API)
```

### Bible/ (verse notes)

Path: `Bible/{Book}/{Chapter}/{Book}-{Chapter}-{Verse}.md`  
Example: `Bible/1 Chronicles/1/1 Chronicles-1-1.md`

YAML frontmatter keys: `title`, `book`, `chapter`, `verse`, `section`

Body embeds the Greek and Hebrew source files and has stub sections:
```
![[/Greek/{Book}/{Chapter}/{Book}-{Chapter}-{Verse}G.md]]
![[/Hebrew/{Book}/{Chapter}/{Book}-{Chapter}-{Verse}H.md]]

## Analysis
#### Words
#### Phrases
#### Concepts

## Reflections
```

### Greek/ (source + lexicon)

**Verse files** — Path: `Greek/{Book}/{NNN}/{Book}-{NNN}-{NNN}G.md`  
Chapters and verses are zero-padded to 3 digits (e.g., `001`, `023`).

YAML frontmatter:
```yaml
language: greek
book: Genesis
chapter: 1
verse: 1
tokens:
  - form: "ἀρχῇ"     # surface form as it appears in text
    lemma: "ΑΡΧΗ"    # ALL-CAPS Greek, matches Lexicon filename
    morph: DSF        # morphology code, links to Greek/Morphology/{CODE}
```

Body: HTML `<span class="tok">` elements with Obsidian wikilinks to Lexicon and Morphology entries.

**Lexicon/** — One file per lemma, named in ALL-CAPS Greek: `Greek/Lexicon/{LEMMA}.md`  
YAML frontmatter: `pos`, `language`, `strongs`, `gloss` (list), `lexicon` (display forms), `perfected-date`, `gender`, `number-of-verses`, etc.  
Body includes GNT/LXX occurrence lists, definition, and cross-references.

**Strongs/** — Numbered index files (e.g., `0000.md`, `1700.md`) mapping Strong's numbers to Lexicon entries. These are reference lists, not per-word entries.

### Hebrew/ (source texts; Lexicon planned)

**Verse files** — Path: `Hebrew/{Book}/{NNN}/{Book}-{NNN}-{NNN}H.md`  
Same zero-padded chapter/verse numbering as Greek.

YAML frontmatter:
```yaml
language: hebrew
book: Genesis
chapter: 1
verse: 1
tokens:
  - form: רֵאשִׁית     # surface form
    lemma: רֵאשִׁית    # root/lemma (Hebrew script)
    morph: FSA          # morphology code
    affixes: ב          # optional; prefixed particles (ב, הַ, וְ, etc.)
```

Hebrew Lexicon and Morphology folders will mirror the Greek structure when built. Links in Hebrew verse bodies already reference `Hebrew/Lexicon/{lemma}` and `Hebrew/Morphology/{code}` in anticipation.

## Internal link conventions

All wikilinks use vault-absolute paths (leading `/`):
- Greek lexicon: `[[/Greek/Lexicon/ΑΡΧΗ|ἀρχῇ]]`
- Greek morphology: `[[/Greek/Morphology/DSF|ˑ]]`
- Hebrew lexicon: `[[Hebrew/Lexicon/רֵאשִׁית|רֵאשִׁית]]`
- Bible verse embed: `![[/Greek/Genesis/001/Genesis-001-001G.md]]`

The `ˑ` (middle dot, U+02C0) is used as the link display text for morphology markers — it renders as a superscript dot in Obsidian CSS.

## Naming quirks to watch

- **Bible/** uses unpadded chapter/verse numbers in filenames (`1 Chronicles-1-1.md`) but **Greek/** and **Hebrew/** use 3-digit zero-padded numbers (`Genesis-001-001G.md`).
- Greek lemmas in YAML and filenames are **ALL-CAPS Greek** (e.g., `ΠΟΙΕΩ`, not `ποιέω`). Hebrew lemmas use normal Hebrew script.
- The `Greek/` directory covers both LXX (OT) and GNT (NT), plus Josephus's *War of the Jews*.
- `Greek/Strongs/` contains Strong's index chunks, not individual word entries; the actual lexicon entries live in `Greek/Lexicon/`.

## Obsidian plugins in use

- **Dataview / DataviewJS** — powers the `Home.md` dashboard and any computed queries
- **Templater** — `templates/season-core.tpl.md` is a JS template computing the current liturgical season (Advent / Christmas / Epiphany / Easter); import it with `<%* tR += await tp.file.include(...) %>` then call `SEASON.seasonLabel(date)`
- **Obsidian Git** — vault is version-controlled; commits are made from inside Obsidian
- **Homepage** — sets `Home.md` as the startup note
- **Meta Bind** — used for inline input controls in notes

## Templates

`templates/season-core.tpl.md` exports a single object `SEASON` with one method:
- `SEASON.seasonLabel(date?)` → `"Advent" | "Christmas" | "Epiphany" | "Easter"` (where "Easter" covers both Lent and Eastertide; "Epiphany" covers both the season after Epiphany and ordinary time after Pentecost)

`Home.md` uses raw DataviewJS (not Templater) to hit `https://www.hebcal.com/leyning?cfg=json&date={iso}` and display today's Torah portion.
