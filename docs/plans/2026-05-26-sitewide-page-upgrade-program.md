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

### Batch 038: Comparison Guide Label Copy

Date: 2026-05-26
Implementation commit: `1f8873dfb2` (`feat: soften comparison guide labels`)

Scope:

- `src/components/LenderCard.astro`
- `src/pages/answers/index.astro`
- `src/pages/state/[slug].astro`

What changed:

- Replaced the internal lender-card HTML comment `Best For` with `Profile
  signals` so generated source mirrors the already-neutral visible label.
- Reframed answer-index comparison links from top/rate-oriented labels to
  neutral comparison-guide and pricing/terms language.
- Reframed state-page ItemList JSON-LD from `Top Financial Services` to
  `Financial Service Profiles`.
- Replaced the state-page CTA `See all comparisons` with `View comparison
  guides`.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Targeted source/generated scan was clean for `Top Comparison Guides`,
  `Top Financial Services`, `<!-- Best For -->`, `Compare BBB-rated services`,
  `Compare rates & terms`, and `See all comparisons`.
- `git diff --check` passed.

Notes:

- `dist/answers` is not emitted as a static directory in the current build, so
  generated verification covered `dist/state` and `dist/browse` plus source.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 039: City Featured Provider Copy

Date: 2026-05-26
Implementation commit: `498c5e35fe` (`feat: soften city featured provider copy`)

Scope:

- `src/pages/city/[slug].astro`

What changed:

- Kept the strategic city-guide featured-provider section, but reframed it from
  `Top Rated` to `Featured Provider Profiles`.
- Renamed the local featured-provider variable/comment from top-lender language
  to featured-provider language while preserving ordering by stored Google
  rating where available.
- Reframed city page metadata, JSON-LD description, and hero copy away from
  `Honest reviews` / `independently reviewed` claims toward stored ratings,
  BBB context, pricing fields, maps, and local rules where available.
- Preserved maps, local regulations, category sections, browse links, and city
  interlinking.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Targeted source/generated city scan was clean for `Top Rated`, `top lenders`,
  `topLenders`, `Honest reviews`, and `independently reviewed`.
- Generated Amarillo page was checked and now shows `Featured Provider Profiles
  in Amarillo`, stored-rating metadata, and local profile context.
- `git diff --check` passed.

Notes:

- This preserves the bottom-up local SEO strategy while reducing unsupported
  ranking/review claims in city snippets.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 040: 404 Guide Label Copy

Date: 2026-05-26
Implementation commit: `fe86349200` (`feat: soften 404 guide labels`)

Scope:

- `src/pages/404.astro`

What changed:

- Reframed the 404 page quick-link section from `Top Guides` to `Research
  Guides`.
- Reframed visible guide anchor text from `Best ...` labels to neutral guide
  labels.
- Preserved the existing `/best/.../` URLs so no route, sitemap, or internal
  link target changed.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Targeted source/generated 404 scan was clean for `Top Guides`, `Best Credit
  Repair Companies`, `Best Personal Loan Lenders`, `Best Debt Relief
  Companies`, `Best Credit Builder Loans`, and `Best Credit Monitoring
  Services`.
- Generated `dist/404.html` shows `Research Guides` and neutral guide labels.
- `git diff --check` passed.

Notes:

- This is a presentation-only cleanup; URL slugs were intentionally preserved.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 041: Finance Tool Estimate Copy

Date: 2026-05-26
Implementation commit: `f0cef15223` (`feat: soften finance tool estimate copy`)

Scope:

- `src/pages/tools/borrowing-power-quiz.astro`
- `src/pages/tools/debt-payoff-calculator.astro`

What changed:

- Reframed borrowing-quiz copy from personalized matching/qualification
  language toward educational estimates based on user inputs.
- Changed `Find My Borrowing Power` to `Estimate Borrowing Power`.
- Reframed credit-score and DTI result insights to avoid lender certainty,
  savings certainty, and confidence/qualification claims.
- Renamed embedded category data internals from recommendation terminology to
  profile terminology while preserving client-side quiz behavior.
- Reframed debt-avalanche copy from `saves you the most money` to total-interest
  reduction when assumptions are equal.
- Removed a `choose the approach` FAQ phrase from the debt calculator JSON-LD.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Targeted source/generated/client-asset scan was clean for `matched to your
  situation`, `how much you could qualify for`, `Find My Borrowing Power`,
  `Your best estimate`, `saves you the most money`, `Lenders see you as low
  risk`, `Most lenders will consider you`, `could save you thousands`, `shop
  confidently`, `may qualify for lower`, and `choose the approach`.
- `git diff --check` passed.

Notes:

- Calculator behavior was preserved; this was copy and embedded-data naming
  cleanup only.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 042: Homepage Quality Gate Comment

Date: 2026-05-26
Implementation commit: `c242b74355` (`chore: soften homepage quality gate comment`)

Scope:

- `src/pages/index.astro`

What changed:

- Reframed a non-rendered homepage source comment from `Verified providers
  always qualify` to `Verified providers pass the quality gate`.

Verification:

- `git diff --check` passed for the touched file.
- Targeted source scan was clean for `Verified providers always qualify` and
  `qualify` in `src/pages/index.astro`.

Notes:

- No rendered output or calculator/page behavior changed; no full build was
  required for this source-comment-only batch.
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

### Batch 035: Glossary Display Copy

