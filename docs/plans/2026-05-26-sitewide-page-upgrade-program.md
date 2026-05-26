# CreditDoc Sitewide Page Upgrade Program

Date: 2026-05-26  
Status: active planning  
Owner: CreditDoc growth/content operations  
Related plan: `docs/plans/2026-05-26-creditdoc-local-authority-graph.md`

## Objective

Upgrade every important CreditDoc page family so each page becomes part of the
same authority graph:

`local page -> category page -> provider profile -> state rules -> answer cluster -> tool/resource -> original research`

The goal is not cosmetic polishing. The goal is to make every page more useful,
more internally connected, more defensible for YMYL, and more likely to earn
clicks, links, provider corrections, and future routing data.

## What "Upgraded" Means

A page is upgraded only when it passes these checks:

1. **Useful Above The Fold**
   - The page immediately tells the user what it covers.
   - No generic filler, thin intro, or misleading total/count language.
   - Local pages show local value, not just national directory copy.

2. **Graph Links Present**
   - Links to at least 3 relevant internal graph layers where possible:
     city/category, provider profile, state rules, answer, tool, research, or
     resource.
   - No links to archived, noindexed, held, quarantined, or wrong-vertical
     provider pages.

3. **YMYL-Safe Claims**
   - No unverified licensing, approval odds, cheapest/best/safest claims.
   - CFPB complaint data is framed as transparency context, not proof of
     wrongdoing or endorsement.
   - Local regulations are presented as state/city context, not as a claim that
     a specific provider is licensed unless direct proof exists.

4. **Entity Quality**
   - Provider references use correct category, city/state, and company identity.
   - Duplicate subsidiaries, chain locations, and weak profiles are handled
     explicitly.

5. **Search Result Utility**
   - Title/meta match the user intent.
   - Page has a clear next step, comparison path, or educational path.
   - FAQ/schema is used where the content genuinely supports it.

6. **Measurement Ready**
   - Page family can be tracked by impressions, CTR, clicks, rankings,
     backlinks, provider corrections, and engagement events where available.

## Page Families To Upgrade

### 1. City Guides

Templates:

- `src/pages/credit-guide/[slug]/index.astro`
- `src/pages/city/[slug].astro`

Priority:

- Keep daily city/small-town expansion running.
- Upgrade existing city pages with the strongest strategic value first:
  small towns, regional towns, pages with impressions, and pages linked to
  high-value finance categories.

Upgrade standard:

- Add clear local finance context.
- Link to relevant city-category pages.
- Link to state lending law page.
- Link to 2-4 relevant answer pages.
- Link to at least one tool/resource where appropriate.
- Link to original research when CFPB/regulatory data is discussed.
- Avoid claiming the page is a complete list unless the dataset is complete.

Batch size:

- 10-25 city pages per batch.

Acceptance checks:

- Sample 5 pages per batch manually.
- Confirm at least 5 meaningful internal links across at least 3 graph layers.
- Confirm no links to archived/noindexed profiles.

### 2. City-Category Pages

Templates:

- `src/pages/credit-guide/[slug]/[category].astro`
- `src/pages/browse/[catSlug]/[citySlug].astro`

Priority:

- Personal loans, emergency cash, credit repair, debt relief, credit unions,
  banking, mortgages, fintech, check cashing, and business loans.

Upgrade standard:

- Clarify whether listings are complete inventory or selected CreditDoc
  profiles.
- Add category-specific local context.
- Add state-rule and consumer-risk context.
- Link to provider profiles only when profile quality is acceptable.
- Add relevant answer/tool links.
- Avoid overclaiming provider availability, approval, price, speed, or
  licensing.

Batch size:

- 10 city-category pages per batch for manual QA.
- Template-level improvements may roll out to all pages only after spot checks.

Acceptance checks:

- No misleading provider counts.
- No irrelevant quiz/resource blocks for categories where they do not fit.
- No provider cards for archived/noindexed pages.

