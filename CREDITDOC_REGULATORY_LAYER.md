# CreditDoc — Regulatory Data Layer

**Status:** EXECUTING — Phase 2 CFPB complaints at 2.46M/~5M + entity resolver DONE (7,096 matches)
**Detailed plan:** `CreditDoc Project Improvement/2026-05-08_REGULATORY_DATA_LAYER_PROJECT_PLAN.md`
**Original architecture:** `CreditDoc Project Improvement/2026-04-21_REGULATORY_DATA_LAYER_PLAN.md`
**Compliance research:** `CreditDoc Project Improvement/2026-04-29_RESEARCH_01_REGULATORY.md`
**Google Drive mirror:** https://drive.google.com/drive/folders/13Zm9_MD1S4MduPGBTugT3pSyew3cFtyK

---

## What This Is

A separate `regulator.db` fed by four free federal data sources. Every lender page gets regulator-verified content blocks that competitors cannot fabricate:

1. **CFPB Consumer Complaints** — "X complaints in 12 months, Y% resolved with relief" per company. ~6M records, daily refresh.
2. **CFPB Enforcement Actions** — "Fined $X in YYYY for Z." ~1,500 consent orders. Trust signals you can't fake.
3. **SBA 7(a) + 504 Loans** — Ranks top business lender per state/year. ~500K records. Fuels the Business Loans cluster (highest CPC category).
4. **FDIC Locations** — 78K branch records for geo queries. Data already downloaded to `data/fdic/`.

Enrichment happens at **render time** via `enrich.lookup_company()`, NOT bulk pre-compute. Drip-beats-flood rule stays locked.

---

## 6 Phases

| Phase | What | Time | Status |
|-------|------|------|--------|
| 0 | Install pipeline, create `regulator.db`, 11 empty tables | Day 1 AM | ✅ 2026-05-08 |
| 1 | CFPB Enforcement Actions (385 actions, 347 companies) | Day 1 PM | ✅ 2026-05-08 |
| 2 | CFPB Consumer Complaints (730-day backfill, ~5M records) | Day 2 | 🔄 BATCH INGEST — 2.46M/~5M, covered 2024-05-08→2025-01-30, crash-resilient patches applied |
| 3 | FDIC Locations (27,832 institutions + 78,347 locations) | Day 3 | ✅ 2026-05-08 |
| 4 | SBA Loans (373,980 loans + 16,263 state + 5,704 national rankings) | Day 4 | ✅ 2026-05-08 |
| 5 | Wire into /review/ + /answers/ renderer (feature-flagged) | Week 2 | ⬜ |
| 6 | Wire into FA profile scanner (reviewer aid, not autowrite) | Week 3 | ⬜ |

---

## Dependencies Cleared

- [x] Architecture fixes (data quality batches 1-6)
- [x] FDIC data downloaded
- [x] similar_lenders backfill complete
- [x] SSR code fixes deployed

## Awaiting

- [x] Jammi GO on Phase 0 — GIVEN 2026-05-08
- [x] Decision: CFPB backfill 365 vs 730 days — 730 selected
- [x] Decision: USER_AGENT email — admin@creditdoc.co
- [ ] Phase 2 batch ingest completion (~5M records target)
- [ ] Compute cfpb_company_stats (after all batches)
- [ ] Entity matching (regulator_entities → creditdoc slugs)
- [ ] Jammi GO on Phase 5 (render integration)

---

## Rules

- Separate DB (`regulator.db`) — zero schema changes to `creditdoc.db`
- Every phase: show Jammi output, wait for GO before proceeding
- Cron installed append-only, verify with `tools/verify_crons.sh`
- Feature flag for render-layer integration
- Per-phase checkpoint + explicit rollback path

---

## How to Resume

1. Read the detailed plan: `CreditDoc Project Improvement/2026-05-08_REGULATORY_DATA_LAYER_PROJECT_PLAN.md`
2. Check if `creditdoc/data/regulator.db` exists
3. Check if `creditdoc/tools/regulator_data/` exists
4. Resume from next incomplete phase above
5. Every phase needs Jammi GO before proceeding
