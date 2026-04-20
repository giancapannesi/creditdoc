# Chain Page Differentiation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Protect the programmatic-SEO model (per-location pages) while killing thin-content risk on ~3,500 pages belonging to 50 multi-location chains. Keep pages, differentiate copy, add brand-hero canonicals.

**Architecture:**
- Stage 1 — Measure what we actually have (free, read-only CSV)
- Stage 2 — Add brand-hero pages (template work, free, zero data writes)
- Stage 3 — Rewrite thin first-paragraphs via Claude CLI (Haiku model, Max plan → no marginal cost), **batched + per-chain spot-check approval** for quality not cost
- Stage 4 — Monitor + prevent regression (free)

**Tech Stack:** SQLite DB (source of truth), Python analysis scripts, Astro static site, Claude Haiku API (only in Stage 3, only with approval), JSON-LD schema.

**Scale constraints:**
- 50 chains, ~3,500 location pages total
- Top 10 chains: MoneyGram (178), Western Union (149), Ace Cash Express (139), Advance America (107), Cash America Pawn (84), Titlemax (77), PLS Check Cashers (60), Montana Capital (60), WU Money Order Only (58), 5 Star Car Title (57)

**Non-negotiables (per CLAUDE.md):**
- DB is source of truth. All writes via `tools/creditdoc_db.py`, never direct JSON.
- FA-protected profiles (195) cannot be auto-edited.
- Never `git add -A src/content/lenders/` — use `creditdoc_build.py --export-and-commit`.
- No paid API call without founder approval + cost estimate.
- Never delete logos. Never touch `logo_url` in any of these tasks.
- CSV-first, manual approval, then apply.

---

## Stage 1 — Measure (Day 1, free, zero-risk)

### Task 1.1: Build `chain_similarity_analyzer.py`

**Goal:** Score every multi-location chain on thin-content risk so we can decide per-chain strategy. Uses same Jaro-Winkler implementation as `creditdoc_cfpb.py` — no pip installs.

**Files:**
- Create: `/srv/BusinessOps/creditdoc/tools/chain_similarity_analyzer.py` (~180 lines)

**Inputs:** SQLite DB at `data/creditdoc.db`, all rows with `processing_status='ready_for_index'` grouped by normalized name (lower + strip + collapse whitespace).

**Logic per chain (minimum 10 locations):**

1. Compute **description_short similarity** — average pairwise Jaro-Winkler on first 120 chars of `description_short`. Exclude address/phone/name tokens before comparing (replace with `<CITY>`, `<STATE>`, `<PHONE>`, `<NAME>` placeholders).
2. Compute **location uniqueness signals:**
   - `% with unique phone` (count distinct phones / count locations)
   - `% with unique address` (should be ~100% — flag if not)
   - `% with google_rating != null`
   - `% with google_reviews_count >= 1`
3. Compute **lead paragraph pattern** — does the first 50 chars of description start with the brand name (`Western Union is...`) vs the city (`At 3701 Constitution Ave NE...`)? Count both.
4. Assign `thin_content_risk`:
   - **HIGH** = desc_similarity > 0.85 AND brand-lead > 80%
   - **MEDIUM** = desc_similarity > 0.70 AND brand-lead > 50%
   - **LOW** = desc_similarity < 0.70 OR unique content ratio > 30%

**Output CSV:** `reports/chain_analysis_YYYY-MM-DD.csv`

Columns:
```
chain_name,location_count,desc_similarity_avg,unique_phone_pct,unique_address_pct,rating_present_pct,brand_lead_pct,city_lead_pct,thin_risk,suggested_action,sample_slug_1,sample_slug_2,sample_slug_3
```

`suggested_action` values: `CONSOLIDATE` (desc_similarity >0.95, <30% unique data — not worth keeping), `HERO_ONLY` (add brand page, keep locations, rewrite leads), `DIFFERENTIATE_LEADS` (keep all, rewrite first paragraph to lead with location), `KEEP_AS_IS` (already differentiated).

**CLI:**
```bash
python3 tools/chain_similarity_analyzer.py            # all chains ≥10
python3 tools/chain_similarity_analyzer.py --min 5    # include smaller chains
python3 tools/chain_similarity_analyzer.py --chain "western union"  # single chain detail mode
```