### 3. Review/Profile Pages

Template:

- `src/pages/review/[slug].astro`

Priority:

- Indexed pages with impressions and poor CTR.
- Report-included CFPB providers.
- Profiles appearing on upgraded city/category pages.
- Profiles with regulator data, state context, or strong local usefulness.

Upgrade standard:

- Confirm category and identity before improving.
- Add state regulatory context where available.
- Add CFPB/data explainer link where complaint data appears.
- Add link to relevant research reports when the provider is included.
- Add related city/category links where relevant.
- Improve title/meta only through the approved data path.
- Keep weak, wrong-vertical, raw, unsupported, or ambiguous pages noindexed or
  archived.

Batch size:

- 10-15 provider pages per batch.

Acceptance checks:

- Each touched page has a source/evidence note.
- No noindex removal without explicit quality decision.
- Exact built/static reference scan for any archived or redirected profiles.

### 4. Trends / Regulator Pages

Templates:

- `src/pages/trends/[slug].astro`
- `src/pages/trends/index.astro`

Priority:

- Companies with reliable regulator matches.
- Providers included in research reports.

Upgrade standard:

- Add methodology context.
- Link back to profile pages where quality supports it.
- Link to `/research/consumer-complaints/` and relevant CFPB reports.
- Keep trend pages aligned with archived/noindexed profile filtering.

Batch size:

- Template-level only, then spot-check 10 generated pages.

Acceptance checks:

- No generated trends page for archived/noindexed lender-backed records.
- No misleading interpretation of complaint volume.

### 5. Compare Pages

Template:

- `src/pages/compare/[slug].astro`

Priority:

- High-intent comparisons involving major providers or improved provider pages.

Upgrade standard:

- Add clearer comparison criteria.
- Link to both provider profiles.
- Link to category, relevant answers, and research/data methodology.
- Avoid declaring a winner unless there is a defensible, narrow criterion.

Batch size:

- Template-level improvements, then 20 page spot-checks.

Acceptance checks:

- Provider identity and category are correct.
- No unsupported ranking or endorsement language.

### 6. Answer Pages

Templates:

- `src/pages/answers/[slug].astro`
- `src/pages/answers/index.astro`

Priority:

- Questions that support city/category/provider clusters.
- Questions with GSC impressions and low CTR.
- Questions that explain CFPB, state rules, credit repair, debt relief, loans,
  and local borrowing choices.

Upgrade standard:

- Direct answer at the top.
- Link to one relevant city/category page where useful.
- Link to one category page.
- Link to one tool/resource where useful.
- Link to research or data source where the answer depends on public data.

Batch size:

- 20-30 answer pages per batch.

Acceptance checks:

- No generic internal links.
- Answer remains educational, not regulated advice.

### 7. Research Pages

Templates/pages:

- `src/pages/research/index.astro`
- `src/pages/research/consumer-complaints.astro`
- `src/pages/research/lending-transparency.astro`
- `src/pages/research/most-responsive-consumer-finance-providers-2026.astro`
- `src/pages/research/state-of-subprime-lending-2026.astro`

Priority:

- CFPB responsiveness report release loop.
- Research hub.
- Complaint transparency explainer.

Upgrade standard:

- Each report links to methodology/data pages.
- Each report links to relevant provider/category/state/city assets.
- Research hub surfaces latest and evergreen reports.
- Press page and data page link to original reports.
- Outreach trackers exist for every report with backlink/provider engagement
  potential.

Batch size:

- One report/research page at a time.

Acceptance checks:

- Claims are source-backed.
- Positive/neutral framing for CFPB data.
- Outreach assets and tracker exist.

### 8. State Law Pages

Templates:

- `src/pages/state/[slug].astro`
- `src/pages/state/[slug]/lending-laws.astro`
- `src/pages/state/index.astro`

Priority:

- States with the most city pages.
- States tied to high-value categories and report/provider clusters.

Upgrade standard:

- Link to major city guides in the state.
- Link to relevant category pages.
- Link to answer pages explaining the rule in plain English.
- Link to CFPB/data methodology where appropriate.
- Avoid applying state rules to a specific provider unless verified.

Batch size:

- 5-10 states per batch.

Acceptance checks:

- No unverified licensing claims.
- Links point to active/indexable city/category pages.

### 9. Tools And Resources

Templates/pages:

- `src/pages/tools/index.astro`
- `src/pages/tools/borrowing-power-quiz.astro`
- `src/pages/tools/credit-score-simulator.astro`
- `src/pages/tools/debt-payoff-calculator.astro`
- `src/pages/resources/index.astro`
- `src/pages/resources/debt-credit-letter-templates/*`
- `src/pages/resources/credit-report-checklist/*`

Priority:

- Tools/resources that can sit naturally inside city/category/answer paths.

Upgrade standard:

- Link tools from relevant city/category/answer pages.
- Link tools back into research, answers, and provider/category pages.
- Add no-risk intent capture only where value is clear.
- Avoid prequalification, credit pulls, approval odds, or lender routing claims
  until traffic and compliance plan justify it.

Batch size:

- One tool/resource cluster at a time.

Acceptance checks:

- Workflow works on mobile and desktop.
- No regulated financial advice or approval implication.

## Dedicated Page Improvement Agent Lane

Create one recurring agent role:

**CreditDoc Page Quality Agent**

Mission:

- Upgrade existing pages and templates into the Local Authority Graph.
- Work in controlled batches.
- Never mix unrelated cleanup, data exports, or deploy fixes into the same
  commit.

Inputs:

- GSC impressions/clicks/CTR.
- Sitemap/page inventory.
- Noindex/archive status.
- Regulator/profile quality queues.
- City guide generation queue.
- Research/report release calendar.

Outputs per batch:

- Candidate CSV.
- Upgrade notes.
- Changed files list.
- Build result.
- Link/noindex validation notes.
- Commit hash.

Rules:

- Do not index weak pages just because they have impressions.
- Do not link to archived/noindexed profiles.
- Do not create negative CFPB lists.
- Do not invent licensing, price, speed, approval, or safety claims.
- Keep every batch small enough to review.

## Execution Phases

### Phase 1: Standards And Instrumentation

Goal:

- Lock the upgrade checklist and candidate selection logic.

Tasks:

1. Create page-family inventory.
2. Build a candidate selector from GSC + sitemap + DB status.
3. Create a batch note template.
4. Define link validation checks.
5. Pick first 10-page pilot batch.

Exit criteria:

- The first batch can be chosen without guessing.

### Phase 2: Research And Profile Graph Links

Goal:

- Use the CFPB report as the first authority node.

Tasks:

1. Add report links from included provider profiles where suitable.
2. Add relevant links from trends pages and research hub.
3. Start provider outreach using the tracker.
4. Track backlinks, corrections, and replies.

Exit criteria:

- Report is connected from research, press, data, and relevant provider/profile
  pages.

### Phase 3: Local Page Upgrade Pilot

Goal:

- Prove the local page standard on a small batch.

Tasks:

1. Select 10 city guides:
   - mix of small towns, regional towns, and pages with impressions.
2. Upgrade internal links, local context, state-rule links, answer links, and
   tool/resource links.
3. Validate no bad provider links.
4. Build and commit.

Exit criteria:

- Each pilot city page has at least 5 meaningful internal links across at least
  3 graph layers.

### Phase 4: City-Category Upgrade Pilot

Goal:

- Make local commercial-intent pages stronger and safer.

Tasks:

1. Select 10 city-category pages from high-value categories.
2. Fix count/coverage wording.
3. Add category-specific local/regulatory context.
4. Link to quality provider profiles and answer/tool assets.

Exit criteria:

- No misleading coverage claims; pages are more useful than a raw directory
  listing.

### Phase 5: Review/Profile Upgrade Batches

Goal:

- Improve the provider entity layer.

Tasks:

1. Select 10-15 high-value profile pages.
2. Confirm category/source/evidence.
3. Add state/regulator/research/local links.
4. Improve metadata through approved data path.
5. Keep questionable pages noindexed or held.

Exit criteria:

- Profiles support city/category pages and research assets with clean entity
  data.

### Phase 6: Scale The System

Goal:

- Repeat without creating operational mess.

Cadence:

- 1 research/report batch per week.
- 2 city/city-category batches per week.
- 2 profile-quality batches per week.
- 1 answer/resource cluster batch per week.

Stop conditions:

- Build failure.
- Links to archived/noindexed profiles.
- YMYL claim risk.
- Dirty unrelated files.
- Data/export process starts touching thousands of files unexpectedly.

## Metrics

Primary:

- GSC clicks.
- CTR by page family.
- Indexed pages with impressions.
- Referring domains to research pages.
- Provider replies/corrections.

Secondary:

- Internal links per upgraded page.
- Pages connected to at least 3 graph layers.
- Noindex/archive link violations.
- Template-level build regressions.

Do not judge the program too early. CreditDoc is a very young YMYL site.
Measure early batches for execution quality first, then evaluate SEO movement
over 21-60 day windows.

## First Batch Recommendation

Start with a small, controlled pilot:

1. CFPB report provider-profile links for the top 10 suitable included
   providers.
2. 10 city guide pages including Amarillo and other small/regional towns with
   good existing local data.
3. 10 city-category pages tied to those cities.
4. 10 answer pages that can link into the same clusters.

This creates the first visible graph cluster instead of isolated improvements.

## Execution Log

### Batch 032: Answer Display Copy Boundary

Date: 2026-05-26  
Implementation commit: `bdd7591b3c` (`feat: soften answer display copy`)

Scope:

- `src/pages/answers/[slug].astro`

What changed:

- Moved the answer page renderer from the generic YMYL copy softener to the
  education-specific softener.
- Applied softened display copy to answer title, H1, meta description,
  breadcrumb, JSON-LD headline/description, key takeaways, section headings,
  section content, FAQ schema, visible FAQ copy, and related-answer cards.
- Preserved raw answer JSON and URLs; this is a render-boundary improvement.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Targeted scan across generated trends output plus answer/trend templates was
  clean for the tracked risky teaser and recommendation phrases.
- `git diff --check` passed.

Notes:

- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 033: Compare Profile Notes

Date: 2026-05-26  
Implementation commit: `01f45822ca` (`feat: soften compare profile notes`)

Scope:

- `src/pages/compare/[slug].astro`

What changed:

- Reframed compare-page profile notes from stored signals that `match your
  needs` to stored signals that may be relevant to user research.
- Neutralized generated comparison reasons that used `better option`.
- Cleaned an awkward generated phrase caused by a previous replacement rule:
  `more sustainable and profile with trust signals to verify`.
- Replaced the local `wins` fallback with `is highlighted`.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Generated compare HTML scan was clean for `match your needs`,
  `better option`, `more sustainable and profile`, `wins`, and `is flagged`;
  remaining hits were source-only replacement-rule literals.
- `git diff --check` passed.

Notes:

- Raw comparison JSON was not edited.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 034: Score Simulator And Checklist Copy

Date: 2026-05-26  
Implementation commit: `62901c345c` (`feat: soften score simulator copy`)

Scope:

- `src/pages/tools/credit-score-simulator.astro`
- `src/pages/resources/credit-report-checklist/index.astro`

What changed:

- Reframed the score simulator CTA away from improving scores faster and toward
  additional credit report context.
- Rewrote the score-change FAQ to avoid timing and point-change promises.
- Reframed the checklist related-answer copy from `help you decide` to
  comparison/learning language.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Generated tools/resources scan was clean for the targeted fast-score,
  point-change, and `help you decide` phrases.
- `git diff --check` passed.

Notes:

- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.
