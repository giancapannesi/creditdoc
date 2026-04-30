# CreditDoc — NEXT (RULE 10 handoff, last updated 2026-04-29 post-Option-C+)

## What's next

### 1. **HTML parity drift — INVESTIGATED, 4 drift sources identified (top priority)**

Forensic diff complete on credit-saint (worst at 4.13%). Findings file:
`CreditDoc Project Improvement/2026-04-29_HTML_PARITY_DRIFT_FINDINGS.md`

**Real drift sources (not formatting noise):**
1. **Date stringification** — `lenders.last_updated` returned as full ISO `2026-04-29T12:10:54.809439+00:00` instead of `2026-04-05` date-only. Hits JSON-LD `datePublished` and visible "Updated" line. Cosmetic but affects search snippets. Fix: ~5 LOC slice in SSR loader.
2. **`similar_lenders` cards rendered with empty fields (CRITICAL)** — logos, descriptions, ratings, pricing, BBB, money-back, "Best for" all blank on preview. Confirmed via JSON inspection: `similar_lenders` is a **list of slug strings** in JSON; build-time prerender expands via `getAllLenders()` filesystem join. SSR calls `getLendersBySlugListRuntime` then `shapeCatalogToLenderStub` — but the stub function isn't selecting/exposing the card-render columns. Fix: ~30-50 LOC in `data-runtime.ts`.
3. **5 `/compare/credit-saint-vs-X/` cards missing** on preview. Either A.2 comparisons backfill missed rows OR `getComparisonsForLenderRuntime` filter mismatch. Need to read the runtime query.
4. **Service array order shuffled** — JSONB roundtrip doesn't preserve order. Fix: `.sort()` ~3 LOC.

**Read-only next steps (this loop, no DB writes, no edits without diff):**
- DONE — db.ts + data-runtime.ts read; root cause confirmed (CATALOG_COLUMNS 8 cols, shapeCatalogToLenderStub minimal, comparisons limit=6 hardcoded).
- DONE — `tools/cdm_rev_structural_parity.py` written + 10-slug baseline captured (0/10 pass).
- DONE — patch proposal written (4 patches, ~18 LOC after re-scoping with existing infra, zero schema) — see findings doc.
- DONE — drop-in unified diff blocks for all 4 patches written into findings doc § "drop-in diff blocks". Application is now mechanical on greenlight.
- **AWAITING Jammi greenlight** to apply patches.
- After greenlight: apply → rebuild → `npx wrangler pages deploy dist` → re-run `tools/cdm_rev_structural_parity.py` (target 10/10) → re-run `tools/cdm_rev_html_diff.sh` (target <0.1%).

### 2. **Phase 2.4 end-to-end revalidation probe**

Once parity drift understood: write to a lender row via `creditdoc_db.py update_lender(slug, fields)`, time the round-trip from DB write → globally-cached new HTML. Target ≤10s p95 over 20 trials. **This is what flips OBJ-1 to GREEN.**

### 2. **Activate revalidate ping in production tools**

Phase 2.3 is wired, but only fires when `REVALIDATE_TOKEN` env var is set. Token lives at `/srv/BusinessOps/tools/.creditdoc-revalidate.env` (chmod 600). To activate:

```bash
# In any cron unit that calls creditdoc_db.py writers:
. /srv/BusinessOps/tools/.creditdoc-revalidate.env
export REVALIDATE_TOKEN
```

Cron units that should source it (need Jammi greenlight to modify crontab):
- `creditdoc_db_sync.py` (07:00 UTC daily)
- `creditdoc_guardian.py` (hourly)
- Any cluster_answer publisher
- Any blog_writer.py / publish_blog_posts.py invocation

### 3. Phase 3.1 — audit_log triggers (off-limits without explicit greenlight)

Live Supabase trigger creation. Plan unchanged.

### 4. **Strategic question from Jammi — 20K+ records full migration to Supabase — ANSWERED (Apr 29 loop)**

> "when are we pulling the full 20,000 plus records to the database with all the information, maps locations, links etc - this is going to be the acid test - all that stuff needs to work seamlessley"

**Short answer:** It's already done — but the SSR can't read it yet. Full analysis in `CreditDoc Project Improvement/2026-04-29_20K_RECORDS_QUESTION_ANSWER.md`.

**Confirmed via `jq`:** `body_inline jsonb` (A.1 backfill, 20,813/20,825 rows) contains every per-lender field — logo_url, rating, pricing.tiers[], rating_breakdown.bbb, money_back_guarantee, similar_lenders[], best_for[], services[], pros/cons, address, affiliate_url, etc. The data IS in Supabase.