**Verify:**
```bash
cd /srv/BusinessOps/creditdoc
python3 tools/chain_similarity_analyzer.py --chain "western union" 2>&1 | tail -20
# Expect: thin_risk verdict, sample slugs, similarity score
python3 tools/chain_similarity_analyzer.py 2>&1 | tail -10
wc -l reports/chain_analysis_*.csv
head -3 reports/chain_analysis_*.csv
```

Must complete in <2 min on full DB. Must not write to DB.

**Acceptance:** CSV row for every chain ≥10 locations (≥50 rows). Manual sanity check: Western Union appears with `thin_risk ∈ {HIGH, MEDIUM}` (we already saw boilerplate in samples).

**Commit:**
```
feat(quality): chain similarity analyzer — CSV-only, read-only

Scores multi-location chains on description similarity, location data
uniqueness, and first-paragraph pattern. Outputs CSV with per-chain
thin_content_risk + suggested_action. No DB writes.
```

---

### Task 1.2: Jammi reviews CSV

**Not a code task.** Hand off: open the CSV in Drive/spreadsheet, spot-check the Top 10 chains, mark a `FINAL_ACTION` column per chain. Claude does not choose actions autonomously.

**Output:** `reports/chain_analysis_YYYY-MM-DD.csv` with `FINAL_ACTION` column filled by Jammi.

**Gate:** No Stage 2/3 work starts until this CSV exists with at least top 10 chains marked.

---

## Stage 2 — Brand-Hero Pages (Day 2, free, additive only)

### Task 2.1: Add brand_slug column + populate top 10

**Files:**
- Modify: `/srv/BusinessOps/creditdoc/data/creditdoc.db` — add nullable `brand_slug` TEXT column to `lenders` table
- Modify: `/srv/BusinessOps/creditdoc/tools/creditdoc_db.py` — expose `brand_slug` in `update_lender()` as a transient field

**Step 1:** Check if column already exists.
```bash
sqlite3 /srv/BusinessOps/creditdoc/data/creditdoc.db "PRAGMA table_info(lenders);" | grep brand_slug || echo "NO_COLUMN"
```

If `NO_COLUMN`:
```bash
sqlite3 /srv/BusinessOps/creditdoc/data/creditdoc.db "ALTER TABLE lenders ADD COLUMN brand_slug TEXT DEFAULT NULL;"
```

**Step 2:** Populate for Jammi-approved chains only. One-off script `/srv/BusinessOps/creditdoc/scripts/populate_brand_slug.py`:

```python
#!/usr/bin/env python3
"""Populate brand_slug for approved chains. Run only for chains flagged HERO_ONLY or DIFFERENTIATE_LEADS in CSV."""
import argparse, csv, sqlite3, sys
from pathlib import Path

def normalize(name): return name.lower().strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv_path')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--db', default='/srv/BusinessOps/creditdoc/data/creditdoc.db')
    args = ap.parse_args()

    approved = {}
    with open(args.csv_path) as f:
        for row in csv.DictReader(f):
            action = (row.get('FINAL_ACTION') or row['suggested_action']).strip()
            if action in ('HERO_ONLY', 'DIFFERENTIATE_LEADS', 'CONSOLIDATE'):
                approved[normalize(row['chain_name'])] = (action, row['chain_name'])

    db = sqlite3.connect(args.db)
    db.row_factory = sqlite3.Row
    updates = []
    for norm, (action, display) in approved.items():
        brand_slug = norm.replace(' ', '-').replace('/', '-')
        rows = db.execute("SELECT slug, json_extract(data,'$.name') AS name FROM lenders WHERE LOWER(TRIM(json_extract(data,'$.name')))=? AND json_extract(data,'$.processing_status')='ready_for_index'", (norm,)).fetchall()
        for r in rows:
            updates.append((brand_slug, r['slug'], display))

    print(f"Would update {len(updates)} rows across {len(approved)} chains")
    if args.dry_run:
        for b, s, d in updates[:20]:
            print(f"  {s} ← brand_slug={b} ({d})")
        return

    for b, s, _ in updates:
        db.execute("UPDATE lenders SET brand_slug=? WHERE slug=?", (b, s))
    db.commit()
    print(f"Committed {len(updates)} brand_slug updates")

if __name__ == '__main__': main()
```