Date: 2026-05-26
Implementation commit: `fefe5cba77` (`feat: soften glossary display copy`)

Scope:

- `src/utils/safe-copy.ts`
- `src/components/GlossaryAppendix.astro`
- `src/pages/glossary.astro`

What changed:

- Added a glossary-specific render-boundary softener that inherits the existing
  educational teaser cleanup.
- Applied glossary softening to standalone glossary JSON-LD and visible
  definition, why-it-matters, and example copy.
- Applied the same boundary to shared glossary appendices used on state, blog,
  wellness, and related educational surfaces.
- Neutralized glossary claims around cheapest loans, `best mortgage deals`,
  bankruptcy chapter superiority, and lower-LTV/rate certainty.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Generated glossary/state/blog/financial-wellness scan was clean for targeted
  glossary claims; remaining hits were source-only replacement-rule literals.
- `git diff --check` passed.

Notes:

- Raw glossary JSON was not edited.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 036: Compare Pricing FAQ Copy

Date: 2026-05-26
Implementation commit: `59acdfa7d6` (`feat: soften compare pricing faq copy`)

Scope:

- `src/pages/compare/[slug].astro`
- `src/utils/safe-copy.ts`

What changed:

- Reframed generated comparison FAQ pricing language from `Which is cheaper`
  and `is cheaper at` to lower listed monthly price and setup-fee context.
- Replaced `currently flags` comparison wording with stored comparison-note
  language.
- Added render-boundary softening for `choose ... only if`,
  `Consumers should choose`, `should choose`, and `superior choice` variants in
  generated comparison summaries.
- Preserved raw comparison JSON and comparison URLs.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Generated compare-page scan was clean for targeted pricing FAQ,
  `currently flags`, `choose ... only if`, `should choose`, and
  `superior choice` phrases; remaining hits were source-only replacement-rule
  literals.
- Sample generated compare page showed the updated FAQ and JSON-LD wording.
- `git diff --check` passed.

Notes:

- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 037: HMDA Research Approval Copy

Date: 2026-05-26
Implementation commit: `99b04fc2f3` (`feat: soften hmda research approval copy`)

Scope:

- `src/pages/research/index.astro`
- `src/pages/research/lending-transparency.astro`

What changed:

- Reframed the research index card from `Which Banks Actually Approve
  Mortgages?` to mortgage application outcomes by bank.
- Replaced `who approves the most` / `biggest approval gaps` teaser wording
  with recorded HMDA outcome context.
- Reframed the lending-transparency page title, metadata, headings, stats, and
  section copy from approval/ranking language toward recorded public-data
  outcome language.
- Clarified that income-based gaps in the public dataset are not predictions
  for individual applicants.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Rendered research/source scan was clean for `Which Banks Actually Approve
  Mortgages`, `Who approves the most`, `highest approval rates`,
  `stronger predictor of approval`, `Mortgage Approval Data by Bank`, and
  related targeted phrases.
- `git diff --check` passed.

Notes:

- The `/research/lending-transparency/` page is not currently present as a
  static file under `dist/research`; source was still updated because the route
  exists and is linked from the research index.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 043: Borrowing Quiz CTA Copy

Date: 2026-05-26
Implementation commit: `bd5f8b052d` (`feat: soften borrowing quiz cta copy`)

Scope:

- `src/pages/credit-guide/[slug]/[category].astro`
- `src/pages/blog/[slug].astro`

What changed:

- Reframed credit-guide quiz CTA copy from eligibility/qualification wording to
  borrowing-range estimate and research-path wording.
- Changed the sidebar CTA heading from `Check Your Options` to
  `Research Your Options`.
- Reframed blog tool teaser copy from `Find out what you qualify for` to
  `Estimate a borrowing range`.
- Preserved the existing borrowing-power quiz URL and city/category routing.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and built worker route-module scans were clean for
  `Find out what you qualify for`, `qualify for based`, `what ... qualify for`,
  and `Check Your Options`.
- Built route-module scan confirmed the replacement borrowing-range and
  research-options copy in blog and credit-guide routes.
- `git diff --check` passed.

Notes:

- Credit-guide dynamic pages are emitted as server route modules under
  `dist/_worker.js/pages/credit-guide/`, not static `dist/credit-guide/`
  files in this build.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 044: Inline Link Title Copy

Date: 2026-05-26
Implementation commit: `409fd29cc6` (`feat: soften inline link titles`)

Scope:

- `src/utils/inline-linker.ts`

What changed:

- Added a render-boundary title softener for inline money-link `title`
  attributes.
- Preserved existing `/best/` URLs, keyword matching, budgets, and visible
  anchor text.
- Reframed generated title attributes from strong comparative or eligibility
  labels toward neutral comparison/context labels:
  - `Best` -> `Comparison`
  - `Cheapest` -> `Lower-Cost`
  - `Easy Approval` -> `Approval Context`
  - `Money Back Guarantee` -> `Refund Terms`
  - `Guarantee` -> `Terms`

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Generated dist scan was clean for old high-risk inline-link title attributes:
  `title="Best...`, `title="Cheapest...`, `title="Easy Approval...`, and
  guarantee-style title attributes.
- Built worker chunk contains the title-softening function, confirming the
  runtime render path is updated.
- `git diff --check` passed.

Notes:

- Raw link-map strings remain in source and compiled utility data because they
  are internal map labels; the emitted anchor title attribute is softened at
  render time.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 045: Credit Guide Local CTA Copy

