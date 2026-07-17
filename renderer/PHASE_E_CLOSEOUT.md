# Phase E — Renderer migration closeout audit trail (2026-07-17)

Master closeout for the CreditDoc Astro → Python+Jinja2 renderer
migration workstream. Covers Phase 2 (initial 4 families) through
Phase 3.7 (compare) plus the Phase A→E audit workstream that
verified the work.

## Founder mandate

> "keep looping and saving through the stages all the way until we
> have removed the neccessity to rebuild the entire site every time."

## Coverage delivered (renderer-authoritative pages)

| Family | Pages | Phase | Commit |
|---|---:|---|---|
| /review/ | 15,775 | Phase 2 | `dd8793c826` (milestone) |
| /answers/ | 495 | Phase 2 | `1c9d148add` |
| /blog/ | 129 | Phase 2 | `48a97622c1` |
| /financial-wellness/ | 139 | Phase 2 | `a7ba0534f1` |
| /categories/ | 19 | Phase 3.1 | `b99da60567`, `a3143baec0` |
| /city/ | 331 | Phase 3.2 | `9d4482db00`, `cb66891827` |
| /brand/ | 57 | Phase 3.3B | `843c496efb` |
| /state/ | 50 | Phase 3.4 | `84d365b1eb` |
| /browse/ | 467 | Phase 3.5 | `18ceb512bd` |
| /trends/ | 713 | Phase 3.6 | `9827e6231b`, `a74dded9f3` |
| /compare/ | 394 | Phase 3.7 | `785e98cfa0` |
| **Total** | **18,569** | **11 families** | |

## Coverage remaining (Astro-fingerprinted, plan v3 targets)

