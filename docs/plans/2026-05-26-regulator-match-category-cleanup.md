# Regulator Match And Category Integrity Cleanup

Date: 2026-05-26  
Project: CreditDoc regulator/lender graph cleanup  
Trigger: CFPB responsiveness candidate generation exposed category/profile mismatches.

## Objective

Clean the CreditDoc regulator-to-lender graph before publishing CFPB/data authority assets.

The first public CFPB report must not rank or cite a provider through the wrong CreditDoc category, branch/location, duplicate slug, or weak entity match.

## Why This Matters

The CFPB responsiveness candidate set is useful, but the first pass exposed mismatches such as:

- `Goldman Sachs Bank USA` mapped to a CreditDoc row categorized as `pawn-shops`.
- `BMO Bank National Association` mapped to a row categorized as `personal-loans`.

That means the regulator data is valuable, but some CreditDoc profile/category/canonical mappings need review before the data can safely support:

- public research reports
- review-page trust blocks
- trend pages
- provider outreach
- future matching/routing logic

## Source Files

Initial workpack:

`/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/`

Primary candidate CSV:

`cfpb_responsiveness_candidates_enriched_2026-05-26.csv`

Databases:

- `/srv/BusinessOps/creditdoc/data/regulator.db`
- `/srv/BusinessOps/creditdoc/data/creditdoc.db`

## Non-Negotiable Rules

- Database is the source of truth.
- Do not directly edit `src/content/lenders/*.json`.
- Do not publish the CFPB responsiveness report before top candidates are manually classified.
- Do not use CFPB data adversarially.
- Do not claim a company is safe, approved, licensed, cheapest, best, or recommended based only on CFPB complaint data.
- Do not auto-change category on FDIC/NCUA-identified rows without understanding the federal-ID guard in `tools/creditdoc_db.py`.
- Keep all changes auditable.

## Phases

### Phase 1 - Audit Queue And Classification

Create a review CSV from the 131 CFPB candidate rows with additional decision columns:

- `correct_match`
- `correct_category`
- `recommended_category`
- `canonical_slug`
- `brand_level_needed`
- `include_in_report`
- `action`
- `manual_notes`

Classify at least the top 50 before any public report work.

Classification labels:

- `approved_for_report`
- `needs_category_fix`
- `needs_canonical_slug`
- `duplicate_or_subsidiary`
- `exclude_low_confidence_context`
- `needs_provider_identity_review`
- `exclude_from_report`

### Phase 2 - Safe DB Fixes

Only after Phase 1 classification:

- fix obvious category errors through `CreditDocDB.update_lender()`
- set `brand_slug` where appropriate
- add `review_status` / `validation_notes` for report eligibility
- keep risky rows excluded
- preserve protected/federal-ID guardrails

### Phase 3 - Regenerate CFPB Candidates

Rerun the candidate query after fixes:

- compare before/after
- verify no top candidates have obvious category mismatches
- produce final report input CSV

### Phase 4 - Public Report Build

Only after Phase 3:

- build `/research/most-responsive-consumer-finance-providers-2026/`
- add methodology/caveats
- add provider-friendly citation language
- add internal links
- create press pitch/outreach assets

## Success Criteria

Phase 1:

- top 50 candidates classified
- all obvious category/profile mismatches marked
- no DB writes yet

Phase 2:

- safe fixes applied via DB API
- audit log records changes
- Supabase retry queue checked
- no accidental noindex/index changes

Phase 3:

- regenerated candidate CSV
- top public candidates clear manual review

Phase 4:

- public report builds cleanly
- internal links and press assets ready
- Drive copy uploaded

## Strategic Note

This is not "waiting for Google." This cleanup improves the lender intelligence graph that powers:

- local city pages
- category pages
- review pages
- CFPB/data research
- provider outreach
- future routing/matching