Date: 2026-05-26
Implementation commit: `e8d48b482d` (`feat: soften credit guide local ctas`)

Scope:

- `src/pages/credit-guide/[slug]/index.astro`
- `src/pages/credit-guide/[slug]/[category].astro`

What changed:

- Reframed the city credit-guide SBA link from `Best SBA lenders serving` to
  `SBA lender profiles serving`.
- Reframed borrowing-power links from `Check your borrowing power` to
  `Estimate borrowing power`.
- Reframed the city HMDA section heading from `Which Banks Approve the Most`
  to `Mortgage Application Outcomes`.
- Reframed HMDA intro copy from lenders `ranked by approval rate` to recorded
  application-outcome context.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and built credit-guide worker route-module scans were clean for:
  `Best SBA lenders serving`, `Check your borrowing power`,
  `Which Banks Approve the Most`, and `Mortgage lenders ranked by approval
  rate`.
- Built worker route-module scan confirmed the replacement SBA profile,
  borrowing estimate, and HMDA application-outcome copy.
- `git diff --check` passed.

Notes:

- Credit-guide dynamic pages are emitted as server route modules under
  `dist/_worker.js/pages/credit-guide/`, not static `dist/credit-guide/`
  files in this build.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 046: Homepage Profile Anchor

Date: 2026-05-26
Implementation commit: `999425abbf` (`feat: rename homepage profile anchor`)

Scope:

- `src/pages/index.astro`

What changed:

- Renamed the homepage profile-highlight jump link target from `#top-picks` to
  `#profile-highlights`.
- Updated the profile-highlight section ID to match the new link.
- Updated the homepage table filtering selector from the stale
  `#top-picks-table tbody` selector to `#profile-highlights tbody`.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and generated homepage scans were clean for `top-picks`,
  `#top-picks`, and `top-picks-table`.
- Generated homepage confirmed `href="#profile-highlights"`,
  `id="profile-highlights"`, and the updated script selector.
- `git diff --check` passed.

Notes:

- This batch removes stale homepage `top-picks` terminology while keeping the
  visible `Profile Highlights` copy and existing table behavior.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 047: Listicle Display Titles

Date: 2026-05-26
Implementation commit: `6d0227d286` (`feat: soften listicle display titles`)

Scope:

- `src/pages/best/[slug].astro`

What changed:

- Added a route-level `softenListicleTitle()` helper for listicle display and
  SEO titles.
- Reframed rendered listicle titles such as `Best`, `Cheapest`, `Top`,
  `Money-Back Guarantee`, and `Lowest` wording toward comparison/profile
  language.
- Updated the rendered page title, H1, breadcrumb text, breadcrumb schema,
  `ItemList` schema, and `Article` headline to use the softened display title.
- Preserved existing slugs, canonical URLs, Supabase source rows, and lender
  ranking order.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and built `/best/[slug]` worker route-module scans confirmed the
  softened display title path for page title, H1, breadcrumbs, and schema.
- Source scan was clean for direct rendered `listicle.title` and
  `listicle.seo_title` references in the listicle route.
- `git diff --check` passed.

Notes:

- `/best/[slug]` is an SSR route emitted under
  `dist/_worker.js/pages/best/_slug_.astro.mjs`; there are no static
  `dist/best/*` files to inspect for this route.
- This batch intentionally leaves raw source listicle JSON/Supabase title
  values untouched and applies YMYL-safe wording at the render boundary.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 048: Homepage Filter Promise

Date: 2026-05-26
Implementation commit: `27b5f2c9d8` (`feat: soften homepage filter promise`)

Scope:

- `src/components/FilterBar.astro`

What changed:

- Reframed the homepage filter helper line from `we'll show the best matches`
  to `we'll show matching directory profiles`.
- Preserved the existing filter form, category options, homepage placement, and
  interaction behavior.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and generated homepage scans were clean for `best matches` and
  confirmed the replacement `matching directory profiles` copy.
- `git diff --check` passed.

Notes:

- This is a shared homepage UI copy cleanup: the filter can still help users
  narrow directory listings without making a recommendation-style promise.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 049: Homepage Filter Heading

Date: 2026-05-26
Implementation commit: `9048dab61a` (`feat: soften homepage filter heading`)

Scope:

- `src/components/FilterBar.astro`

What changed:

- Reframed the homepage filter heading from `Find the Right Service for You` to
  `Find Service Profiles`.
- Preserved the already-softened helper copy and all filter interactions.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and generated homepage scans confirmed `Find Service Profiles` and
  were clean for `Find the Right Service for You`.
- `git diff --check` passed.

Notes:

- This completes the first pass over the homepage filter’s recommendation-like
  heading/helper language.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 050: Category Meta Titles

Date: 2026-05-26
Implementation commit: `771d35800e` (`feat: soften category meta titles`)

Scope:

- `src/pages/categories/[category].astro`

What changed:

- Added `softenCategoryTitle()` to the SSR category route.
- Applied it to category SEO titles before passing them into `BaseLayout`.
- Reframed `Best`, `top`, and `right` title wording toward comparison,
  listed-profile, and relevant-context language.
- Preserved category names, slugs, canonical route behavior, schema names,
  lender ordering, and source category JSON/Supabase values.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and built `/categories/[category]` worker route-module scans confirmed
  `softenCategoryTitle()` and category meta-title usage.
