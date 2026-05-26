# CreditDoc Profile Quality Agent Plan

Date: 2026-05-26  
Owner: CreditDoc editorial/data operations  
Purpose: continuously improve lender/profile pages to the quality level expected for authority, SEO, user trust, and future monetization.

## Objective

Create a repeatable profile-improvement workflow that makes every important lender page:

- correctly matched to the real legal/brand entity
- assigned to the right CreditDoc category
- linked to the official public website
- written as a useful consumer-facing profile
- free of weak scraped/source-derived filler
- safe for inclusion in research reports, local pages, category hubs, and future routing logic

This is a permanent operating lane, not a one-off cleanup.

## Quality Bar

Every reviewed profile should meet this standard:

- Correct entity: the profile must describe the actual company behind the slug.
- Correct category: banking, credit union, mortgage, credit monitoring, debt relief, etc. must match the real consumer-facing role.
- Brand vs branch clarity: brand-level pages should not show misleading branch-only phone/address details.
- Official URL: website should point to the provider's official consumer page where possible.
- Useful copy: description should explain what the provider offers, who it is relevant for, and what consumers should verify.
- No unsupported claims: do not call a provider best, safest, cheapest, licensed, guaranteed, approved, or recommended unless there is a source-backed basis and the claim is scoped.
- CFPB/data caveat: complaint and response data can support context, not endorsement.
- Published only after review: set `review_status: published` only when the profile is clean enough to be visible and reused.

## Agent Responsibilities

The dedicated Profile Quality Agent should:

1. Pull a daily queue of profiles from high-value sources.
2. Inspect the current DB record and exported JSON.
3. Verify the entity through official/public sources.
4. Decide whether the page is a branch profile or brand profile.
5. Update the DB through `tools/creditdoc_db.py` only.
6. Export changed lender JSON.
7. Check Supabase retry queue.
8. Update the batch documentation and audit CSV/workpack where relevant.
9. Run the minimum build/check suite for the batch.
10. Commit each logical batch with a clear message.

## Queue Priority

Work profiles in this order:

1. CFPB/regulator report candidates and any profile feeding a public research asset.
2. Pages already receiving impressions, clicks, or internal links.
3. Lenders appearing across many city/category pages.
4. Profiles with wrong category, weak source copy, missing official website, draft status, or branch/brand mismatch.
5. Small-town/local authority pages that need stronger lender support pages.

Useful queue signals:

- `review_status` is `draft` or `needs_manual_review`
- category mismatch discovered in regulator matching
- website is missing, non-official, Wikipedia, Instrumentl, random directory, or branch-only
- `description_short` / `description_long` is missing or weak
- brand profile has a single branch address/phone
- high CFPB complaint volume or high internal-link importance

## Source Rules

Preferred sources:

- provider official website
- FDIC / NCUA / regulator databases where entity identity matters
- CFPB data for complaint/response context
- state regulator pages where licensing or local law context is needed
- company investor/press pages only for neutral corporate facts

Avoid as primary sources:

- Wikipedia as a profile authority source
- Instrumentl or generic nonprofit/company directories
- random SEO directories
- unsourced scraped text
- affiliate pages making unsupported product claims

## Write Rules

The database is the source of truth.

- Use `CreditDocDB.update_lender()`.
- Do not directly edit `src/content/lenders/*.json`.
- Back up `data/creditdoc.db` before meaningful write batches.
- Use `updated_by='regulator_profile_review'` or a similarly specific operator for normal profiles.
- Use `updated_by='founder'` only when a founder-protected or federal-ID-guarded row requires the authorized override.
- Preserve founder protection after authorized updates.
- Use `force=True` only for intentional profile-copy replacement after review.
- Export changed lender JSON after DB writes.
- Confirm no unresolved Supabase retry rows for touched slugs.

## Page Template Pattern

For brand-level financial profiles, use this structure in the data:

- `name`: consumer-recognizable brand/legal name
- `category`: correct CreditDoc category
- `website`: official public consumer URL
- `phone`: blank unless a durable brand-level support number is verified
- `address`: blank unless the page is intentionally a location page
- `description_short`: one concise consumer summary
- `description_long`: two short paragraphs:
  - what the provider offers
  - what consumers should verify before applying/opening an account
- `meta_title`: neutral review/profile title
- `meta_description`: neutral, useful search snippet
- `review_status`: `published` once reviewed

## Documentation Rules

Each batch must record:

- backup path
- slugs touched
- fields changed
- source rationale
- protected/founder override use, if any
- Supabase retry result
- exported JSON result
- build/check result
- commit hash

Update the active workpack README when the batch belongs to a specific project, and update `CREDITDOC_NOW.md` / `CREDITDOC_NEXT.md` when it affects the broader project state.

## Cadence

Suggested daily operating rhythm:

- 10 to 25 high-priority profiles per day when doing light cleanup.
- 3 to 8 profiles per day when research/copy quality is high-touch.
- Stop and commit after each coherent batch.
- Do not leave dirty worktrees overnight.

## Success Metrics

Track:

- reviewed profiles per day
- wrong-category profiles fixed
- weak-source profiles replaced
- branch/brand mismatches removed
- profiles moved to `published`
- high-priority CFPB/report candidates cleared
- local/category pages supported by reviewed lender profiles

## Current Launch Queue

The first queue comes from the CFPB responsiveness workpack:

- Completed: First Tech Federal Credit Union, Mountain America Credit Union, WaFd Bank, Hancock Whitney Bank, San Diego County Credit Union.
- Completed post-regeneration review: Goldman Sachs Bank USA, BMO Bank, Synovus Bank.
- Remaining policy holds: MoneyLion and Sarma.

After the policy holds are decided, move into the next top CFPB/regulator candidates and then profiles with high internal-link importance from local/city pages.