**Verify:**
```bash
python3 scripts/populate_brand_slug.py reports/chain_analysis_2026-04-19.csv --dry-run
# Review output
python3 scripts/populate_brand_slug.py reports/chain_analysis_2026-04-19.csv
sqlite3 data/creditdoc.db "SELECT brand_slug, COUNT(*) FROM lenders WHERE brand_slug IS NOT NULL GROUP BY brand_slug;"
```

**Acceptance:** brand_slug is set on every location of every approved chain. Pawn/ATM/FA-protected profiles are NOT touched (this is additive metadata — can be rolled back by NULL-ing the column).

**Commit:**
```
feat(schema): brand_slug column + population for approved chains

Non-destructive metadata layer: every location of an approved chain
now has brand_slug set (e.g. 'western-union'). Enables brand-hero
pages and location-to-brand linking without touching any existing
profile content. NULL = no brand association (normal case).
```

---

### Task 2.2: Build brand-hero Astro route

**Files:**
- Create: `/srv/BusinessOps/creditdoc/src/pages/brand/[brand].astro`
- Modify: `/srv/BusinessOps/creditdoc/src/utils/data.ts` — add `getAllBrands()`, `getLendersByBrand(brandSlug)`

**Pattern:** Clone the structure of `src/pages/categories/[category].astro`. Brand hero shows:
- H1: `{brandDisplayName} Locations — Find Your Nearest Branch`
- Intro paragraph (from a per-brand JSON file, see Task 2.3)
- Interactive state-grouped list: all locations grouped by state, each state collapsible
- Sidebar: chain stats (total locations, avg rating, states covered)
- JSON-LD: `Organization` schema for the brand, `ItemList` of locations
- Canonical: `https://www.creditdoc.co/brand/{brand-slug}/`
- No AggregateRating (per Phase 0 Task 0.5 rule)

**`getStaticPaths`:** Query `SELECT DISTINCT brand_slug FROM lenders WHERE brand_slug IS NOT NULL` at build time via the existing DB→JSON export pipeline.

**DB export change needed:** Add `brand_slug` to the JSON export in `creditdoc_build.py --export-only`. Verify it appears in `src/content/lenders/*.json` after running.

**Step-by-step (executing agent):**

1. Read `src/pages/categories/[category].astro` end-to-end. Read `src/utils/data.ts` lines 200-260 (the category data helpers).
2. Add `getAllBrands()` and `getLendersByBrand(slug)` in `src/utils/data.ts` — mirrors `getLendersByCategory(slug)`.
3. Write `src/pages/brand/[brand].astro`. Follow the EXACT same URL/schema/breadcrumb pattern as categories. Use `https://www.creditdoc.co/brand/{slug}/` for canonical. NO hardcoded apex URLs — the pre-commit guard will block you.
4. Run `python3 tools/creditdoc_build.py --export-only` to regenerate JSON with brand_slug.
5. Verify output:
   ```bash
   python3 -c "import json; d=json.load(open('src/content/lenders/western-union-albuquerque-nm.json')); print('brand_slug:', d.get('brand_slug'))"
   # Expected: brand_slug: western-union
   ```
6. Smoke-test frontmatter by building ONLY one page locally — do NOT build full 16K site (it takes 6min+). Instead:
   ```bash
   cd /srv/BusinessOps/creditdoc && npx astro check 2>&1 | tail -20
   ```
   Check for TypeScript/Astro errors only.

**Acceptance:**
- File `src/pages/brand/[brand].astro` exists, ~200 lines, uses BaseLayout, canonical = www.
- After deploy, `https://www.creditdoc.co/brand/western-union/` returns 200, lists ≥100 locations grouped by state.
- `getAllBrands()` returns ≥1 brand (only approved ones).
- Pre-commit guard passes.

**Commit:**
```
feat(hub): brand-hero pages at /brand/{slug}/

Single canonical page per approved chain aggregating all locations by
state. Links location pages to brand hero via data.ts helpers. Zero
changes to location-level content.
```

---

### Task 2.3: Per-brand copy files

**Files:**
- Create: `/srv/BusinessOps/creditdoc/src/content/brands/western-union.json`
- (Repeat for each approved chain, one file each)