- `git diff --check` passed.

Notes:

- `/categories/[category]` is an SSR route emitted under
  `dist/_worker.js/pages/categories/_category_.astro.mjs`.
- This keeps raw category data intact and applies title cleanup at the render
  boundary.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 051: Blog Related Listicle Titles

Date: 2026-05-26
Implementation commit: `90fd309aba` (`feat: soften blog related listicle titles`)

Scope:

- `src/pages/blog/[slug].astro`

What changed:

- Applied `softenEducationalTeaserCopy()` to related listicle titles loaded for
  the blog sidebar.
- Preserved related listicle slugs, `/best/` links, category lookup behavior,
  and sidebar layout.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and built `/blog/[slug]` worker route-module scans confirmed related
  listicle titles are softened before rendering.
- `git diff --check` passed.

Notes:

- Blog page title, H1, metadata, related posts, FAQ, and key takeaways already
  had safe-copy handling; this batch closes the remaining related-listicle
  sidebar path.
- `/blog/[slug]` is an SSR route emitted under
  `dist/_worker.js/pages/blog/_slug_.astro.mjs`.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 052: Blog Related Guide Titles

Date: 2026-05-26
Implementation commit: `de73dbf8fb` (`feat: soften blog related guide titles`)

Scope:

- `src/pages/blog/[slug].astro`

What changed:

- Applied `softenEducationalTeaserCopy()` to related financial-wellness guide
  titles rendered in the blog sidebar.
- Preserved guide slugs, `/financial-wellness/` links, read-time display, and
  sidebar layout.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and built `/blog/[slug]` worker route-module scans confirmed related
  guide titles are softened before rendering.
- `git diff --check` passed.

Notes:

- This pairs with Batch 051 to cover both related-listicle and related-guide
  title paths in the blog sidebar.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 053: Comparison Display Titles

Date: 2026-05-26
Implementation commit: `6fbf915e3b` (`feat: soften comparison display titles`)

Scope:

- `src/pages/compare/[slug].astro`

What changed:

- Added a `displayComparisonTitle` derived from the existing comparison copy
  softener.
- Applied the softened display title to page metadata, H1, breadcrumb text,
  Article JSON-LD headline, and Breadcrumb JSON-LD.
- Preserved comparison slugs, canonical route behavior, provider cards, FAQ
  provider names, review links, and source comparison data.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source scan confirmed the comparison title render path now uses
  `displayComparisonTitle`.
- Generated comparison page scan confirmed title/H1/breadcrumb/schema used the
  softened display title while stored provider names and review links remained
  unchanged.
- `git diff --check` passed.

Notes:

- Provider names inside cards, FAQ questions, diagnosis cards, and profile links
  intentionally remain exact stored names because those may be business-name
  strings rather than editorial claims.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 054: Guide Link-List Titles

Date: 2026-05-26
Implementation commit: `dc0c6963fc` (`feat: soften guide link-list titles`)

Scope:

- `src/pages/index.astro`
- `src/pages/sitemap.astro`
- `src/pages/categories/[category].astro`

What changed:

- Applied `softenEducationalTeaserCopy()` to homepage financial-wellness guide
  card titles and descriptions.
- Applied `softenEducationalTeaserCopy()` to financial-wellness guide titles
  rendered in the HTML sitemap.
- Added a sitemap-only comparison title display helper built on the existing
  educational teaser softener and used it for comparison links.
- Pre-softened category related wellness-guide titles and descriptions during
  the SSR mapping step before card rendering.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source scans confirmed homepage and sitemap guide/comparison link-list render
  boundaries now use safe-copy helpers.
- Generated `/categories/[category]` worker route-module scan confirmed related
  wellness guide title and description values are pre-softened before rendering.
- `git diff --check` passed.

Notes:

- Broad generated sitemap scans still include exact slugs, provider names, and
  untouched future-copy targets such as some financial-wellness article titles;
  this batch only covers the link-list render boundaries above.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 055: Review Related Guide Copy

Date: 2026-05-26
Implementation commit: `0f635e1a44` (`feat: soften review related guide copy`)

Scope:

- `src/pages/review/[slug].astro`

What changed:

- Added display-only related financial-wellness guide records on provider review
  pages.
- Applied `softenEducationalTeaserCopy()` to related guide titles and
  descriptions before card rendering.
- Applied the same title softener to the "next step" card label when it points
  to the first related guide.
- Preserved guide slugs, runtime fetches, provider profile data, and provider
  names.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and generated `/review/[slug]` worker route-module scans confirmed
  `displayRelatedWellnessGuides` uses safe-copy title/description values before
  rendering.
- `git diff --check` passed.

Notes:

- This closes the provider-review related-guide surface without changing
  DB-backed guide records or review page routing.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 056: Brand And State Related Titles

Date: 2026-05-26
Implementation commit: `974611d992` (`feat: soften brand and state related titles`)

Scope:

- `src/pages/brand/[brand].astro`
- `src/pages/state/[slug].astro`

What changed:

- Added display-only related question and related blog-post arrays on brand
  pages.
- Added the same display-only related question and related blog-post arrays on
  state pages.
- Applied `softenEducationalTeaserCopy()` to runtime related answer/blog titles
  after stripping the `| CreditDoc` suffix from answer titles.