| Family | Pages | Blocker | Est. |
|---|---:|---|---|
| /credit-guide/ | 412 | Supabase ETL needed | 1 day |
| /best/ | 27 | SVG gradient determinism | 4 hours |
| /state/*/lending-laws/ | 50 | Template port (Phase 3.4B) | 3 hours |
| /tools/, /research/, /resources/, /about/, /courses/ | ~28 | Hand-authored static | 1 day |
| Legal pages | ~15 | Hand-authored static | 0.5 day |
| **Remaining subtotal** | **~532** | | ~3 days |

Plus infrastructure work (Rocks 1 & 3 in
`renderer/CREDITDOC_ARCH_REMEDIATION_PLAN_v3.md`):
- Kill `@astrojs/cloudflare` adapter (Rock 1) — 2 days
- Add per-file wrangler push to watch_and_rebuild (Rock 3) — 1 day

## Files touched this workstream

### Renderer code
- `renderer/db.py` — grew from 4 to 25+ query functions covering all
  11 families. Notable adds: `cities_with_lenders`, `all_brands`,
  `all_states_info`, `browse_pairs`, `all_trends_entries`,
  `all_comparisons`. Uses `sqlite3.connect(...uri=True, mode=ro)` for
  reader safety.
- `renderer/render.py` — 11 `render_*(slug, out_dir)` functions +
  matching CLI subcommands. Shared helper `_safe_jsonld_str()`
  hardens against `</script>` injection in JSON-LD.
- `renderer/build_all.py` — DB-authoritative full rebuild.
  `FAMILIES` tuple + `_purge_stale()` (Phase C fix) + flock guard on
  `/tmp/creditdoc_db_writer.lock` + per-file atomic writes.
- `renderer/watch_and_rebuild.py` — cron poll (60s) triggering
  per-slug re-renders on `updated_at` changes. Fixed status filter
  from `'approved'` to `'pending_approval'` in Phase 3.6 audit.
- `renderer/cutover.py` — parallelized parity gate for deploys.
- `renderer/generate_sitemap.py` — replaces `@astrojs/sitemap`.

### Templates (Jinja2)
- `renderer/templates/_header.html`, `_footer.html` — shared chrome
- `renderer/templates/{review,answer,blog,wellness}.html.j2` — Phase 2
- `renderer/templates/{category,city,brand,state,browse,trends,compare}.html.j2` — Phase 3
- Each family template has WebPage/CollectionPage + BreadcrumbList
  JSON-LD; several add ItemList/FinancialService/AggregateRating.

### Documentation
- `renderer/PHASE_3_1_CATEGORIES.md`
- `renderer/PHASE_3_2_CITY.md`
- `renderer/PHASE_3_3B_BRAND.md`
- `renderer/PHASE_3_4_STATE.md`
- `renderer/PHASE_3_5_BROWSE.md`
- `renderer/PHASE_3_6_TRENDS.md`
- `renderer/PHASE_3_7_COMPARE.md`
- `renderer/CREDITDOC_ARCH_REMEDIATION_PLAN_v3.md`
- `renderer/PHASE_E_CLOSEOUT.md` (this file)

## Parity gate — how "done" was measured per family

Every phase used the same visible-word ratio gate:

```
ratio = wordcount(renderer_visible_text) / wordcount(astro_visible_text)
```

Threshold: **≥ 0.80**. Rationale: below 0.80 signals meaningful
content missing (Google penalizes thin variants); above 1.0×–1.4× is
acceptable and often positive (renderer adds richer explainer copy).

Sample sizes:
- Phase 3.1: 19/19 (100%)
- Phase 3.2: 20/20 initial + follow-up 5 top cities after budget fix
- Phase 3.3B: 57/57 (100%)
- Phase 3.4: 50/50 (100%)
- Phase 3.5: 20/20 sampled
- Phase 3.6: 20/20 initial + 25/25 audit re-run
- Phase 3.7: 10/10 sampled

Failures caught and fixed inline (Phase 3.2 big-city floor 0.75 → 0.87
after adding scaling explainer block).

## Bugs caught by audits

### Phase 3.1 audit (agent, aea1d3d...)
JSON-LD `</script>` injection risk in ItemList if lender name contains
`</`. Fixed with `_safe_jsonld_str()` shared helper. Commit `a3143baec0`.

### Phase 3.2 audit
Status filter used `('ready_for_index','approved')` instead of Astro's
`('ready_for_index','pending_approval')`. Cities went 320 → 331 after
fix. `sed -i` across 5 SQL sites in `db.py`. Commit `cb66891827`.

### Phase 3.6 audit
Same status filter bug in `watch_and_rebuild.py:64` — the cron would
have silently dropped `pending_approval`-promoted lenders. Fixed in
`a74dded9f3`.

### Phase C independent reviewer (Opus, 2026-07-17)
Verdict: signed-off:N with 4 blockers. All 4 resolved in commit
`3b2f243493`:

1. Stale `dist/city/washington-dc/index.html` (renderer excludes DC,
   dir survived from pre-fix iteration) → purged
2. 50 stale `dist/state/*/lending-laws/index.html` Astro artifacts from
   Jul 16 → purged (Phase 3.4B ships fresh)
3. Fabricated city count discrepancy (claim 331, backup 332, renderer
   333) → actually 331 slugs + `/city/index.html` hub file = 332
   matches Astro exactly, `washington-dc` was the phantom 333rd
4. Fabricated compare 2-page delta explanation → verified all 4
   underlying lenders are `ready_for_index` today, delta is legit
   net-new coverage, not drift

Preventive fix: added `_purge_stale()` to `build_all.py` running
before each family render.

## Commands run (paste-verifiable)

```bash
# Full rebuild dry-run (2026-07-17)
$ python3 renderer/build_all.py --dry-run
[build_all] TOTAL: 18569 slug(s) would be rendered

# Real rebuild timing (Phase 3.6 snapshot)
$ python3 renderer/build_all.py --only trends
[build_all] trends: 713 ok, 0 fail in 13.0s