**Shape:**
```json
{
  "slug": "western-union",
  "display_name": "Western Union",
  "summary_short": "Global money transfer and bill payment network with 500,000+ agent locations worldwide.",
  "summary_long": "[2-4 paragraph brand overview — Jammi-written OR Haiku-drafted-and-approved — explaining parent company, services, where they're authoritative, what consumers typically ask about them]",
  "faq": [
    {"q": "How do I send money via Western Union?", "a": "..."},
    {"q": "What are Western Union fees?", "a": "..."},
    {"q": "Is Western Union safe?", "a": "..."}
  ],
  "official_website": "https://www.westernunion.com",
  "last_reviewed": "2026-04-20"
}
```

**Important:** If Haiku drafts the copy, it MUST be in a dedicated batch (see Stage 3 rules) and Jammi reviews each brand's JSON before it lands in git.

**Acceptance:** JSON file exists for every approved chain. Brand hero renders summary + FAQ from this file.

**Commit per batch:** `content(brands): add hero copy for {N} approved chains`

---

### Task 2.4: Link location pages to brand hero

**Files:**
- Modify: `/srv/BusinessOps/creditdoc/src/pages/review/[slug].astro`

**Change:** At the top of the review page, if `lender.brand_slug` is set, add a breadcrumb link + a "Part of the {BrandName} chain →" callout. One line of UI, no schema changes, no content changes.

```astro
---
// ...existing frontmatter...
const brandInfo = lender.brand_slug ? getBrandInfo(lender.brand_slug) : null;
---
{brandInfo && (
  <div class="text-sm text-muted mb-2">
    Part of the <a href={`/brand/${lender.brand_slug}/`} class="text-primary hover:underline">{brandInfo.display_name}</a> chain · {brandInfo.location_count} locations
  </div>
)}
```

`getBrandInfo` reads from `src/content/brands/{slug}.json`. Fails silently (returns null) if no brand file exists.

**Acceptance:** On any Western Union location page, the breadcrumb "Part of the Western Union chain · 149 locations" appears above the H1 and links to `/brand/western-union/`. Non-chain pages are unchanged.

**Commit:** `feat(internal-links): link chain locations to brand hero`

---

### Task 2.5: Add brand hero URLs to sitemap

**Files:**
- Modify: `/srv/BusinessOps/creditdoc/src/pages/sitemap.astro` (or wherever the sitemap XML is generated — grep first: `grep -rn "sitemap" src/ public/ | head -5`)

**Change:** Include `/brand/{slug}/` URLs for every distinct `brand_slug` in the DB.

**Acceptance:** `curl https://www.creditdoc.co/sitemap-index.xml` (after deploy) includes brand-hero URLs.

**Commit:** `feat(sitemap): include brand hero URLs`

---

## Stage 3 — Lead-Paragraph Rewrite (Day 3-7, free via Claude CLI / Max plan — **QUALITY APPROVAL PER BATCH**)

**Cost:** $0 marginal. Rewrites run via `claude` CLI (Max plan), not direct Anthropic API billing.

**Quality gate is why batches still exist:** Run Top 1 chain first (Western Union, 149 pages), review 5 sample outputs manually, then expand. Same rule as all bulk ops per CLAUDE.md Rule 4 — never touch thousands of rows without spot-checks.

### Task 3.1: Build `lead_rewriter.py` (wired to Haiku via `claude` CLI)

**Files:**
- Create: `/srv/BusinessOps/creditdoc/tools/lead_rewriter.py`

**Contract:**
- Reads DB rows where `brand_slug IS NOT NULL` (only approved chains).
- Skips `is_protected=1` (FA profiles — never auto-edit).
- Skips pages where `description_short` already leads with the location (heuristic: starts with "At ", "Located at ", or any digit — address numbers).
- For each candidate: builds a Haiku prompt with location data + current description + style requirements, gets new lead paragraph, writes to DB via `CreditDocDB.update_lender(slug, {'description_short': new_text}, updated_by='lead_rewriter')`.
- Uses the `force=False` default — if description_short was already human-edited, DB rejects the write with a "REPLACE value → different" protection error (see CLAUDE.md). Log and skip those.