- Preserved Supabase fetches, answer/blog slugs, destination URLs, brand data,
  state data, and provider listings.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and generated `/brand/[brand]` and `/state/[slug]` worker route-module
  scans confirmed related question/article titles render from softened display
  arrays.
- `git diff --check` passed.

Notes:

- This batch only changes related-content labels; it does not change article,
  answer, brand, state, or provider source records.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 057: Blog And Review Related Content Titles

Date: 2026-05-26
Implementation commit: `7d5c6ebd9a` (`feat: soften related content titles`)

Scope:

- `src/pages/blog/[slug].astro`
- `src/pages/review/[slug].astro`

What changed:

- Applied `softenEducationalTeaserCopy()` to related answer titles rendered on
  blog article pages.
- Applied `softenEducationalTeaserCopy()` to related service-research listicle
  titles rendered in the blog sidebar.
- Applied `softenEducationalTeaserCopy()` to related answer titles rendered on
  provider review pages.
- Preserved answer, listicle, and review URLs plus runtime fetch behavior.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and generated `/blog/[slug]` and `/review/[slug]` worker route-module
  scans confirmed the related-content title render expressions use safe-copy.
- `git diff --check` passed.

Notes:

- This batch closes the remaining raw related-answer/listicle render paths found
  in the blog and review route scan.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 058: Answers Index Card Copy

Date: 2026-05-26
Implementation commit: `1ac7b890cd` (`feat: soften answers index card copy`)

Scope:

- `src/pages/answers/index.astro`

What changed:

- Applied `softenEducationalTeaserCopy()` to answer card H1 display values on
  the `/answers/` index.
- Applied the same safe-copy helper to answer card meta descriptions and answer
  summaries before truncation.
- Preserved answer slugs, source row titles, categories, update timestamps, and
  runtime Supabase fetch behavior.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Source and generated `/answers/` worker route-module scans confirmed answer
  card display values are softened before rendering.
- `git diff --check` passed.

Notes:

- This supports the question-cluster strategy by keeping answer index snippets
  safer without changing answer records or URLs.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 059: Educational Title Softener Coverage