# Purge verification (Phase C)
$ mkdir dist/brand/__fake_stale_test__/ && touch dist/brand/__fake_stale_test__/index.html
$ python3 renderer/build_all.py --only brand
[build_all] brand: purged 1 stale slug dir(s): __fake_stale_test__
[build_all] brand: 57 ok, 0 fail in 1.9s
```

## Agents spawned

- Phase 3.1 audit: `aea1d3d59fd013063` (debugger, caught `</script>` risk)
- Phase 3.2 audit: `aea1d3d59fd013063` (debugger, caught status filter)
- Phase 3.4/3.5/3.6 audits: same debugger agent (multiple runs)
- Phase C reviewer: `a90d08965b3c3b903` (Opus, independent reviewer,
  cross-verified 3.1–3.7 closeouts from raw evidence)

## Commits, chronological

```
b99da60567 renderer: add /categories/ family (Phase 3.1 — 19 pages)
7747e3ef91 docs: Phase 3.1 /categories/ closeout — 19/19 parity pass, deploy pending
a3143baec0 renderer: escape </ in ItemList JSON-LD (audit fix)
9d4482db00 renderer: add /city/ family (Phase 3.2 — 320 pages)
eaad2d2358 docs: Phase 3.2 /city/ closeout — 20/20 sample parity pass, 320 pages rendered
cb66891827 renderer: Phase 3.2 audit fixes — status filter + big-city visible-word budget
843c496efb renderer: add /brand/ family (Phase 3.3B — 57 pages, all local)
824874e9b7 docs: Phase 3.3B /brand/ closeout
84d365b1eb renderer: add /state/ family (Phase 3.4 — 50 US states)
23bb63d7f1 docs: Phase 3.4 /state/ closeout
18ceb512bd renderer: add /browse/ family (Phase 3.5 — 467 category×city pages)
9827e6231b renderer: add /trends/ family (Phase 3.6 — 713 CFPB pages)
a74dded9f3 renderer: apply Phase 3.4-3.6 audit fixes
785e98cfa0 renderer: add /compare/ family (Phase 3.7 — 394 head-to-head pages)
f9f524ecc2 docs: Phase 3.7 /compare/ closeout
3b2f243493 renderer: phase C fix — purge stale slug dirs + audit deltas
8c0c03f13e renderer: phase D — v3 remediation plan
<pending> renderer: phase E — closeout audit trail (this doc)
```

## Deploy status

**Not deployed to production.** Local `dist/` contains the 18,569
renderer-authoritative pages plus the 415 remaining
Astro-fingerprinted pages. Live production still serves the Astro
Jul 16 build.

Deploy path when ready:
```bash
./deploy.sh   # runs wrangler deploy dist with Global API Key auth
```
Deploy blockers:
- Founder must review a spot-check render of each family
- Rock 1 (adapter removal) may be preferable to ship first so we
  don't push a partial hybrid
- Rock 2 (remaining 415 pages) at minimum needs strip-fingerprint
  pass so URLs don't 404 on cache miss

Rollback: `dist.trashed_r1_1784269927/` retains the Astro Jul 16 build.

## What comes after Phase E

Per `renderer/CREDITDOC_ARCH_REMEDIATION_PLAN_v3.md`:

1. Phase 3.4B — /state/*/lending-laws/ (3 hours)
2. Phase 3.8 — /best/ with deterministic SVG (4 hours)
3. Phase 3.3 — /credit-guide/ with Supabase ETL (1 day)
4. Phase 3.9 — static pages (1 day)
5. Phase 3.10 — kill @astrojs/cloudflare adapter (2 days) ← Rock 1
6. Phase 3.11 — per-file wrangler push in watch cron (1 day) ← Rock 3

Definition of "done" for the founder mandate: astro build fires only
on framework upgrades; dist/ has no `_astro/` or `_worker.js/`; a
single DB row change triggers a single-file live deploy in ≤90s.

Currently 0/3 — this workstream got us the coverage foundation
(18,569 pages renderer-authoritative). Rocks 1/2/3 close it out.

## Handoff

- Live plan: `renderer/CREDITDOC_ARCH_REMEDIATION_PLAN_v3.md`
- Per-family closeouts: `renderer/PHASE_3_*.md`
- Renderer entry point: `renderer/build_all.py` (also `--only <family>`
  and `--dry-run` flags; `--no-purge` opt-out for the new cleanup pass)
- Cron: `renderer/watch_and_rebuild.py` polls DB every 60s
- DB source of truth: `data/creditdoc.db` (SQLite, WAL mode)
- Templates: `renderer/templates/*.html.j2`, shared chrome in
  `_header.html` / `_footer.html`
- Parity gate: visible-word ratio ≥ 0.80 vs live Astro (samples
  documented in each PHASE_3_*.md)