**Prompt template:**
```
You're rewriting the first paragraph of a business directory page so it leads with location-specific information rather than brand boilerplate.

LOCATION:
- Brand: {name}
- Address: {address}
- City: {city}, {state}
- Phone: {phone}

CURRENT FIRST PARAGRAPH (to be replaced):
{description_short}

RULES:
1. Lead with "At {address}, {city}..." or "The {city}, {state} {name} branch offers..."
2. Include concrete, verifiable local data (address, phone, city).
3. Keep 2-3 sentences, max 250 characters.
4. Mention the brand ({name}) once — but not in the first five words.
5. If you have nothing location-specific beyond address/phone, output exactly: NO_CHANGE
6. Never invent hours, reviews, or data not provided.
7. Don't use marketing hype ("best", "trusted", "premium").

Output: only the new paragraph, no preamble.
```

**CLI:**
```bash
python3 tools/lead_rewriter.py --chain "western union" --dry-run           # prints diffs, no writes, no API calls — uses cached only
python3 tools/lead_rewriter.py --chain "western union" --dry-run --live     # calls API, prints diffs, no DB writes
python3 tools/lead_rewriter.py --chain "western union" --apply              # calls API + writes DB (per-batch approval required before this)
python3 tools/lead_rewriter.py --chain "western union" --limit 5            # test mode, first 5 locations only
```

**Quality guard (MANDATORY):** Before any `--apply` run, the script prints batch size + 3 random sample rewrites and prompts `Proceed? [y/N]`. Exit if not `y`.

**Cache:** API responses cached in `data/lead_rewriter_cache.json` keyed by slug + input hash. Re-runs don't re-spend.

**Acceptance:** 
- `--limit 5 --live` on Western Union produces 5 rewritten paragraphs, each starts with address/city, each mentions phone, each ≤250 chars. Reviewed manually.
- `--apply` on full WU (149 pages) runs, logs audit_log entries, and completes. Post-run spot check: 5 random WU pages have new leads.

**Commit per batch:** 
```
content(chain:{brand}): rewrite lead paragraphs to location-first (N pages)

Approved by Jammi on 2026-MM-DD. Batch size: N pages. Audit log:
audit_log table, filter by updated_by='lead_rewriter' AND timestamp
>= 'YYYY-MM-DD'.
```

---

### Task 3.2: Batch rollout + approval gates

**Cadence:**

| Batch | Chain | Pages | Gate |
|---|---|---|---|
| 1 | Western Union | 149 | Manual review of 5 samples before `--apply` |
| 2 | MoneyGram | 178 | Spot check 10 pages from batch 1 first |
| 3 | Ace Cash Express | 139 | Spot check |
| 4 | Advance America | 107 | Spot check |
| 5 | Cash America Pawn | 84 | Spot check |
| ... | ... | ... | ... |
| Final | Remaining 45 chains | ~2,800 | Bulk with spot checks every 5 chains |

**Each batch requires:**
1. Jammi explicit "proceed" before `--apply`
2. Independent inspection of 5 random outputs post-batch
3. Audit log entry confirming N writes

**Rollback:** Since DB writes via API populate `audit_log` with before/after values, any batch can be rolled back by:
```sql
UPDATE lenders 
SET data = json_set(data, '$.description_short', old_value)
WHERE slug IN (SELECT entity_id FROM audit_log WHERE updated_by='lead_rewriter' AND batch_tag='western_union_2026_04_19');
```

(Use the existing `creditdoc_db.py audit` CLI to reconstruct this.)

---

## Stage 4 — Monitoring (Day 7+, free, continuous)

### Task 4.1: Daily chain-thin-content scanner

**Files:**
- Create: `/srv/BusinessOps/creditdoc/tools/chain_monitor.py`
- Add to crontab: `0 15 * * * cd /srv/BusinessOps/creditdoc && python3 tools/chain_monitor.py --alert-telegram`

**Contract:**
- Re-runs Stage 1 similarity analysis daily.
- Compares vs prior day's CSV (git-tracked at `reports/chain_analysis_*.csv`).
- Alerts to Telegram if:
  - Any chain's `thin_risk` went from LOW → MEDIUM or MEDIUM → HIGH
  - Any new chain appeared with ≥10 locations and HIGH risk
  - Any chain's `desc_similarity` jumped by >0.10

**Acceptance:** First run produces baseline, subsequent runs alert only on regressions.

**Cost:** Free (stdlib only).

