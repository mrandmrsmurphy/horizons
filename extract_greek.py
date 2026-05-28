#!/usr/bin/env python3
"""
extract_greek.py  —  MediaWiki XML → Obsidian vault

Reads Greek.xml from the vault root and writes markdown files.
All modes skip existing files.

Usage:
    python3 extract_greek.py --morphology
    python3 extract_greek.py --verses
    python3 extract_greek.py --lexicon
    python3 extract_greek.py --all
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

VAULT   = Path(__file__).parent
XML_PATH = VAULT / "Greek.xml"
MW_NS   = "{http://www.mediawiki.org/xml/export-0.6/}"


# ─── XML iteration ────────────────────────────────────────────────────────────

def iter_pages(path):
    """Yield (title, wikitext) for every <page>, one at a time (low memory)."""
    for _, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != f"{MW_NS}page":
            continue
        title_el = elem.find(f"{MW_NS}title")
        rev      = elem.find(f".//{MW_NS}revision")
        text_el  = rev.find(f"{MW_NS}text") if rev is not None else None
        title = (title_el.text or "") if title_el is not None else ""
        text  = (text_el.text  or "") if text_el  is not None else ""
        yield title, text
        elem.clear()


# ─── Page classification ──────────────────────────────────────────────────────

VERSE_RE   = re.compile(r"^Greek:(.+)/(\d+)/(\d+)$")
CHAPTER_RE = re.compile(r"^Greek:(.+)/(\d+)$")

def _has_greek(s):
    return any("Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿" for c in s)

def classify(title):
    """
    Returns one of:
        ('verse',      book, chapter, verse)
        ('chapter',    book, chapter)          — always skipped
        ('morphology', code)
        ('lexicon',    lemma)
        None — not a Greek-namespace content page
    """
    if not title.startswith("Greek:"):
        return None
    local = title[6:]

    m = VERSE_RE.match(title)
    if m:
        return ("verse", m.group(1), m.group(2), m.group(3))

    m = CHAPTER_RE.match(title)
    if m:
        # Pure ASCII-uppercase/digit book part → morph code with an embedded slash
        # (e.g. "Greek:PAP/NSM" matches CHAPTER_RE with book="PAP", ch="NSM" but
        # "NSM" fails \d+ so this branch never fires for real chapter pages)
        if re.fullmatch(r"[A-Z0-9]+", m.group(1)):
            return ("morphology", local)
        return ("chapter", m.group(1), m.group(2))

    # No slash or slash inside an all-ASCII-uppercase code like PAP/NSM
    if re.fullmatch(r"[A-Z0-9/]+", local):
        return ("morphology", local)

    if _has_greek(local):
        return ("lexicon", local)

    return None


# ─── Template helpers ─────────────────────────────────────────────────────────

def parse_infobox(text, template_name):
    """Return {lowercase_key: value_str} for the first {{template_name ...}} found."""
    pat = r"\{\{" + re.escape(template_name) + r"(.*?)\}\}"
    m = re.search(pat, text, re.DOTALL)
    if not m:
        return {}
    params = {}
    for part in re.split(r"(?m)^\|", m.group(1)):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            params[k.strip().lower()] = v.strip()
    return params


PG_RE = re.compile(r"\{\{PG\|([^|{}]+)\|([^|{}]+)(?:\|([^|{}]+))?\}\}")

def parse_pg_tokens(text):
    """Return list of {lemma, form, morph} dicts from {{PG|...}} calls."""
    return [
        {
            "lemma": m.group(1).strip(),
            "form":  m.group(2).strip(),
            "morph": (m.group(3) or "").strip(),
        }
        for m in PG_RE.finditer(text)
    ]


# ─── Wiki → Markdown ──────────────────────────────────────────────────────────

def wiki_to_md(text):
    """Minimal conversion of MediaWiki markup to Markdown."""
    # HTML entities
    text = (text.replace("&lt;", "<").replace("&gt;", ">")
                .replace("&amp;", "&").replace("&quot;", '"'))
    # Remove comments and <poem>
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"</?poem\b[^>]*>", "", text)
    # Headers: deepest first to avoid partial matches
    for n in (5, 4, 3, 2):
        eq, hdr = "=" * n, "#" * n
        text = re.sub(rf"{eq}\s*(.+?)\s*{eq}", rf"{hdr} \1", text)
    # Links: [[target|label]] → label, [[target]] → target
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Bold / italic
    text = re.sub(r"'{3}(.+?)'{3}", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"'{2}(.+?)'{2}", r"*\1*",   text, flags=re.DOTALL)
    # List items (line-by-line; must come after header conversion)
    out = []
    for line in text.splitlines():
        if re.match(r"^#{2,}", line):   # already a ## header
            out.append(line)
        elif line.startswith("# ") or line == "#":
            out.append("1. " + line[2:])
        elif line.startswith("** "):
            out.append("  - " + line[3:])
        elif line.startswith("* "):
            out.append("- " + line[2:])
        else:
            out.append(line)
    return "\n".join(out).strip()


# ─── Verse files ──────────────────────────────────────────────────────────────

_MORPH_CHAR = "ˑ"  # ˑ  MODIFIER LETTER HALF TRIANGULAR COLON — morph marker

def _safe_morph(morph):
    """Replace / in compound morph codes (e.g. PAP/NSM → PAP_NSM) for filenames."""
    return morph.replace("/", "_")

def _token_span(tok):
    lemma, form, morph = tok["lemma"], tok["form"], tok["morph"]
    if morph:
        mid = _safe_morph(morph)
        return (
            f'<span class="tok" title="{lemma} — {morph}">'
            f"[[/Greek/Lexicon/{lemma}|{form}]]"
            f"[[/Greek/Morphology/{mid}|{_MORPH_CHAR}]]</span>"
        )
    return (
        f'<span class="tok" title="{lemma}">'
        f"[[/Greek/Lexicon/{lemma}|{form}]]</span>"
    )

def write_verse(book, chapter, verse, text, stats):
    ch3 = chapter.zfill(3)
    v3  = verse.zfill(3)
    out = VAULT / "Greek" / book / ch3 / f"{book}-{ch3}-{v3}G.md"
    if out.exists():
        stats["skipped"] += 1
        return
    tokens = parse_pg_tokens(text)
    if not tokens:
        stats["empty"] += 1
        return

    yaml_lines = [
        "---",
        "language: greek",
        f"book: {book}",
        f"chapter: {int(chapter)}",
        f"verse: {int(verse)}",
        "tokens:",
    ]
    for tok in tokens:
        yaml_lines.append(f'  - form: "{tok["form"]}"')
        yaml_lines.append(f'    lemma: "{tok["lemma"]}"')
        if tok["morph"]:
            yaml_lines.append(f'    morph: {tok["morph"]}')
        else:
            yaml_lines.append( '    morph: ""')
    yaml_lines.append("---")

    body = " ".join(_token_span(t) for t in tokens)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(yaml_lines) + "\n" + body + "\n", encoding="utf-8")
    stats["created"] += 1


# ─── Morphology files ─────────────────────────────────────────────────────────

_MORPH_FIELDS = ("person", "number", "tense", "mood", "voice", "case", "gender", "degree")

def write_morphology(code, text, stats):
    safe = _safe_morph(code)
    out  = VAULT / "Greek" / "Morphology" / f"{safe}.md"
    if out.exists():
        stats["skipped"] += 1
        return
    params = parse_infobox(text, "Infobox Parsing")
    if not params:
        stats["skipped"] += 1
        return

    lines = ["---", f"code: {code}", "language: greek"]
    for field in _MORPH_FIELDS:
        if field in params:
            lines.append(f"{field}: {params[field]}")
    lines.append("---")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    stats["created"] += 1


# ─── Lexicon files ────────────────────────────────────────────────────────────

_LEXICON_MAP = {          # XML infobox key → YAML key
    "pos":     "pos",
    "strongs": "strongs",
    "common":  "gloss",   # split into list
    "lexicon": "lexicon", # inline list
    "hebrew":  "hebrew",
    "latin":   "latin",
    "root":    "root",
    "gender":  "gender",
}

def write_lexicon(lemma, text, stats):
    out = VAULT / "Greek" / "Lexicon" / f"{lemma}.md"
    if out.exists():
        stats["skipped"] += 1
        return

    params    = parse_infobox(text, "Infobox Greek Word")
    body_wiki = re.sub(r"\{\{Infobox Greek Word.*?\}\}", "", text,
                       flags=re.DOTALL).strip()
    body_md   = wiki_to_md(body_wiki)

    lines = ["---", "language: Greek"]
    for xml_key, yaml_key in _LEXICON_MAP.items():
        val = params.get(xml_key, "").strip().rstrip(",").strip()
        if not val:
            continue
        if yaml_key == "gloss":
            items = [g.strip() for g in val.split(",") if g.strip()]
            lines.append("gloss:")
            lines.extend(f"  - {item}" for item in items)
        elif yaml_key == "lexicon":
            items = [x.strip() for x in val.split(",") if x.strip()]
            lines.append(f"lexicon: [{', '.join(items)}]")
        else:
            lines.append(f"{yaml_key}: {val}")
    lines.append("---")

    out.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines) + "\n"
    if body_md:
        content += "\n" + body_md + "\n"
    out.write_text(content, encoding="utf-8")
    stats["created"] += 1


# ─── Runner ───────────────────────────────────────────────────────────────────

def run(modes):
    stats = {m: {"created": 0, "skipped": 0, "empty": 0}
             for m in ("morphology", "verses", "lexicon")}
    total = 0

    for title, text in iter_pages(XML_PATH):
        total += 1
        if total % 5000 == 0:
            print(f"  ... {total:,} pages", flush=True)

        kind = classify(title)
        if kind is None or kind[0] == "chapter":
            continue

        page_type   = kind[0]
        target_mode = "verses" if page_type == "verse" else page_type
        if target_mode not in modes:
            continue

        if page_type == "verse":
            write_verse(kind[1], kind[2], kind[3], text, stats["verses"])
        elif page_type == "morphology":
            write_morphology(kind[1], text, stats["morphology"])
        elif page_type == "lexicon":
            write_lexicon(kind[1], text, stats["lexicon"])

    print(f"\nDone — {total:,} pages in XML.\n")
    for m in ("morphology", "verses", "lexicon"):
        if m not in modes:
            continue
        s = stats[m]
        row = f"  {m:12s}  created {s['created']:5,}  skipped {s['skipped']:5,}"
        if m == "verses":
            row += f"  no-tokens {s['empty']:4,}"
        print(row)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--morphology", action="store_true",
                   help="Generate Greek/Morphology/{CODE}.md files")
    p.add_argument("--verses",     action="store_true",
                   help="Generate Greek/{Book}/{NNN}/{Book}-{NNN}-{NNN}G.md files")
    p.add_argument("--lexicon",    action="store_true",
                   help="Generate Greek/Lexicon/{LEMMA}.md stubs (skips existing)")
    p.add_argument("--all",        action="store_true",
                   help="Run all three modes")
    args = p.parse_args()

    modes = set()
    if args.all or args.morphology: modes.add("morphology")
    if args.all or args.verses:     modes.add("verses")
    if args.all or args.lexicon:    modes.add("lexicon")

    if not modes:
        p.print_help()
        sys.exit(1)

    if not XML_PATH.exists():
        sys.exit(f"Error: {XML_PATH} not found")

    print(f"Modes:  {', '.join(sorted(modes))}")
    print(f"Source: {XML_PATH}")
    print(f"Vault:  {VAULT}\n")
    run(modes)


if __name__ == "__main__":
    main()
