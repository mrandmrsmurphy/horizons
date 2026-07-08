# Redirect cleanup / verse upload — outstanding items

Context: mid-migration of vault verse pages to xed.miraheze.org via `~/pywikibot-xed/sync/push_main_xml.py`. Phase 1 (analysis pages) is done. Phase 2 (stub pages) is paused pending this cleanup. Full history/detail in Claude's memory: `project_verse_upload.md`.

## Bug found (2026-07-08)

`audit_main_xml.py` didn't check for the `<redirect>` element in `main.xml`, so MediaWiki redirect pages got misclassified as "missing verse pages" and `push_main_xml.py` created real (mostly blank) stub pages at redirect titles instead of skipping them. Fixed in both scripts so it won't recur.

Of the pages already created this way, 1,998 were identified as wrongly-created redirect titles. They split into categories — **not all of them should just become redirects** (see the `1 Chronicles/15/36` incident below).

## Done

- [x] Fixed `audit_main_xml.py` and `push_main_xml.py` to exclude `<redirect>` titles going forward
- [x] Converted the **1,855 confirmed-safe abbreviation-style titles** (e.g. `1S/14/52 → 1 Samuel/14/52`, same chapter/verse, just an abbreviated book name) to proper `#REDIRECT` pages. 0 skips, 0 errors. Log: `~/pywikibot-xed/sync/log/fix_wrong_redirects_abbrev_log.jsonl`
- [x] Caught and reverted a mistake: initially ran the redirect-fix against the full, uncategorized 1,998 list. Only 11 pages were actually converted before it was stopped; all 11 restored to original content via wiki revision history. No data lost.

## Vault slimming (2026-07-08)

Deleted 31,255 vault files (10,437 Bible/ notes + 10,436 Greek/ verse files + 10,382 Hebrew/ verse files) for verses confirmed to have real content live on the wiki (verified via `audit_deletable.py`, which checks each wiki page for actual `{{PG|`/`{{PH|` token data or a non-empty Analysis body — not just page existence). Vault went from 475M → 341M.

**12 verses held back** (not deleted — wiki page is blank or a redirect, not real content). User confirmed the reason for each on 2026-07-08:
- `Acts/8/37` — Majority Text only verse (absent from critical texts); user says it "looks right on the wiki so far"
- `Proverbs/20/18` — doesn't exist in the LXX at all, so no Greek is correctly expected, not a bug
- `Daniel/3/3`, `Daniel/4/2`, `Daniel/4/6`, `Daniel/4/35`, `Daniel/5/14`, `Daniel/5/18`, `Daniel/5/19`, `Daniel/5/20`, `Daniel/5/24` — Daniel's Greek text is a known text-critical nightmare; these have unparsed Greek in the vault (present but not tokenized into `{{PG|}}` form). Livable for now, needs addressing someday, but do NOT delete — the vault has real data that just hasn't made it to the wiki correctly yet.
- `Leviticus/5/26` — MT vs. Christian/LXX verse numbering difference; confirmed correctly a redirect, no action needed

Report used: `~/pywikibot-xed/sync/log/audit_deletable.jsonl`. Script: `~/pywikibot-xed/sync/audit_deletable.py` (note: the "substance" check specifically looks for `{{PG|`/`{{PH|` markers, not a naive regex on the `Greek =`/`Hebrew =` field — an earlier version of this script had a false-positive bug where the template's trailing `|` delimiter matched a "non-empty field" regex even when blank; fixed before running at scale).

This only covered `Bible/` scope (10,449 verse units). `Greek/` and `Hebrew/` still have ~21K/~24K files remaining beyond that — those cover other versions/apocrypha/Josephus not tied to a `Bible/` note, and haven't been audited for deletion yet.

## Outstanding

- [ ] **132 chapter-only target redirects** (e.g. `1 Maccabees/10/88 → 1 Maccabees 10`, `1 Corinthians/13/14 → 1 Corinthians 13`) — believed safe (apocrypha books only have chapter-level pages; some canonical-book "overflow" verses also roll up to chapter level), but not yet confirmed or actioned.
- [ ] **5 full-name spelling-variant redirects** (e.g. `1 Corinthian/6/15 → 1 Corinthians/6/15`, same verse, book name typo'd) — believed safe, not yet actioned.
- [ ] **6 held verse-shift titles** — redirect to a *different verse number* within the same canonical book/chapter, not just a naming variant. Unresolved: could be genuine LXX-vs-MT versification differences (which this project cares about preserving as distinct pages) or an outdated 2008-era editorial choice. Do not touch without figuring out which. Note: user confirmed `Leviticus/5/26 → Leviticus/6/7` (a *different* case caught during the vault-slimming audit, not one of these 6) is legitimately "MT vs. Christian numbering" and should stay a redirect — suggestive that these 6 may follow the same pattern, but not yet confirmed for these specific verses.
  - `1Ch/15/36 → 1 Chronicles/15/29`
  - `1Ch/24/32 → 1 Chronicles/24/31`
  - `1 Chronicles/15/36 → 1 Chronicles/15/29`
  - `1 Chronicles/7/41 → 1 Chronicles/7/40`
  - `1 Kings/9/29 → 1 Kings/9/28`
  - `1 Samuel/21/16 → 1 Samuel/21/15`
- [ ] Once the above is sorted, **resume phase 2 (stub pages)** with:
  ```bash
  cd ~/pywikibot-xed/sync && source ../.venv/bin/activate
  python3 push_main_xml.py --live --max-edits 1000
  ```
  Keep firing 1000-page batches after each completes; watch for a batch that creates fewer than 1000, which signals the whole migration is done.