**Commit:** `feat(monitor): daily chain thin-content scanner + Telegram alerts`

---

### Task 4.2: GSC integration — track brand hero + chain location rankings

**Files:**
- Modify: `/srv/BusinessOps/creditdoc/tools/creditdoc_gsc.py` (or wherever GSC data is pulled — grep `gsc_data.py` too)

**Change:** Add a weekly report pulling impressions/clicks for `/brand/*` URLs and for location URLs grouped by `brand_slug`. Tracks whether:
- Brand hero pages gain traffic (expected: YES, we're creating new URLs)
- Location pages lose traffic (risk: canonical/duplicate confusion)
- Chain pages gain position (expected: YES, better differentiation)

**Output:** Weekly PDF to Google Drive.

**Acceptance:** First run produces a baseline report. Second run (7 days later) shows delta.

**Commit:** `feat(monitor): weekly GSC chain ranking report`

---

## Sequencing & Dependencies

```
Stage 1 (Day 1)
  └─ Task 1.1 analyzer → Task 1.2 Jammi review → CSV with FINAL_ACTION

Stage 2 (Day 2) [gated on FINAL_ACTION]
  ├─ Task 2.1 brand_slug column + populate
  ├─ Task 2.2 brand hero Astro route (parallel with 2.1)
  ├─ Task 2.3 brand copy JSONs
  ├─ Task 2.4 location → brand linker
  └─ Task 2.5 sitemap update
  (all five ship in one commit batch, one deploy)

Stage 3 (Day 3-7) [gated per batch by Jammi approval + cost estimate]
  ├─ Task 3.1 lead_rewriter tool
  └─ Task 3.2 batch rollouts (Western Union first)

Stage 4 (Day 7+) [continuous]
  ├─ Task 4.1 daily chain monitor
  └─ Task 4.2 weekly GSC chain report
```

---

## Rollback

- **Stage 1:** Analyzer is read-only. Delete the CSV = done.
- **Stage 2:** brand_slug is additive — `UPDATE lenders SET brand_slug=NULL;` restores prior state. `/brand/*` pages are new — delete files = gone. Sitemap update is additive — revert commit.
- **Stage 3:** Every rewrite has an audit_log entry with old value. Roll back any batch by scripted restore (SQL template in Task 3.2).
- **Stage 4:** Monitor is read-only.

---

## Success Metrics (check at Day 30)

| Metric | Baseline (Apr 19) | Target (May 19) |
|---|---|---|
| Chain pages flagged HIGH risk | ~20 chains (est.) | <5 chains |
| Avg desc_similarity on top 10 chains | ~0.85 (est.) | <0.60 |
| Brand hero pages indexed | 0 | ≥30 |
| Chain location pages with "brand_slug link" | 0 | ~3,500 |
| GSC position for "western union near me" | unknown | ≤20 |
| GSC impressions on `/brand/*` | 0 | ≥500/week |
| GSC impressions on chain location pages | unknown | no drop >15% |
| Total marginal API spend | $0 | $0 (CLI via Max plan) |

---

## Out of Scope (separate plans required)

- **Consolidation (CONSOLIDATE action from Stage 1 CSV):** If Stage 1 flags any chain as CONSOLIDATE (e.g. 100% identical descriptions, no unique location data), a **separate plan** is needed to merge N pages into 1 hero + redirects. That requires GSC impact analysis first — never delete an indexed page without checking its traffic.
- **Homepage brand-chain showcase:** Could add a "Browse by chain" module on homepage. Low priority.
- **Brand official-logo acquisition:** Many chains have hosted logos we could use instead of DDG favicons. Separate plan (DDG→hosted logo migration already captured in memory/`creditdoc_logo_url_problem.md`).
- **Schema.org `Franchise` markup:** Research whether Google recognizes it (it doesn't, as of last check). Not worth pursuing.

---

## Agent notes for executor

- Use `superpowers:executing-plans` to work task-by-task.
- Commit after each task completes local verification. Do NOT push without Jammi reviewing the commit.
- For any API-calling task (only Stage 3), print the cost estimate and WAIT for "proceed" before spending.
- Store test output + audit_log references in PRs/commit messages so rollback is always possible.
- Memory Palace: `wing=creditdoc`, `room=chain-differentiation` for any post-mortem or decision this plan produces.