Date: 2026-05-26
Implementation commit: `2a359e0845` (`feat: broaden educational title softening`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Broadened `softenEducationalTeaserCopy()` so surfaces already using the
  central helper soften plain `Best` article titles, `Best Free`, `Guaranteed
  Approval`, `Who Actually Approves`, and `Who Approves` patterns.
- Added copy-safe phrasing for rendered teaser descriptions that referenced
  "what lenders actually check", "which lenders approve", "highest acceptance
  rates", and a direct 500-credit-score approval framing.
- Added grammar cleanup for generated "advertised approval claims for..."
  snippets, "advertises certain approval", and "Here are eligibility fields to
  check" after title replacement.
- Preserved source article records, slugs, URLs, runtime fetch behavior, and
  page-specific rendering logic.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Generated `dist/blog/index.html` confirmed representative article-card
  titles and descriptions now render softened text for installment-loan,
  advertised-approval, credit-card, and 500-credit-score examples.
- `git diff --check` passed.

Notes:

- This central-helper change benefits existing surfaces that already call
  `softenEducationalTeaserCopy()`; it does not recategorize or rewrite content
  records.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 060: Wellness Guide List Titles

Date: 2026-05-26
Implementation commit: `7e490ca06a` (`feat: soften wellness guide list titles`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Broadened `softenEducationalTeaserCopy()` for financial-wellness guide titles
  already routed through safe-copy on `/financial-wellness/` and `/sitemap/`.
- Softened rendered list-title phrases including `Easy Approval`, `How to
  Qualify`, `How to Get Approved`, `Better Loan Deal`, `Which Protects You
  Better`, `What Hurts Your Score`, `Where to Apply`, cosigner, payoff-method,
  and credit-monitoring phrasing.
- Added cleanup for replacement joins such as `Cosigner Trade-Offs: Risks`,
  `Loan Cost Comparison`, `Eligibility Fields and Listed Pricing Context`,
  `Protection Trade-Offs`, and `How to Evaluate`.
- Preserved guide records, slugs, URLs, route structure, and page templates.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- `git diff --check` passed.
- Generated `dist/financial-wellness/index.html` and `dist/sitemap/index.html`
  confirmed targeted raw phrases were removed and representative softened
  titles were present.
- Production spot checks returned HTTP 200 for `/`,
  `/credit-guide/amarillo-tx/`, `/categories/fintech/`,
  `/financial-wellness/`, `/sitemap-index.xml`, and `/robots.txt`.

Notes:

- This is a central helper change only; no source records or URL paths were
  changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 061: Remaining Wellness Decision Titles

Date: 2026-05-26
Implementation commit: `70ae41eeaa` (`feat: soften remaining wellness decision titles`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added final safe-copy handling for financial-wellness guide list titles that
  still rendered as direct personal-decision prompts.
- Softened `Which Should You Choose?` to `Trade-Offs to Compare`.
- Softened `What You Actually Need` to `Account Trade-Offs to Compare`.
- Cleaned up `How to Evaluate Your Financial Account Protection?` to
  `Financial Account Protection Evaluation Guide`.
- Preserved source guide records, slugs, URLs, route structure, and page
  templates.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- `git diff --check` passed.
- Generated `dist/financial-wellness/index.html` and `dist/sitemap/index.html`
  confirmed targeted direct-decision phrases were removed and representative
  softened titles were present.

Notes:

- This continues the central-helper strategy from Batches 059 and 060.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 062: Glossary Advice Copy

Date: 2026-05-26
Implementation commit: `e3fffb9f50` (`feat: soften glossary advice copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Broadened `softenGlossaryCopy()` for glossary definitions, why-it-matters
  blocks, and examples already routed through the helper on `/glossary/`.
- Softened direct/advice-like glossary phrases around checking reports, credit
  freeze protection, soft-inquiry shopping, balance-transfer payoff timing,
  minimum-payment descriptions, FCRA/FDCPA/TILA legal-action phrasing, usury
  repayment, FHA MIP, and mortgage refinance break-even framing.
- Preserved glossary records, anchors, JSON-LD term URLs, route structure, and
  page templates.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- `git diff --check` passed.
- Generated `dist/glossary/index.html` confirmed targeted raw phrases were
  removed and representative softened glossary copy was present.
- Production spot checks returned HTTP 200 for `/`,
  `/credit-guide/amarillo-tx/`, `/categories/fintech/`,
  `/financial-wellness/`, `/glossary/`, `/sitemap-index.xml`, and
  `/robots.txt`.

Notes:

- This is a central helper change only; no source glossary records or URL paths
  were changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 063: Remaining Glossary Legal Copy

Date: 2026-05-26
Implementation commit: `52dbf701bc` (`feat: soften remaining glossary legal copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Extended `softenGlossaryCopy()` for the last visible `/glossary/` phrases
  found by the rendered quality scan.
- Softened legal-absolute and result-claim phrases around APR disclosure,
  finance-charge disclosure, Chapter 7 income context, CROA result promises,
  FCRA inaccurate-information handling, TILA APR comparison, and VA mortgage
  backing.
- Corrected the rendered artifact `What to Know in Lending Act` back to
  `Truth in Lending Act` in the glossary helper output.
- Preserved glossary records, anchors, JSON-LD term URLs, route structure, and
  page templates.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- `git diff --check` passed.
- Generated `dist/glossary/index.html` confirmed targeted raw phrases were
  removed and representative softened glossary copy was present.
- Rendered `/glossary/` scan returned no matches for the tracked YMYL phrase
  set used in this batch.

Notes:

- This continues the central helper approach from Batch 062.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 064: Homepage and Blog Need Copy

Date: 2026-05-26
Implementation commit: `f015da3967` (`feat: soften homepage and blog need copy`)

Scope:

- `src/components/FilterBar.astro`
- `src/utils/safe-copy.ts`

What changed:

- Reworded homepage filter helper text and labels from personal-need prompts to
  topic-selection language: `Choose a topic`, `Monitoring focus`, and
  `Help topic`.
- Extended `softenEducationalTeaserCopy()` for blog-card titles and
  descriptions already routed through the helper on `/blog/`.
- Softened `What You Need to Know`, `What Credit Score Do You Need...`,
  `you should use it`, `how to choose`, and `what you need before`.
- Preserved post records, slugs, URLs, the blog route/template, and filter
  category behavior.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- `git diff --check` passed.
- Generated `dist/index.html` and `dist/blog/index.html` confirmed targeted
  raw phrases were removed and representative softened copy was present.

Notes:

- No source post records, slugs, URLs, or filter destination mappings changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 065: Neutral Category Action Labels

Date: 2026-05-26
Implementation commit: `a96860aae7` (`feat: neutralize category action labels`)

Scope:

- `src/content/categories.json`
- `src/components/FilterBar.astro`
- `src/components/Footer.astro`
- `src/pages/compare/[slug].astro`
- `src/pages/answers/[slug].astro`
- `src/pages/credit-guide/[slug]/index.astro`

What changed:

- Replaced shared category display labels `I Need a Loan`, `Get Out of Debt`,
  and `Build My Credit` with neutral labels: `Personal Loans`, `Debt Relief`,
  and `Credit Building`.
- Updated homepage filter options, footer links, category records, comparison
  category cards, answer category labels, and local city guide path labels.
- Preserved category slugs, URLs, route params, city-guide category paths, and
  existing interlinking structure.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- `git diff --check` passed.
- Generated `dist/index.html`, `dist/sitemap/index.html`,
  `dist/city/amarillo-tx/index.html`, and representative comparison output
  confirmed old category action labels were removed and neutral labels were
  present.

Notes:

- Remaining source matches for `Build My Credit` or `Get Out of Debt` are
  provider/product names or quoted marketing context inside lender data and
  were not changed in this batch.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 066: Learn Search Payload Copy

Date: 2026-05-26
Implementation commit: `2d93f7c39e` (`feat: soften learn search payload copy`)

Scope:

- `src/pages/learn.astro`
- `src/utils/safe-copy.ts`

What changed:

- Extended `softenEducationalTeaserCopy()` for education-search payload strings
  already routed through `getEducationSearchData()`.
- Softened embedded `/learn/` search-result titles, descriptions, and key
  takeaways around `you need`, `you should`, `you must`, `must`, `guarantee`,
  `guaranteed`, `proven`, `safest`, and `choose`.
- Reworded the visible `/learn/` Answers Library context link from a
  personal-need phrase to neutral focused-explanation language.
- Added narrow cleanup rules for generated helper artifacts around result
  claims, minimum-payment wording, and approval-claim wording.
- Preserved `/learn/` route/template, search categories, search indexes,
  result URLs, slugs, and source content records.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- `git diff --check` passed.
- Generated `dist/learn/index.html` confirmed targeted raw phrases were
  removed from visible/search payload copy; the only remaining `guaranteed`
  matches were slug/URL strings.
- Generated output confirmed awkward phrases such as
  `specific result claim specific`, `Minimum payments specific result claim`,
  and `can maintain approval` were absent.
- Production spot checks returned HTTP 200 for `/`, `/learn/`, `/blog/`,
  `/credit-guide/amarillo-tx/`, `/categories/fintech/`, `/glossary/`,
  `/sitemap-index.xml`, and `/robots.txt`.

Notes:

- Central helper and page-copy change only; no source guide/post/glossary
  records, URLs, slugs, or search behavior changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 067: Blog and Learn Best-Copy Snippets

Date: 2026-05-26
Implementation commit: `6b52ebc3d3` (`feat: soften blog and learn best-copy snippets`)

Scope:

- `src/pages/blog/index.astro`
- `src/utils/safe-copy.ts`

What changed:

- Reworded the `/blog/` Answer clusters context tile from `when you need a
  focused next question` to `for focused follow-up questions`.
- Extended `softenEducationalTeaserCopy()` with phrase-specific replacements
  for remaining rendered blog/Learn teaser and search-payload copy around
  `best time`, `best budget`, `best defense`, `generally best`, `fits your
  situation best`, and `best-performing`.
- Corrected the helper artifact `Which Free Score results?` to
  `Free Score Comparison`.
- Preserved blog post records, wellness guide records, `/blog/` and `/learn/`
  routes, result URLs, slugs, categories, and search behavior.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- `git diff --check` passed.
- Generated `dist/blog/index.html` and `dist/learn/index.html` confirmed the
  targeted raw phrases were absent.
- Generated output confirmed replacement copy was present, including `Learn
  timing factors for applying`, `which tool has relevant comparison signals`,
  `A useful budget is one you can stick with`, `it is a key defense`, and
  `Free Score Comparison`.

Notes:

- Phrase-specific helper coverage was used instead of a broad lowercase `best`
  replacement because many remaining `best` matches are route slugs, provider
  names, or quoted third-party rankings.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 068: Homepage Filter and Glossary Comparison Copy

Date: 2026-05-26
Implementation commit: `7587c292bc` (`feat: soften homepage filter and glossary comparison copy`)

Scope:

- `src/components/FilterBar.astro`
- `src/utils/safe-copy.ts`

What changed:

- Reworded the homepage filter helper text and category label from `Choose a
  topic` language to neutral `Select a topic` language.
- Extended `softenGlossaryCopy()` so glossary explanatory copy renders `works
  best when` as `is generally most useful when`.
- Preserved homepage filter category values, slugs, form behavior, glossary
  records, anchors, JSON-LD term URLs, and route structure.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Generated `dist/index.html` and `dist/glossary/index.html` confirmed the
  targeted raw phrases were absent and replacement copy was present.
- Rendered stripped-text scan confirmed remaining sitemap `best` hits are
  provider-name contexts and the state `recommendation` hit is a disclaimer, so
  they were not changed.
- Production spot checks returned HTTP 200 for `/`, `/glossary/`, `/sitemap/`,
  `/state/`, `/learn/`, `/blog/`, `/financial-wellness/`,
  `/credit-guide/amarillo-tx/`, `/categories/fintech/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- This batch only changed shared homepage filter copy and glossary helper
  output; no source content records, URLs, slugs, or data mappings changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 069: Homepage Provider Action Step

Date: 2026-05-26
Implementation commit: `07f0594021` (`feat: soften homepage provider action step`)

Scope:

- `src/pages/index.astro`

What changed:

- Reworded the fourth homepage `How It Works` step from `Apply` to `Visit`.
- Replaced sign-up/free-consultation action language with neutral provider-site
  research language: `Use the provider website to review current terms,
  disclosures, and intake steps directly.`
- Preserved homepage layout, step count, icons, links, category sections,
  route structure, and provider/category data.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Generated `dist/index.html` confirmed `Apply`, `Click through to the company
  website`, `sign up`, and `free consultations` were absent from the homepage
  step copy.
- Generated `dist/index.html` confirmed the replacement `Visit` step and
  provider-site research wording were present.

Notes:

- This batch only changed visible homepage workflow copy; no source content
  records, URLs, slugs, or data mappings changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 070: Comparison Refund-Term Claim Copy

Date: 2026-05-26
Implementation commit: `680284aaea` (`feat: soften comparison refund-term claim copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Extended `softenYmylCopy()` with phrase-specific coverage for comparison
  summaries, JSON-LD descriptions, visible FAQ answers, and comparison-note
  snippets that referenced provider refund guarantees, result-confidence
  language, or customer-protection claims.
- Reworded variants such as `50-point credit score increase guaranteed or full
  money back`, `score-increase guarantee`, `stronger guarantee`, `guarantee
  demonstrates confidence in results`, and `protects customers from paying for
  undelivered services` into provider-stated refund-term context.
- Added final-pass cleanup for the generated artifact `with published refund
  terms results with a published refund term`.
- Preserved comparison routes, slugs, lender records, pricing fields, FAQ
  structure, JSON-LD structure, and comparison page layout.

Verification:

- `git diff --check` passed.
- Direct helper checks confirmed the targeted guarantee/result-confidence
  phrases soften before rendering.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Generated comparison pages confirmed the targeted raw phrases were absent and
  provider-stated refund-term replacements were present for
  `/compare/continental-credit-vs-cosmo-credit-repair/`,
  `/compare/the-credit-repairmen-vs-cosmo-credit-repair/`, and
  `/compare/ecreditadvisor-vs-cosmo-credit-repair/`.
- Broader `dist/compare` scan confirmed no remaining matches for the targeted
  guarantee/result-confidence phrases.
- Production spot checks returned HTTP 200 for
  `/compare/continental-credit-vs-cosmo-credit-repair/`,
  `/compare/the-credit-repairmen-vs-cosmo-credit-repair/`,
  `/compare/ecreditadvisor-vs-cosmo-credit-repair/`, `/learn/`, `/blog/`,
  `/credit-guide/amarillo-tx/`, `/categories/fintech/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Helper-only change; no source comparison/lender records, routes, slugs, or
  data mappings changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 071: City Card Urgency Copy

Date: 2026-05-26
Implementation commit: `b94d5b0922` (`feat: soften city card urgency copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Extended `softenYmylCopy()` with phrase-specific coverage for city and
  browse provider-card descriptions and profile signals that used high-pressure
  urgency, application-timing, same-day funding, no-credit-check, or
  qualification-exclusion wording.
- Reworded variants such as `fast approval`, `quick cash`, `fast title loans`,
  `quick personal loans`, `same-day or next-business-day funding`, `need
  emergency cash within days`, `need funds quickly`, `no credit check needed`,
  `cannot qualify for traditional personal loans`, and `have exhausted other
  options` into provider-profile or verification-oriented context.
- Added final-pass cleanup for generated artifacts such as `short-term cash
  access access`, `who need listed funding timing`, `need emergency cash
  quickly`, `no other financing alternatives`, and `for short-term cash access
  for short-term cash research`.
- Preserved source lender records, city/browse routes, slugs, rankings,
  category mappings, card layout, ratings, and links.

Verification:

- `git diff --check` passed.
- Direct helper checks confirmed targeted urgency, no-credit-check, timing, and
  qualification phrases soften before rendering.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Generated city/browse pages confirmed targeted raw phrases were absent from
  sampled provider-card copy and replacement wording was present for
  `/city/tampa-fl/`, `/city/hammond-in/`, `/city/houston-tx/`,
  `/city/norcross-ga/`, `/city/nashville-tn/`, `/city/tempe-az/`,
  `/browse/emergency-cash/houston-tx/`, `/browse/pawn-shops/tampa-fl/`, and
  `/browse/pawn-shops/virginia-beach-va/`.
- Broader `dist/city` and `dist/browse` scan confirmed no remaining matches
  for the targeted generated-artifact phrases. Remaining sampled hits were
  provider/business names such as `Quick Cash Pawn` or `TN Quick Cash`, not
  body-copy claims.
- Production spot checks returned HTTP 200 for `/city/tampa-fl/`,
  `/city/hammond-in/`, `/city/houston-tx/`, `/city/tempe-az/`,
  `/browse/emergency-cash/houston-tx/`, `/browse/pawn-shops/tampa-fl/`,
  `/learn/`, `/blog/`, `/categories/fintech/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Helper-only change; no source lender records, routes, slugs, rankings,
  category mappings, or card layout changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 072: Business Funding Card Claims

Date: 2026-05-26
Implementation commit: `c47a84759e` (`feat: soften business funding card claims`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Extended `softenYmylCopy()` with phrase-specific coverage for provider-card
  descriptions and profile signals that used business-funding speed,
  approval-timing, 0% interest, limited-documentation, collateral, rate, or
  marketplace-matching claims.
- Reworded variants such as `quick approval`, `quick approvals`,
  `24-hour approvals`, `minimal documentation`, `competitive rates`,
  `0% interest business funding`, `without requiring collateral or financial
  statements`, `funding marketplace that matches small businesses with`, and
  `fast business funding solutions` into provider-profile or
  verification-oriented context.
- Added final-pass cleanup for generated artifacts such as `business-funding
  profile details solutions`, nested `advertised advertised 0% interest`
  output, `a advertised 0% interest`, and `find rate claims to verify`.
- Preserved source lender records, city/browse routes, slugs, rankings,
  category mappings, card layout, ratings, and links.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Generated city/browse pages confirmed targeted raw phrases were absent from
  sampled provider-card copy and replacement wording was present for
  `/browse/business-loans/charlotte-nc/`, `/city/charlotte-nc/`,
  `/browse/mortgages/baltimore-md/`, `/browse/pawn-shops/national-city-ca/`,
  `/city/national-city-ca/`, and `/city/south-gate-ca/`.
- Broader `dist/city` and `dist/browse` scan confirmed no remaining matches
  for the targeted business-funding/card-claim raw phrases.
- Production spot checks returned HTTP 200 for
  `/browse/business-loans/charlotte-nc/`, `/city/charlotte-nc/`,
  `/browse/mortgages/baltimore-md/`, `/browse/pawn-shops/national-city-ca/`,
  `/browse/check-cashing/houston-tx/`, `/city/los-angeles-ca/`, `/learn/`,
  `/blog/`, `/categories/fintech/`, `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Helper-only change; no source lender records, routes, slugs, rankings,
  category mappings, or card layout changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.