**The bottleneck is projection, not migration.** `CATALOG_COLUMNS` (db.ts:44) is 8 cols. `shapeCatalogToLenderStub` doesn't read body_inline jsonb paths. Patch 1 in the parity findings doc fixes this with ~30 LOC across `db.ts` + `data-runtime.ts`, zero schema changes.

**Recommended sequence:**
1. Apply the 4 parity patches → HTML parity GREEN → OBJ-1 unblocks.
2. Phase 2.4 revalidate probe → OBJ-1 fully GREEN.
3. **Path X (proper column promotion) is DEFERRED**, only triggered when one of: column-level RLS needed (affiliate_url scoping), GIN-indexed structured search needed, foreign-key referential integrity needed, or per-column audit_log granularity needed (Phase 3.1).

The "acid test" Jammi was pointing at is now framed as a render-side fix, not a data-migration project. ~30 LOC instead of 8-12h.

---

## What's DONE this loop

- [x] Pushed `cdm-rev-hybrid` to origin (5 commits) earlier
- [x] A.2 backfill applied — 303 rows (wellness 81 / comparisons 165 / brands 57)
- [x] A.3 DDL applied + backfill — 139 rows (states 50 / categories 18 / glossary 71)
- [x] A.4 DDL applied + backfill — 77 rows (blog 34 / listicles 26 / answers 14 / specials 3)
- [x] REVALIDATE_TOKEN set on CF Pages preview env
- [x] Worker redeployed (14:49 UTC): `https://d1ed5fba.creditdoc.pages.dev`
- [x] Phase 2.3 wired: `_ping_revalidate()` + 9 writer injection points + `/api/revalidate` extended to 11 ContentTypes — commit `7b5065d7e4`
- [x] **Option C+ utils/data.ts split landed** — commit `c5ab63a4f1`. data.ts (779→408 pure) + new data-build.ts (367 fs-backed) + 24 page imports + Header.astro switched to data-runtime. `grep -rln 'node:fs' dist/_worker.js/` returns nothing.

## What's NEXT (in order, awaiting unblock)

1. **(Jammi action)** Refresh `CLOUDFLARE_API_TOKEN` in `/srv/BusinessOps/.env` per item 1 above.
2. **(loop)** `cd /srv/BusinessOps/creditdoc && source /srv/BusinessOps/.env && export CLOUDFLARE_API_TOKEN && npx wrangler pages deploy dist --project-name creditdoc --branch cdm-rev-hybrid`
3. **(loop)** Run `tools/cdm_rev_html_diff.sh` — Phase 1 acceptance gate (d). If green: OBJ-1 → GREEN.
4. **(propose)** Section A.5 plan for full 20K+ lender records → Supabase row-level resources. Wait for Jammi greenlight before any DB DDL.
5. **(crontab modification — Jammi greenlight)** Wire `REVALIDATE_TOKEN` into cron units.
6. **(Jammi greenlight)** Phase 3.1 audit_log trigger creation.
7. **(separate explicit greenlight + 24h notice)** Phase 6 DNS flip.

---

## What NOT to do

- Do NOT touch `arch-overhaul` branch (parallel-window territory).
- Do NOT auto-flip DNS. Production cutover is separate explicitly-approved step. Jammi: "We are not pulling any triggers for cutover until site is completely reviewed and tested. We need to dot every i and cross every t."
- Do NOT touch `utils/data.ts` or `utils/data-build.ts` without showing the diff first — pre-edit rule applies and the split is a recent (today) change.
- Do NOT redo `/privacy/`, `/terms/`, `/disclosure/` — they are LIVE and 200 OK.
- Do NOT propose A.5+ (full lender migration) execution until preview deploy is clean and HTML diff smoke test passes.

---

## Reference: branch state at handoff

- Working branch: `cdm-rev-hybrid` — pushed to origin at `c5ab63a4f1`
- Latest commit: `c5ab63a4f1` — CDM-REV Option C+ utils/data.ts split
- Previous: `7b5065d7e4` — Phase 2.3 wiring
- `main`: untouched
- `arch-overhaul`: parallel-window, off-limits
- Live `creditdoc.co`: serving previous Vercel static build, untouched
- CF Pages preview: `https://cdm-rev-hybrid.creditdoc.pages.dev` (deploy `d1ed5fba` — STALE, awaits redeploy after token refresh)

Re-check verifier any time:
```bash
python3 tools/verify_strategic_objectives.py
```
