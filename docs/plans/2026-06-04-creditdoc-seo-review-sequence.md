# CreditDoc SEO Review Sequence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve CTR and quality for the remaining unworked GSC-visible review pages without redoing prior CreditDoc review, noindex, Vigo, or metadata work.

**Architecture:** Use the database as the source of truth for review pages. Work in small, auditable batches from the saved June 4 startpack, updating only fields that can be supported by existing source data and verifying every touched live URL at the end of each batch.

**Tech Stack:** CreditDoc Astro SSR on Cloudflare Workers, Supabase runtime data, local SQLite mirror at `creditdoc/data/creditdoc.db`, DB update API in `creditdoc/tools/creditdoc_db.py`, project workpacks under `/srv/BusinessOps/CreditDoc Project Improvement/`.

---

## Phase 0: Reload Context And Freeze The Work Queue

**Files:**
- Read: `/srv/BusinessOps/creditdoc/AGENTS.md`
- Read: `/srv/BusinessOps/creditdoc/CREDITDOC_NOW.md`
- Read: `/srv/BusinessOps/creditdoc/CREDITDOC_NEXT.md`
- Read: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/README.md`
- Read: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/already_worked_review_slugs.csv`
- Read: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/tomorrow_first_batch_candidates.csv`

**Steps:**

1. Run `git -C /srv/BusinessOps/creditdoc status --short --branch`.
2. Confirm the branch is `cdm-rev-hybrid` and the repo is clean before edits.
3. Read the startpack README and CSVs listed above.
4. Treat `already_worked_review_slugs.csv` as the duplicate-work guard.
5. Do not touch any slug already listed as worked unless new GSC evidence shows a fresh issue.

**Verification checklist:**

- Repo status captured.
- First 13 candidates loaded from `tomorrow_first_batch_candidates.csv`.
- Prior-work guard loaded from `already_worked_review_slugs.csv`.

**Anti-pattern guards:**

- Do not restart from the full GSC top-page list.
- Do not rework Marco's, Vigo chain pages, Phase 1 held pages, noindex drop batches, or prior review metadata batches.
- Do not edit `src/content/lenders/*.json` directly for live profile changes.

---

## Phase 1: Audit The 13 First-Batch Pages Before Editing

**Files:**
- Read: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/tomorrow_first_batch_candidates.csv`
- Read DB: `/srv/BusinessOps/creditdoc/data/creditdoc.db`
- Write audit output: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/first_batch_live_audit_YYYY-MM-DD.csv`

**Current candidate evidence from June 4:**

| Slug | Category | GSC Impressions | Avg Pos | Live Status | Immediate Issue |
|---|---:|---:|---:|---:|---|
| `velnor-credit-repair-san-diego` | credit-repair | 21 | 1.4 | 200 indexable | protected, missing `seo_title` |
| `crisdon-credit-repair` | credit-repair | 29 | 1.6 | 200 indexable | protected, missing `seo_title` |
| `savage-squad-credit` | credit-repair | 20 | 1.6 | 200 indexable | protected, missing `seo_title` |
| `credit-repair-specialists` | credit-repair | 23 | 1.8 | 200 indexable | protected, likely wrong-intent/directory source |
| `dc-lending` | mortgages | 41 | 2.7 | 200 indexable | missing `seo_title`, generic meta |
| `consumer-credit-counseling-burlingame` | free-help | 38 | 2.7 | 200 indexable | already has title/meta; check internal links and H1 |
| `credit-pros` | credit-repair | 29 | 4.0 | 200 indexable | protected, missing `seo_title`, meta truncated |
| `lakehills-commercial-lending` | business-loans | 71 | 4.2 | 200 indexable | missing `seo_title`, business-loan opportunity |
| `capdeck-business-loans-san-jose` | business-loans | 24 | 4.3 | 200 indexable | meta contains rating claim; verify or replace |
| `cash-express-of-mwc` | personal-loans | 22 | 4.5 | 200 indexable | meta contains rating and loan amount; verify or replace |
| `nanakuli-housing-corporation` | free-help | 27 | 4.8 | 200 indexable | DB `review_status=draft`; decide before edits |
| `loandepot-new-york` | mortgages | 23 | 7.0 | 200 indexable | meta contains rating; verify or replace |
| `bay-area-loan` | mortgages | 22 | 8.0 | 200 indexable | meta contains rating; verify or replace |

**Steps:**

1. For each slug, query DB fields: `is_protected`, `processing_status`, `review_status`, `quality_score`, `website_url`, `seo_title`, `meta_description`, `description_long`, `services`, `pros`, `cons`, `similar_lenders`, `no_index`.
2. Fetch each live URL with a Googlebot user agent.
3. Record HTTP status, final URL, canonical, robots/noindex status, title length, meta length, H1, and obvious internal-link failures.
4. Save the audit CSV before any DB edits.
5. Split the 13 pages into:
   - `edit_now`
   - `source_validate_first`
   - `hold_do_not_touch`

**Verification checklist:**

- All 13 live pages checked.
- Audit CSV saved.
- Any page with questionable source alignment is moved out of `edit_now`.

**Anti-pattern guards:**

- Do not rely on the June 4 quick status check alone; rerun live checks tomorrow.
- Do not approve or promote pages based only on GSC rank.
- Do not keep rating, price, or loan-amount claims unless the source data supports them.

---

## Phase 2: Credit Repair CTR Batch

**Target slugs:**

- `velnor-credit-repair-san-diego`
- `crisdon-credit-repair`
- `savage-squad-credit`
- `credit-pros`
- `credit-repair-specialists` only if Phase 1 confirms it is not a wrong-intent directory page

**Files:**
- Modify DB via: `/srv/BusinessOps/creditdoc/tools/creditdoc_db.py`
- Use pattern: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Template_2026-05-23.md`
- Output: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/phase_2_credit_repair_updates_YYYY-MM-DD.csv`

**Steps per page:**

1. Confirm the slug is not already worked in `already_worked_review_slugs.csv`.
2. Confirm live URL returns 200, canonical is `/review/<slug>/`, and page is indexable.
3. Confirm DB protection state.
4. Draft a factual `seo_title` using the pattern:
   - `<Name> Review: Credit Repair Services & Alternatives`
   - or `<Name> Review: Credit Repair in <City>, <State>` if city/state is supported.
5. Draft a meta description using factual page data:
   - `Review <Name>: credit repair services, consumer checks, alternatives, and a quick CreditDoc fit quiz.`
6. Remove ellipses and unsupported certainty from existing meta descriptions.
7. If `is_protected=1`, update through `CreditDocDB.update_lender(..., updated_by='founder', reason='seo_ctr_batch_YYYY-MM-DD')`.
8. Verify `is_protected` remains unchanged after update.
9. Verify audit log records the field changes.
10. Revalidate/check live URL.

**Verification checklist:**

- SEO title exists and is under roughly 60-65 chars.
- Meta description is complete, factual, and not truncated.
- No invented ratings, prices, guarantees, or outcome claims introduced.
- Live page still returns 200 and remains indexable.

**Anti-pattern guards:**

- Do not use "best", "guaranteed", "approved", or "lowest".
- Do not keep `Credit Repair Specialists` if it is only a legal-directory result and not a useful CreditDoc finance/provider page.

---

## Phase 3: Business Loans, Mortgages, Free Help, And Personal Loans Batch

**Target slugs:**

- `lakehills-commercial-lending`
- `capdeck-business-loans-san-jose`
- `dc-lending`
- `loandepot-new-york`
- `bay-area-loan`
- `consumer-credit-counseling-burlingame`
- `nanakuli-housing-corporation` only after resolving the `review_status=draft` mismatch
- `cash-express-of-mwc` only after validating or removing rating/loan-amount claims

**Files:**
- Modify DB via: `/srv/BusinessOps/creditdoc/tools/creditdoc_db.py`
- Output: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/phase_3_non_credit_repair_updates_YYYY-MM-DD.csv`

**Steps per page:**

1. Recheck the live page and DB state.
2. For pages with rating claims in `meta_description`, verify source data exists.
3. If rating or amount support is not explicit, replace with neutral wording:
   - `Review <Name> in <City>, <State>: services, eligibility questions, costs to check, alternatives, and CreditDoc guidance.`
4. Add missing `seo_title` using category-specific language:
   - Business loans: `<Name> Review: Business Funding Checks`
   - Mortgages: `<Name> Review: Mortgage Services & Alternatives`
   - Free help: `<Name> Review: Counseling, Fit & Alternatives`
   - Personal loans: `<Name> Review: Loan Options, Fit & Alternatives`
5. For `nanakuli-housing-corporation`, decide whether the draft status is stale metadata or a real hold flag before any update.
6. Update through DB API only.
7. Revalidate and live-check every touched page.

**Verification checklist:**

- Rating/amount claims either verified or removed from metadata.
- DB and live page agree after revalidation.
- Every touched URL returns 200 and has no unintended noindex.

**Anti-pattern guards:**

- Do not invent NMLS, licensing, HUD, nonprofit, or accreditation claims.
- Do not turn mortgage pages into lead-gen claims unless the page has source data.
- Do not publish or promote `nanakuli-housing-corporation` from draft without understanding why it is draft.

---

## Phase 4: Quarantine Decision Plan

**Files:**
- Read: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/quarantine_candidates_need_decision.csv`
- Write: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/quarantine_decision_plan_YYYY-MM-DD.csv`

**Current lanes from June 4 classification:**

- `drop_or_redirect_no_db_match`: 7 pages
- `likely_dump_auto_or_title`: 10 pages
- `manual_keep_candidate_validate_sources`: 7 pages
- `chain_or_money_services_decision`: 53 pages
- `likely_dump_or_low_priority_non_strategy`: 3 pages

**Steps:**

1. Start with `drop_or_redirect_no_db_match` and `likely_dump_auto_or_title`; these are likely easiest to remove from future optimization.
2. Check live status for each URL before deciding.
3. If a URL already redirects safely, mark it `resolved_redirect_monitor`.
4. If a URL still returns weak/junk review content, prepare a redirect/noindex/drop recommendation, but do not execute until reviewed.
5. For `manual_keep_candidate_validate_sources`, check whether each entity is a real finance/lending/credit provider with a valid website.
6. For `chain_or_money_services_decision`, do not rewrite one by one. Decide a systematic chain template for Vigo/Ria/MoneyGram/check-cashing branches or hold as lower priority.
7. Save the decision CSV.

**Verification checklist:**

- Every quarantine row has a lane and recommended action.
- No quarantine page is optimized before classification.
- No live route is removed without an archive/redirect plan.

**Anti-pattern guards:**

- Do not optimize auto dealers, unrelated services, detective agencies, or generic doorway-looking pages just because they rank.
- Do not treat check-cashing/money-transfer chains as the first strategic wedge; keep them systematic and lower priority unless GSC shows strong qualified intent.

---

## Phase 5: Indexing And Measurement

**Files:**
- Read: `/srv/BusinessOps/CreditDoc_SEO/money_page_index_status.json`
- Read: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_GSC_Progress_Calendar_2026-06.md`
- Write: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/post_update_status_YYYY-MM-DD.csv`

**Steps:**

1. After each edited mini-batch, run live URL checks for all touched pages.
2. Confirm pages are in sitemap or SSR route injection as expected.
3. Confirm priority indexing queue behavior; submit eligible edited money/review pages if the existing indexing tool marks them eligible.
4. Log touched pages, previous GSC impressions/positions, and update date.
5. Measure after next GSC pull, then again after 21-28 days.

**Verification checklist:**

- Every touched page has a live status row.
- No 404s introduced.
- No unintended noindex introduced.
- GSC baseline recorded before edits.

**Anti-pattern guards:**

- Do not ask for GSC validation/review immediately after fixing stale crawl issues.
- Do not judge CTR improvement from one day of data.

---

## Final Execution Order

1. Phase 0 reload and duplicate-work guard.
2. Phase 1 audit all 13 first-batch pages.
3. Phase 2 edit 3-5 safest credit-repair pages first.
4. Verify live pages and commit.
5. Phase 3 edit the remaining non-credit-repair pages only after claim/source validation.
6. Verify live pages and commit.
7. Phase 4 classify quarantine rows, starting with obvious dump/no-DB/auto-title pages.
8. Phase 5 indexing and measurement log.

Do not deploy unless the edited DB/Supabase path requires no code deploy. If code/template changes are introduced later, use `/srv/BusinessOps/creditdoc/deploy.sh`, not bare `wrangler deploy`.
