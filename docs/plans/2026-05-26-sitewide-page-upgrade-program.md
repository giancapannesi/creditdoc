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

### Batch 120: Cross-Page Educational Residue Normalization

Date: 2026-05-27
Implementation commit: `6245f10fc7` (`fix: normalize cross-page educational residue`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared render-time cleanup for residual educational, glossary, learn,
  wellness, course, blog, resource, and comparison phrases found in generated
  output.
- Normalized awkward replacement artifacts including `Financial Account
  Protection net`, `has more listed context a judgment`, `makes overspending
  easy to overspend`, `claimed certain by`, `it can be useful to Try`,
  `more listed context-cost context`, `listed context-cost context`, and
  `advertised approval claim to verify`.
- Reframed those phrases into neutral account-protection, legal-reference,
  overspending-risk, listed-cost, judgment, review, and approval-claim
  language.
- Preserved source comparison records, source wellness-guide records, lender
  records, city/category records, slugs, route generation, cards, tables, and
  layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Focused rendered scan across `dist/compare`, `dist/financial-wellness`,
  `dist/learn`, `dist/glossary`, `dist/blog`, `dist/courses`, and
  `dist/resources` returned zero matches for the targeted Batch 120 phrase set.
- Production spot checks returned HTTP 200 for `/`, `/learn/`,
  `/financial-wellness/`, `/glossary/`,
  `/blog/are-guaranteed-approval-personal-loans-real-the-truth/`,
  `/courses/credit-fundamentals/avoiding-scams-and-predatory-lending/`,
  `/compare/self-credit-builder-vs-first-progress-platinum-elite/`,
  `/compare/dickmann-tax-group-vs-grt-financial/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-only cleanup; no source comparison, source wellness guide, lender,
  city, or category records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 121: Comparison Listed-Context Residue Normalization

Date: 2026-05-27
Implementation commit: `66f051d864` (`fix: normalize comparison listed-context residue`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared render-time cleanup for comparison pages where earlier
  safe-copy passes left duplicated listed-context phrasing and remaining hard
  risk language.
- Normalized phrases including `more listed cost context`, `lists more listed
  cost context`, `offers more listed cost context`, `provides more listed
  consumer-protection context`, `stronger regulatory compliance`,
  `perpetuates repeat-borrowing cycles`, `predatory APRs`, `predatory
  304%-688% APRs`, `designed to encourage costly rollovers`, `costly
  rollovers`, `proven credit repair`, `stronger accreditation`, and `more
  practical benefits`.
- Reframed those phrases into cost-context, consumer-protection-context,
  regulatory-context, high-listed-APR, rollover-risk, feature-context, and
  accreditation-context wording.
- Preserved source comparison records, lender records, pricing values, ratings,
  route slugs, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Focused rendered `dist/compare` scan returned zero matches for the targeted
  Batch 121 phrase set.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/brigit-vs-ace-cash-express/`,
  `/compare/brigit-vs-advance-america-montebello/`,
  `/compare/brigit-vs-advance-america-oklahoma-city/`,
  `/compare/ace-cash-express-terrytown-vs-ace-cash-express-miami-fl/`,
  `/compare/dickmann-tax-group-vs-lakeview-law-group/`,
  `/compare/credit-saint-vs-safeport-law/`,
  `/compare/safeport-law-vs-the-credit-people/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 139: Course Module Render Artifact Cleanup

Date: 2026-05-27
Implementation commit: `c55b2a579d` (`fix: clean course module render artifacts`)

Scope:

- `src/pages/courses/credit-fundamentals/[slug].astro`
- `src/utils/safe-copy.ts`

What changed:

- Removed leaked course authoring notes such as `Canva search` from module
  previews and full lesson content before rendering.
- Removed raw horizontal-rule artifacts from rendered module lesson content.
- Sent module meta descriptions through the shared educational safe-copy path.
- Cleaned course CTA/quiz wording around stale verified-lender phrasing,
  broad scam wording, automatic deletion claims, score-increase promises, and
  complaint-agency overclaim framing.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered course scans returned no matches for `Canva search`,
  `listed refund term a specific score increase`, `MOST effective for
  resolving complaints`, `top-rated credit repair companies`, `Search verified
  lenders in your state`, `What is ALWAYS a scam`, `Forces bureaus to delete
  anything`, `automatically removes negative items`, and `before they must
  remove the item`.
- Local static route checks returned HTTP 200 for `/courses/credit-fundamentals/`,
  `/courses/credit-fundamentals/credit-repair-diy-vs-hiring-help/`,
  `/courses/credit-fundamentals/avoiding-scams-and-predatory-lending/`,
  `/city/amarillo-tx/`, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/courses/credit-fundamentals/`,
  `/courses/credit-fundamentals/credit-repair-diy-vs-hiring-help/`,
  `/courses/credit-fundamentals/avoiding-scams-and-predatory-lending/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Course render/safe-copy cleanup only; no raw course markdown, lender, city,
  category, comparison, blog, glossary, or generated inventory records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 138: Static FAQ Claim and Outcome Softening

Date: 2026-05-27
Implementation commit: `b605275bff` (`fix: soften faq claims`)

Scope:

- `src/pages/faq.astro`

What changed:

- Softened FAQ claims around CreditDoc purpose, update cadence, ratings
  visibility, correction review timing, credit-repair outcomes,
  credit-repair pricing/timing, self-repair, and debt-relief framing.
- Replaced deterministic or promissory language with research-oriented,
  provider-data, and context-based phrasing.
- FAQ JSON-LD uses the same cleaned answers because it is generated from the
  shared `faqs` array.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted source and rendered FAQ scans returned no matches for the cleaned
  residue phrases.
- Local static route checks returned HTTP 200 for `/faq/`, `/blog/`,
  `/glossary/`, `/city/amarillo-tx/`, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/faq/`, `/blog/`,
  `/glossary/`, `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Static FAQ copy cleanup only; no raw lender, city, category, comparison,
  blog, glossary, or generated inventory records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 137: Blog and Glossary Outcome Copy Softening

Date: 2026-05-27
Implementation commit: `cda882eca5` (`fix: soften blog and glossary outcome copy`)

Scope:

- `src/pages/blog/index.astro`
- `src/utils/safe-copy.ts`

What changed:

- Added a blog-index display softener so teaser titles and descriptions avoid
  hard approval, scam, and outcome phrasing while preserving the underlying
  article records and slugs.
- Softened glossary display copy for deterministic credit-score, approval, and
  rate examples.
- Replaced point-change and exact mortgage-score outcome examples with
  context-based wording.
- Cleaned second-order glossary grammar artifacts from earlier safe-copy passes,
  including lowercase sentence starts and phrases such as `Every lender are
  required`, `they is generally required`, and `we'll promise removal`.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/blog` and `dist/glossary` scans returned no matches for the
  targeted residual phrases, including hard approval phrases, `red flags`,
  deterministic score-change claims, `100-point difference`, `Every lender are
  required`, `they is generally required`, and `claimed certain`.
- Local static route checks returned HTTP 200 for `/blog/`, `/glossary/`,
  `/city/amarillo-tx/`, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/blog/`, `/glossary/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-time copy cleanup only; no source blog, glossary, lender, comparison,
  city, or category records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 136: Residual Comparison and Provider-Card Claim Cleanup

Date: 2026-05-27
Implementation commit: `78ffaec0c5` (`fix: soften residual comparison and card claims`)

Scope:

- `src/components/LenderCard.astro`
- `src/pages/compare/[slug].astro`

What changed:

- Added provider-card render-time cleanup for lingering city and browse copy
  residue.
- Replaced remaining no-credit-check, minimal-credit, flexible-approval,
  same-day-cash, fast-loan, success-rate, budget-conscious, track-record, and
  credit-improvement phrases with eligibility, timing, listed-cost,
  provider-stated, and review-context wording.
- Added comparison-page render-time cleanup for summaries, meta descriptions,
  JSON-LD, FAQ answers, and research notes.
- Replaced `starts at just`, `profiled for those with poor or no credit
  history`, `faster credit rebuilding`, `accessibility and affordability`,
  `monthly advantage`, unsupported reputation/review-volume phrasing,
  `professional credit-building tools`, `free tier is appealing`, `red flags`,
  `critical security issues`, `verified ConsumerAffairs reviews`, client-volume
  claims, and broad reliability/consumer-protection conclusions.
- Preserved source comparison records, source lender records, pricing values,
  route slugs, cards, maps, tables, FAQs, city pages, and browse pages.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/city`, `dist/browse`, and `dist/compare` scan returned no
  matches for the targeted Batch 136 provider-card and comparison residue
  phrases.
- Local static checks returned HTTP 200 for `/`, `/city/doraville-ga/`,
  `/city/virginia-beach-va/`, `/browse/pawn-shops/memphis-tn/`,
  `/browse/emergency-cash/fresno-ca/`,
  `/browse/emergency-cash/tampa-fl/`,
  `/browse/emergency-cash/cleveland-oh/`,
  `/browse/emergency-cash/orlando-fl/`,
  `/browse/pawn-shops/san-diego-ca/`,
  `/browse/credit-repair/phoenix-az/`,
  `/browse/banking/san-diego-ca/`,
  `/compare/kikoff-vs-discover-it-secured/`,
  `/compare/national-credit-care-vs-elevate-my-scores/`,
  `/compare/brigit-vs-advance-america-hialeah-fl/`,
  `/compare/xperia-credit-solutions-vs-elevate-my-scores/`,
  `/compare/xperia-credit-solutions-vs-national-credit-care/`,
  `/compare/smartcredit-vs-wallethub/`,
  `/compare/national-debt-relief-vs-lakeview-law-group/`, and
  `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/kikoff-vs-discover-it-secured/`,
  `/compare/xperia-credit-solutions-vs-national-credit-care/`, and
  `/sitemap-index.xml`.

Notes:

- Render-only cleanup; no source comparison, lender, city, or category records
  changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 135: Provider Card and Comparison Claim Residue Cleanup

Date: 2026-05-27
Implementation commit: `3d53c7b4d0` (`fix: soften provider and comparison claim residue`)

Scope:

- `src/components/LenderCard.astro`
- `src/pages/compare/[slug].astro`

What changed:

- Added provider-card render-time cleanup for city and browse pages where raw
  descriptions still produced awkward or over-assertive copy.
- Replaced `option to compare Capital Inc provides`, funding/approval timing
  claims, aggressive credit-repair wording, expedited dispute-resolution
  claims, credit-bureau representative claims, 90-120 day results claims,
  awkward no-credit-check phrases, and credit-score improvement wording.
- Added comparison-page render-time cleanup for summaries, meta descriptions,
  JSON-LD, FAQ answers, and research notes.
- Replaced `stored outcome fields`, `stored debt-management context`,
  `27-year track record`, `free financial education`, `accuracy and
  affordability make it`, `strong national reputation`, `higher verified
  customer ratings`, `resolved over $1 billion in debt`, `free debt-free
  assessment`, `faster 3-year potential timelines`, `more suitable for`,
  `last-resort settlement option`, `regulatory penalties`, `unsuitable for`,
  and timeline/outcome overclaims.
- Preserved source comparison records, source lender records, pricing values,
  route slugs, cards, maps, tables, FAQs, city pages, and browse pages.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/city`, `dist/browse`, and `dist/compare` scan returned no
  matches for the targeted provider-card and comparison residue phrases.
- Local static checks returned HTTP 200 for `/`, `/city/norcross-ga/`,
  `/browse/credit-repair/dallas-tx/`, `/browse/emergency-cash/kansas-city-mo/`,
  `/browse/emergency-cash/tampa-fl/`,
  `/compare/incharge-debt-solutions-vs-detroit-wealth-club/`,
  `/compare/transunion-vs-boost-my-fico-scores/`,
  `/compare/cambridge-credit-counseling-vs-clarifi/`,
  `/compare/credit-supreme-credit-repair-miami-fix-credit-fast-miami-fl-vs-the-credit-people/`,
  and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/incharge-debt-solutions-vs-detroit-wealth-club/`, and
  `/sitemap-index.xml`.

Notes:

- Render-only cleanup; no source comparison, lender, city, or category records
  changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 122: Emergency-Cash Comparison Residue Normalization

Date: 2026-05-27
Implementation commit: `a835d70ba2` (`fix: normalize emergency-cash comparison residue`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared render-time cleanup for emergency-cash comparison pages where
  previous safe-copy passes left hard cost/risk phrasing and awkward listed
  context wording.
- Normalized phrases including `extremely expensive`, `unless no alternatives
  exist`, `notable avoided unless`, `makes it with more listed context`,
  `significantly more expensive and predatory`, and `and predatory`.
- Reframed those phrases into high listed borrowing cost, available-alternative,
  listed-context, and high-cost lending risk wording.
- Preserved source comparison records, lender records, pricing values, ratings,
  route slugs, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Focused rendered `dist/compare` scan returned zero matches for the targeted
  Batch 122 phrase set.
- Targeted rendered checks confirmed replacement language on
  `/compare/brigit-vs-advance-america-oklahoma-city/` in JSON-LD, summary,
  research note, and FAQ body.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/brigit-vs-advance-america-oklahoma-city/`,
  `/compare/ace-cash-express-terrytown-vs-ace-cash-express-miami-fl/`,
  `/compare/brigit-vs-advance-america-montebello/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 123: Listed-Context Residue Normalization

Date: 2026-05-27
Implementation commit: `902784f11c` (`fix: normalize listed-context residue`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared render-time cleanup for remaining `more listed context` residue
  across comparison, blog index, course, learn, and financial-wellness output.
- Normalized phrases including `with more listed context`, `has more listed
  context`, `more listed context for`, `more listed value context`, `more
  listed risk context`, `more listed profile context`, `more listed comparison
  context`, `more listed regulatory context`, `more listed feature context`,
  `more listed accreditation context`, `more listed risk-context`, and `more
  listed-cost context`.
- Reframed remaining `better overall choice` language to `stored comparison
  pick`.
- Added cleanup for second-order grammar artifacts including `profile with more
  supporting context with`, `has more supporting context a court judgment`,
  `motivation has more supporting context`, `math has more supporting context`,
  and related course/blog title residue.
- Preserved source comparison records, education records, lender records,
  pricing values, ratings, route slugs, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Focused rendered scan across `dist/compare`, `dist/blog`, `dist/courses`,
  `dist/learn`, and `dist/financial-wellness` returned zero matches for the
  targeted Batch 123 phrase set.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/smartcredit-vs-lookout/`,
  `/compare/kikoff-vs-opensky-secured-credit-card/`,
  `/courses/credit-fundamentals/managing-debt-effectively/`,
  `/courses/credit-fundamentals/know-your-rights/`, `/blog/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-only safe-copy cleanup; no source comparison, education, lender, city,
  or category records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 125: Comparison FAQ Fallback Copy Consolidation

Date: 2026-05-27
Implementation commit: `9b33d02b47` (`fix: consolidate comparison faq fallback copy`)

Scope:

- `src/pages/compare/[slug].astro`

What changed:

- Consolidated comparison FAQ answers when both profiles lack a recurring
  monthly subscription fee.
- Consolidated refund-term FAQ answers when neither profile lists a refund term
  in the stored comparison data.
- Preserved provider-specific setup-fee context and one-provider refund-term
  details when only one side has data.
- Trimmed trailing punctuation from provider-stated refund details to prevent
  double periods in rendered FAQs and FAQ JSON-LD.
- Preserved source comparison records, lender records, pricing values, ratings,
  route slugs, cards, tables, schema shape, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed after a second build with the punctuation cleanup.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan across `dist/compare` returned zero matches for
  duplicate monthly-subscription fallback text, duplicate missing-refund-term
  fallback text, and listed-refund double-period residue.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/creditassociates-vs-new-era-debt-solutions/`,
  `/compare/cambridge-credit-counseling-vs-greenpath-financial-wellness/`,
  `/compare/greenlight-financial-vs-boost-credit-101/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-template cleanup; no source comparison, education, lender, city, or
  category records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 127: Lender Card Profile Signal Softening

Date: 2026-05-27
Implementation commit: `385d0feb52` (`fix: soften lender card profile signals`)

Scope:

- `src/components/LenderCard.astro`

What changed:

- Added provider-card-specific render-time softening for lender descriptions and
  profile signals.
- Reframed visible card phrases such as `guaranteed returns`, `without
  predatory lending`, and `predatory practices` into provider-stated,
  lending-cost, and verification-context language.
- Improved shared card output for city pages and category browse pages without
  changing lender source records, city data, category data, comparison pages, or
  educational content.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted profile-signal rendered scan across `dist/city` and `dist/browse`
  returned zero card matches for raw phrases: `guaranteed returns`,
  `guaranteed return`, `without predatory lending`, `without the predatory
  practices`, `predatory practices`, and `predatory lending practices`.
- Positive rendered checks confirmed replacement language including `stated
  return terms to verify`, `lending-cost context to verify`, `lending-cost and
  title-loan comparison context to verify`, and `high-cost lending practices`.
- Production spot checks returned HTTP 200 for `/`, `/city/irvine-ca/`,
  `/city/arlington-tx/`, `/browse/banking/wilmington-de/`,
  `/browse/free-help/birmingham-al/`, `/browse/bankruptcy/philadelphia-pa/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.
- A first check against `/browse/credit-unions/arlington-tx/` returned 404
  because that route is not generated in `dist`; it was replaced with generated
  browse-route checks above.

Notes:

- Render-component cleanup; no source lender, city, category, comparison, or
  education records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 134: Comparison Residual Grammar and Outcome Cleanup

Date: 2026-05-27
Implementation commit: `382300397d` (`fix: clean comparison residual grammar claims`)

Scope:

- `src/pages/compare/[slug].astro`

What changed:

- Added display-time cleanup for remaining comparison grammar and outcome
  residue in summaries, meta descriptions, JSON-LD, FAQ answers, and visible
  research notes.
- Cleaned phrases including `more consumer comparison context profile details`,
  `is more listed`, `are more listed`, `profile details seeking`,
  `average {n}-point increase`, `average {n}-point score lift`,
  `reporting average {n}-point score improvements for engaged users`,
  `undercuts`, `delivering substantially more cost context`, `significantly
  higher APRs`, `loyal customers`, `raises concerns`, `no-interest or fees`,
  `genuinely free`, and `lower higher listed pricing`.
- Kept output focused on stored profile fields, listed-cost context,
  provider-stated claims to verify, and review/risk context.
- No raw lender, city, category, comparison, or education records changed.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered comparison residue scan across `dist/compare` returned
  zero matches for the Batch 134 raw phrases.
- Local static route checks returned HTTP 200 for `/`, selected comparison
  pages, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/`,
  `/credit-guide/amarillo-tx/`,
  `/compare/dovly-vs-credit-karma-credit-repair/`, and
  `/sitemap-index.xml`.

Notes:

- Render-template cleanup; no source data records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 133: Comparison Approval and Outcome Claim Softening

Date: 2026-05-27
Implementation commit: `f490bff142` (`fix: soften comparison approval and outcome claims`)

Scope:

- `src/pages/compare/[slug].astro`

What changed:

- Added display-time softening for comparison wording that could read as a
  CreditDoc recommendation, approval claim, price superiority claim, or
  credit-score outcome claim.
- Reframed `choose {provider} if you need`, `directly builds credit scores`,
  `essential for actual credit score building`, `direct credit history
  establishment`, `87% approval rate`, `significantly cheaper`,
  `genuinely free comprehensive tier`, `no paywall required`, `meaningful
  features`, and `makes it accessible to users`.
- Kept comparison output focused on stored profile fields, listed-cost context,
  provider-stated claims to verify, and credit-profile context to review.
- No raw lender, city, category, comparison, or education records changed.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered residue scan across `dist/compare` returned zero matches
  for the Batch 133 raw phrases.
- Positive rendered checks confirmed replacement language on representative
  comparison pages, including Greenlight vs OpenSky and Dovly vs WalletHub.
- Local static checks returned HTTP 200 for `/`,
  `/compare/greenlight-financial-vs-opensky-secured-credit-card/`,
  `/compare/dovly-vs-wallethub/`,
  `/compare/dovly-vs-credit-karma-credit-repair/`,
  `/compare/brigit-vs-ace-cash-express/`, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/`,
  `/credit-guide/amarillo-tx/`,
  `/compare/greenlight-financial-vs-opensky-secured-credit-card/`, and
  `/sitemap-index.xml`.

Notes:

- Render-template cleanup; no source data files were changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 132: Comparison Overclaim Residue Cleanup

Date: 2026-05-27
Implementation commit: `5874a3aa45` (`fix: soften comparison overclaim residue`)

Scope:

- `src/pages/compare/[slug].astro`

What changed:

- Added display-time softening for remaining comparison overclaim and loaded
  wording in summaries, meta descriptions, JSON-LD, FAQs, and research notes.
- Cleaned phrases including `devastating payday loan APRs`, `traps borrowers in
  high-cost repeat-borrowing cycles`, `creates repeat-borrowing cycles`,
  `saving borrowers hundreds of dollars`, `signaling serious customer
  dissatisfaction`, `need lower interest rates to make real progress`,
  `affordable short-term funds`, and `higher high-cost lending risk context`.
- Cleaned awkward second-order comparison conclusions including `lower in
  listed-cost context and with more risk context` and `profile with more context
  for long-term financial-health context`.
- No raw lender, city, category, comparison, or education records changed.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered residue scan across `dist/compare` returned zero matches
  for the Batch 132 raw phrases.
- Positive rendered checks confirmed replacement language including `very high
  payday-loan APRs`, `repeat-borrowing risk to review`, `showing materially
  different listed-cost context`, `adding review-context risk to verify`, `are
  comparing lower-interest repayment options`, `lower-listed-cost short-term
  funds`, `higher lending-cost risk context`, and long-term financial-health
  context to review.
- Local static checks returned HTTP 200 for `/`,
  `/compare/brigit-vs-ace-cash-express/`,
  `/compare/brigit-vs-advance-america-claymont/`,
  `/compare/incharge-debt-solutions-vs-detroit-wealth-club/`,
  `/compare/incharge-debt-solutions-vs-clarifi/`,
  `/compare/ecreditadvisor-vs-sky-blue-credit/`, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/`,
  `/credit-guide/amarillo-tx/`,
  `/compare/brigit-vs-ace-cash-express/`, and `/sitemap-index.xml`.

Notes:

- Render-template cleanup; no source data files were changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 131: Second-Order Render Residue Cleanup

Date: 2026-05-27
Implementation commit: `e46834e3d3` (`fix: clean second-order render residue`)

Scope:

- `src/pages/compare/[slug].astro`
- `src/components/LenderCard.astro`

What changed:

- Cleaned second-order comparison and provider-card grammar created by prior
  display-time safety rewrites.
- Normalized comparison residue including `more profile context and
  competitive`, `a more profile context and accessible service`, `more profile
  context-cost`, `more package context context`, and `more listed-cost`.
- Normalized provider-card residue including `more listed-cost`, `no fee unless
  you have more listed context`, and `with with published refund terms
  consultations`.
- No raw lender, city, category, comparison, or education records changed.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered residue scan across `dist/compare`, `dist/browse`,
  `dist/city`, and `dist/review` returned zero matches for the Batch 131
  residue phrases.
- Positive rendered checks confirmed the replacement language appears on the
  affected comparison and browse pages.
- Local static checks returned HTTP 200 for `/`,
  `/compare/greenlight-financial-vs-capital-one-platinum-secured/`,
  `/compare/credit-saint-vs-the-credit-pros/`,
  `/compare/ace-cash-express-miami-fl-vs-advance-america-missouri-city/`,
  `/compare/self-credit-builder-vs-chime/`,
  `/browse/bankruptcy/denver-co/`, `/browse/bankruptcy/indianapolis-in/`,
  `/browse/bankruptcy/san-diego-ca/`, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-template/component cleanup; no source data files were changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 130: Comparison Listed-Residue Cleanup

Date: 2026-05-27
Implementation commit: `f5078c230c` (`fix: normalize comparison listed residue`)

Scope:

- `src/pages/compare/[slug].astro`

What changed:

- Added comparison-page display-time cleanup for residual `more listed ...`,
  `with more listed`, `has more listed`, and `all more listed to` grammar.
- Normalized affected comparison summaries, meta descriptions, JSON-LD FAQ
  answers, and visible research notes without rewriting raw comparison data.
- Preserved advisory-neutral comparison framing: profile context, stored
  fields, public data, and verifiable signals rather than recommendations.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan across `dist/compare` returned zero matches for
  generic `more listed ...`, `has more listed`, `with more listed`, and `all
  more listed to` residue.
- Regression scan across `dist/city`, `dist/browse`, `dist/compare`, and
  `dist/review` returned zero matches for the previously fixed hard-claim and
  duplicated-grammar artifacts in scope.
- Local static checks returned HTTP 200 for `/`, representative comparison
  pages, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/creditassociates-vs-new-era-debt-solutions/`,
  `/compare/accredited-debt-relief-vs-lakeview-law-group/`,
  `/compare/the-credit-pros-vs-the-credit-people/`,
  `/compare/dovly-vs-cbc-companies/`, `/credit-guide/amarillo-tx/`, and
  `/sitemap-index.xml`.

Notes:

- Render-template cleanup; no source lender, city, category, comparison, or
  education records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 129: Lender Card Residual Grammar Cleanup

Date: 2026-05-27
Implementation commit: `0ce68411b3` (`fix: clean lender card residual grammar`)

Scope:

- `src/components/LenderCard.astro`

What changed:

- Added final provider-card cleanup for duplicate `short-term short-term`
  wording in visible city and browse card profile signals.
- Normalized `short-term cash access shortfalls` to `short-term cash
  shortfalls`.
- Cleaned second-order high-cost wording such as `high-cost lending risk
  context lending`.
- Restored remaining proper-name contexts damaged by earlier broad `superior`
  replacements: `Superior Business` and `Superior Mercado`.
- Preserved source lender, city, category, comparison, and education records.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan across `dist/city` and `dist/browse` returned zero
  matches for `short-term short-term`, `short-term cash access shortfalls`,
  `high-cost lending risk context lending`, `risk context lending`, `more
  listed Business`, and `more listed Mercado`.
- Positive rendered checks confirmed replacement/restored language on
  `/city/virginia-beach-va/`,
  `/browse/pawn-shops/virginia-beach-va/`,
  `/browse/pawn-shops/las-vegas-nv/`,
  `/browse/business-loans/chicago-il/`, and
  `/browse/check-cashing/sacramento-ca/`.
- Production spot checks returned HTTP 200 for `/`,
  `/city/virginia-beach-va/`,
  `/browse/pawn-shops/virginia-beach-va/`,
  `/browse/pawn-shops/las-vegas-nv/`,
  `/browse/business-loans/chicago-il/`,
  `/browse/check-cashing/sacramento-ca/`, and `/sitemap-index.xml`.

Notes:

- Render-component cleanup; no source lender, city, category, comparison, or
  education records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 128: Lender Card Proper-Name Restoration

Date: 2026-05-27
Implementation commit: `60061f54f0` (`fix: restore superior proper names in lender cards`)

Scope:

- `src/components/LenderCard.astro`

What changed:

- Added a provider-card restoration pass for proper-name contexts damaged by a
  previous broad `superior` safe-copy replacement.
- Restored visible lender-card copy such as `Superior Pawn`, `Superior Loan`,
  `Superior Credit Repair`, `Superior Ave`, and `Superior rating`.
- Preserved the Batch 127 claim-softening behavior for card descriptions and
  profile signals.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan across `dist/city` and `dist/browse` returned zero
  matches for damaged artifacts: `more listed Pawn`, `more listed Loan`, `more
  listed Credit Repair`, `more listed Ave`, and `more listed rating`.
- Positive rendered checks confirmed restored copy on
  `/browse/pawn-shops/virginia-beach-va/`,
  `/browse/personal-loans/oklahoma-city-ok/`,
  `/browse/credit-repair/chicago-il/`,
  `/browse/emergency-cash/cleveland-oh/`, and
  `/browse/banking/las-vegas-nv/`.
- Production spot checks returned HTTP 200 for `/`,
  `/browse/pawn-shops/virginia-beach-va/`,
  `/browse/personal-loans/oklahoma-city-ok/`,
  `/browse/credit-repair/chicago-il/`,
  `/browse/emergency-cash/cleveland-oh/`,
  `/browse/banking/las-vegas-nv/`, and `/sitemap-index.xml`.

Notes:

- Render-component cleanup; no source lender, city, category, comparison, or
  education records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 126: Emergency-Cash Comparison Claim Softening

Date: 2026-05-27
Implementation commit: `1b83026a91` (`fix: soften emergency-cash comparison claims`)

Scope:

- `src/pages/compare/[slug].astro`

What changed:

- Added comparison-only render-time cleanup for emergency-cash claim language.
- Reframed `predatory` comparison phrases to high-cost/risk-context wording on
  comparison pages.
- Replaced broad `for most borrowers` wording with stored-profile comparison
  framing.
- Preserved educational content, source comparison data, lender data, pricing,
  ratings, slugs, table/schema layout, city pages, and category pages.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for targeted raw phrases:
  `predatory`, `for most borrowers`, `debt-trap`, `debt trap`, `safest`,
  `safer choice`, `best choice`, `best option`, `we recommend`, or
  `should choose`.
- Targeted rendered checks confirmed replacement language including
  `high-cost loan-rate context`, `For borrowers comparing these stored profile
  fields`, `high-cost payday-loan structure`, and `high-cost short-term lending
  model`.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/brigit-vs-ace-cash-express-terrytown/`,
  `/compare/ace-cash-express-new-orleans-la-vs-amscot-the-money-superstore-orlando/`,
  `/compare/brigit-vs-advance-america-montebello/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-template cleanup; no source comparison, education, lender, city, or
  category records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 124: Comparison Context Grammar Normalization

Date: 2026-05-27
Implementation commit: `341d91dda0` (`fix: normalize comparison context grammar`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added final render-time cleanup for comparison grammar created by earlier
  safe-copy passes.
- Normalized remaining `risk-context fields` wording to `risk context`.
- Added final comma cleanup for `more [topic] context with` phrases including
  cost, value, profile, transparency, and consumer-protection contexts.
- Normalized `consumer context protection`, `consumer context researching`,
  `consumer context comparing`, `consumer context compared`, and `consumer
  context seeking`.
- Preserved source comparison records, education records, lender records,
  pricing values, ratings, route slugs, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed after a second build with the final-order cleanup.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Focused rendered scan across `dist/compare`, `dist/blog`, `dist/courses`,
  `dist/learn`, and `dist/financial-wellness` returned zero matches for the
  targeted Batch 124 phrase set.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/brigit-vs-ace-cash-express/`,
  `/compare/smartcredit-vs-regal-credit-management/`,
  `/compare/creditassociates-vs-new-era-debt-solutions/`,
  `/courses/credit-fundamentals/personal-loans-and-borrowing-smart/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-only safe-copy cleanup; no source comparison, education, lender, city,
  or category records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 118: Comparison Risk-Copy Grammar Normalization

Date: 2026-05-27
Implementation commit: `f1ee357215` (`fix: normalize comparison risk copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added render-time cleanup for residual comparison grammar and risk-language
  artifacts created by earlier safe-copy passes.
- Normalized phrases including `more listed choice`, duplicated published
  refund-term wording, `stronger listed`, `protects borrowers`, `actual profile
  context`, `predatory lending risks`, `predatory loan terms`, `predatory debt
  cycles`, `hidden fees`, `troubling history`, `devastating APRs`, `extreme
  APRs`, and `sustainable financial health`.
- Reframed the affected copy into listed-context, refund-term,
  borrower-protection-context, high-cost-risk-context, repeat-borrowing-cycle,
  fee-verification, regulatory-history, high-APR, and long-term financial-health
  context language.

Verification:

- `git diff --check` passed.
- Valid `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Focused rendered `dist/compare` scan returned zero matches for the targeted
  Batch 118 grammar and risk-language phrase set.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/brigit-vs-ace-cash-express/`,
  `/compare/brigit-vs-advance-america-missouri-city/`,
  `/compare/kikoff-vs-gocreditme-lake-western/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-layer cleanup only; no source comparison, lender, city, category,
  wellness, or generated provider data was edited.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.
- Workpack notes:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_118_notes_2026-05-27.md`.

### Batch 094: Category Metadata and Comparison Label Claim Softening

Date: 2026-05-26
Implementation commit: `384cb30442` (`fix: soften category and comparison claim labels`)

Scope:

- `src/components/DiagnosisCard.astro`
- `src/content/categories.json`
- `src/utils/safe-copy.ts`

What changed:

- Removed rendered HTML comment language that exposed diagnosis wording in the
  profile note component.
- Softened category metadata for credit repair, personal loans, emergency cash,
  debt relief, credit building, credit monitoring, free help, and insurance.
- Replaced broad category claims such as `Best ...`, `top credit repair`,
  `real results`, `money-back guarantees`, `Need money today`, `same-day or
  next-day funding`, `Same-Day Funding`, `no catch, no upsell`, and `financial
  guarantees` with comparison, listed-term, public-signal, and verification
  wording.
- Added shared safe-copy replacements for generated comparison language around
  `superior pricing`, `customer proof`, `social proof`, and `same-day funding`
  so rendered comparison pages use listed-pricing, stored public-review, and
  funding-timing verification wording.
- Preserved route slugs, source comparison records, source lender records,
  pricing fields, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected the full 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Strict rendered scan returned no matches for targeted raw phrases:
  `Diagnosis text`, `Stethoscope Icon`, `money-back guarantees`,
  `money-back guarantee`, `Best Credit Repair Companies`,
  `Best Personal Loan Lenders`, `Best Debt Relief Companies`,
  `Best Credit Building Tools`, `Best Credit Monitoring`,
  `same-day or next-day funding`, `Same-Day Funding`, `same-day funding`,
  `Need money today`, `top credit repair`, `real results`,
  `no catch, no upsell`, `financial guarantees`, `superior pricing`,
  `customer proof`, or `social proof`.
- Positive rendered checks confirmed replacement language including
  `Credit Repair Companies 2026`, `listed refund terms`,
  `stored public-review signals`, `Compare Funding Timing`,
  `listed funding-timing claims to verify`, `funding-timing claims to verify`,
  `Debt Relief Companies 2026`, `Credit Building Tools 2026`,
  `Credit Monitoring & Identity Protection 2026`, `free or low-cost`,
  `provider signals`, `exclusions`, `claims processes`,
  `clearer listed pricing context`, and `stored public-review context`.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/credit-saint-vs-the-credit-repairmen/`,
  `/compare/credit-supreme-credit-repair-miami-fix-credit-fast-miami-fl-vs-safeport-law/`,
  `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- This batch combined source category metadata cleanup with shared generated-copy
  safety rules.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 074: Comparison Risk And Timing Claims

Date: 2026-05-26
Implementation commit: `df4d255e33` (`feat: soften comparison risk and timing claims`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Extended `softenYmylCopy()` to convert remaining generated comparison
  endorsement-style phrases into profile-context wording before rendering.
- Softened `lower-risk`, `safer`, `more trustworthy`, `more reliable and
  accountable`, `superior BBB`, `stronger credentials`, and similar comparison
  summary language into listed-field, trust-signal, or context-to-verify copy.
- Reworded guarantee/refund phrasing such as `guarantee terms`,
  `lacks this guarantee`, `unconditional listed refund term`, and
  `transparent guarantee policies` into published refund-term or
  refund-policy context.
- Reworded `same-day funding` and `next-day funding` variants into
  funding-timing claims to verify so city, browse, and comparison output does
  not imply timing certainty.
- Preserved source comparison records, city/browse/review routes, slugs,
  category mappings, rankings, ratings, links, cards, tables, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- `dist/compare` scan returned no matches for targeted risky phrases including
  `lower-risk`, `more trustworthy`, `trustworthy choice`, `more reliable and
  accountable`, `superior BBB`, `stronger BBB reputation`, `crucial consumer
  protection`, `guarantee terms`, `significantly stronger credentials`,
  `stronger business practices`, `guarantee policies`, and `outperforms`.
- Targeted rendered checks confirmed safer wording on:
  `/compare/ace-cash-express-new-orleans-la-vs-ace-cash-express-terrytown/`,
  `/compare/ecreditadvisor-vs-the-credit-people/`, and
  `/compare/credit-saint-vs-the-credit-people/`.
- `dist/city` and `dist/browse` scan returned no matches for raw
  `same-day funding claims to verify` or `next-day funding claims to verify`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/learn/`, `/blog/`, `/categories/fintech/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Helper-only change; no source records, route generation, slug generation,
  ranking logic, category assignment, or page layout changed.
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

### Batch 073: Comparison Monthly Price Rendering

Date: 2026-05-26
Implementation commit: `a8743c57cd` (`fix: guard comparison monthly price rendering`)

Scope:

- `src/components/ComparisonTable.astro`
- `src/pages/compare/[slug].astro`

What changed:

- Added finite-price guards for comparison monthly-price rendering so empty tier
  filters cannot render `Infinity` into the side-by-side comparison table.
- Reused the same lowest-listed monthly-price logic in comparison header cards
  and FAQ answers so tiered providers with `monthly_price: 0` do not display as
  `Free/mo` when a listed tier price exists.
- Removed broad title softening from comparison titles and rebuilt the display
  title from provider names so business names containing `Best` are preserved
  instead of being rewritten to awkward title copy such as `notable 0 Down`.
- Preserved comparison routes, slugs, source records, JSON-LD structure,
  category links, ratings, review links, and card/table layout.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- `dist/compare` scan for `Infinity`, `$Infinity`, and `NaN` returned no
  matches.
- Rendered verification on
  `/compare/greenlight-financial-vs-vip-auto-lease-nyc-best-0-down-leasing-deals/`
  confirmed the card, table, FAQ, and JSON-LD price context use `$229.00/mo`
  for VIP Auto Lease instead of `$Infinity/mo` or `Free/mo`.
- Rendered verification confirmed the page title now preserves
  `VIP Auto Lease NYC Best 0 Down Leasing Deals` as the provider name instead
  of rewriting it to `notable 0 Down Leasing Deals`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/learn/`, `/blog/`, `/categories/fintech/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- The Greenlight/VIP comparison route exists in the local build but returned
  404 on production during the quality check, indicating it is not deployed on
  the live site yet rather than a live outage.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 075: Comparison Guarantee And Value Claims

Date: 2026-05-26
Implementation commit: `ccdfc797cc` (`feat: soften comparison guarantee value claims`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Extended `softenYmylCopy()` for remaining comparison-generated guarantee,
  refund, value, choice, winner, flexibility, and social-proof phrasing.
- Reworded variants such as `does not explicitly guarantee this benefit`,
  `50-point guarantee with full money-back refund`, `full money-back refund`,
  `performance guarantee`, `significantly reduces consumer risk`,
  `assurance of results`, `valuable 72-hour listed satisfaction term`,
  `superior geographic flexibility`, `wins decisively`, `edges ahead`,
  `cannot match`, `overwhelming social proof`, and `critical differentiators`
  into provider-stated, listed-field, listed-cost, or context-to-verify wording.
- Reworded `Choose based on`, `choose Cosmo`, and similar comparison-summary
  phrasing into compare-oriented language.
- Preserved comparison routes, slugs, source records, rankings, category
  mappings, ratings, review links, table layout, and card layout.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- `dist/compare` scan returned no matches for the targeted guarantee, value,
  winner, flexibility, social-proof, and `consumer-protection context context`
  phrases.
- Targeted rendered checks covered
  `/compare/advance-america-oklahoma-city-vs-advance-america-hialeah-fl/`,
  `/compare/ace-cash-express-new-orleans-la-vs-amscot-the-money-superstore-orlando/`,
  `/compare/credit-blueprint-vs-cosmo-credit-repair/`, and
  `/compare/national-credit-care-vs-cosmo-credit-repair/`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/learn/`, `/blog/`, `/categories/fintech/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Helper-only change; no source lender records, routes, slugs, rankings,
  category mappings, or card/table layout changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 076: Comparison BBB Display Normalization

Date: 2026-05-26
Implementation commit: `17aa6b269c` (`fix: normalize comparison BBB display`)

Scope:

- `src/pages/compare/[slug].astro`
- `src/components/ComparisonTable.astro`

What changed:

- Normalized blank and `N/A` BBB ratings in comparison header cards, table
  badges, BBB winner ranking, FAQ copy, and JSON-LD FAQ output.
- Missing BBB values now render as `BBB: NR` in badges and as "does not have a
  stored BBB rating in this profile" in FAQ copy.
- Preserved source lender records, routes, slugs, pricing, ratings, category
  mappings, review links, and table/card layout.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- `dist/compare` scan returned no matches for `has a  BBB rating`,
  `BBB: </span>`, or blank `> </span>` artifacts.
- Targeted rendered check on
  `/compare/smartcredit-vs-boost-my-fico-scores/` confirmed `BBB: NR` display
  and no malformed blank BBB FAQ text.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/learn/`, `/blog/`, `/categories/fintech/`,
  `/compare/smartcredit-vs-boost-my-fico-scores/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only normalization; no source lender records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 077: Shared BBB Badge Normalization

Date: 2026-05-26
Implementation commit: `8d2b206fd6` (`fix: normalize shared BBB badges`)

Scope:

- `src/utils/data.ts`
- `src/components/LenderCard.astro`
- `src/components/TopPicksTable.astro`
- `src/pages/best/[slug].astro`
- `src/pages/deals.astro`
- `src/pages/search.astro`
- `src/pages/api/search.ts`

What changed:

- Added shared `normalizedBbbRating()` helper and made `getBbbClass()` classify
  trimmed BBB values.
- Normalized blank and `N/A` BBB values to `NR` on shared lender cards,
  top-picks tables, listicle ranked cards, deals cards, client-side search
  result cards, and the search API compact payload.
- Preserved lender source records, routes, slugs, rankings, pricing, Google
  ratings, category mappings, review links, and layouts.
- `src/pages/deals.astro` is founder-protected; this batch touched only BBB
  badge normalization under the user's project-level permission to modify
  protected files and document the change.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered scan across `dist/browse`, `dist/deals`, and the static search shell
  returned no matches for blank `BBB:` artifacts.
- Targeted rendered check on
  `/browse/credit-unions/salt-lake-city-ut/` confirmed Hercules First and
  Ridgeline now render `BBB: NR` instead of a blank BBB badge.
- Rendered deals check confirmed BBB badges still render populated values such
  as `BBB: B+` and `BBB: A+`.
- Search API worker output includes `bb: normalizedBbbRating(...)`, and the
  client search bundle includes `normalizedBbbRating()`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/browse/credit-unions/salt-lake-city-ut/`, `/deals/`, `/search/`,
  `/categories/fintech/`, `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Render/API payload normalization only; no source lender records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 078: Comparison BBB FAQ Article Grammar

Date: 2026-05-26
Implementation commit: `a2cae90d57` (`fix: correct comparison BBB article grammar`)

Scope:

- `src/pages/compare/[slug].astro`

What changed:

- Corrected comparison BBB FAQ and JSON-LD FAQ copy so stored BBB labels render
  as `has an A+ BBB rating`, `has an NR BBB rating`, and `has an F BBB rating`
  where appropriate instead of `has a A+ BBB rating`, `has a NR BBB rating`,
  or `has a F BBB rating`.
- Preserved source comparison records, lender records, routes, slugs, pricing,
  ratings, badges, table layout, card layout, and comparison summaries.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for `has a A+ BBB rating`,
  `has a A BBB rating`, `has a F BBB rating`, or `has a NR BBB rating`.
- Targeted rendered checks on
  `/compare/incharge-debt-solutions-vs-detroit-wealth-club/` and
  `/compare/tang-associates-law-office-vs-american-debt-relief/` confirmed
  visible FAQ and JSON-LD FAQ output now use `has an A+ BBB rating` and
  `has an NR BBB rating`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/incharge-debt-solutions-vs-detroit-wealth-club/`,
  `/compare/tang-associates-law-office-vs-american-debt-relief/`, `/robots.txt`,
  and `/sitemap-index.xml`.

Notes:

- Render-only copy grammar fix; no source lender or comparison records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 079: Comparison Summary Safe-Copy Grammar

Date: 2026-05-26
Implementation commit: `f3f38fbc52` (`fix: normalize comparison summary safe copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added render-time copy normalization for comparison summary and winner-reason
  text so `with a A+ BBB rating`, `with a NR BBB rating`, and similar phrases
  render as `with an A+ BBB rating`, `with an NR BBB rating`, or the matching
  vowel-safe article.
- Moved `safer pick` normalization before the broader `safer` replacement so
  stored comparison summaries do not render as `the with more listed...`.
- Added final safe-copy cleanups for rendered comparison summaries that had
  already been softened into phrases such as `the with more listed
  risk-context fields, more sustainable choice`.
- Preserved source comparison records, routes, slugs, rankings, lender records,
  pricing, ratings, badges, table layout, card layout, meta routing, and JSON-LD
  structure.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for `with a A+ BBB rating`,
  `with a A BBB rating`, `with a F BBB rating`, `with a NR BBB rating`,
  `a A+ BBB rating`, `a A BBB rating`, `a F BBB rating`, or
  `a NR BBB rating`.
- Rendered `dist/compare` scan returned no matches for `the with more listed`,
  `with more listed risk-context fields, more`, or
  `with more listed risk-context fields pick`.
- Targeted rendered checks covered
  `/compare/incharge-debt-solutions-vs-clarifi/`,
  `/compare/kikoff-vs-boost-credit-101/`,
  `/compare/self-credit-builder-vs-boost-credit-101/`,
  `/compare/kikoff-vs-debt-freedom-ga/`,
  `/compare/kikoff-vs-self-credit-builder/`, and
  `/compare/credit-blueprint-vs-national-credit-care/`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/incharge-debt-solutions-vs-clarifi/`,
  `/compare/kikoff-vs-boost-credit-101/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only grammar and safe-copy cleanup; no source lender or comparison
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 080: Comparison Refund Safe-Copy Grammar

Date: 2026-05-26
Implementation commit: `c0b1c987d4` (`fix: normalize comparison refund safe copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added specific render-time normalization for common stored `risk-free` trial
  and service phrases before the broader YMYL-safe `risk-free` replacement runs.
- Corrected already-softened fragments such as `a with published refund terms
  $1 trial`, `with published refund terms trial access`, `with published
  refund terms payment structure`, and `with published refund terms service`.
- Corrected `an provider-stated...` article grammar to `a provider-stated...`
  for comparison refund-term copy.
- Preserved source comparison records, routes, slugs, rankings, lender records,
  pricing, ratings, badges, table layout, card layout, meta routing, and JSON-LD
  structure.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for `an provider-stated`,
  `a with published refund terms`, `with published refund terms trial`,
  `with published refund terms trial access`, `with published refund terms
  trial period`, `with published refund terms guarantee`,
  `with published refund terms payment structure`, `with published refund terms
  service`, or `risk-free`.
- Targeted rendered checks covered `/compare/smartcredit-vs-transunion/`,
  `/compare/smartcredit-vs-dovly/`,
  `/compare/the-credit-pros-vs-safeport-law/`,
  `/compare/kikoff-vs-first-progress-platinum-elite/`, and
  `/compare/dickmann-tax-group-vs-national-debt-relief/`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/smartcredit-vs-transunion/`,
  `/compare/the-credit-pros-vs-safeport-law/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only safe-copy cleanup; no source lender or comparison records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 081: Lender Name Whitespace Normalization

Date: 2026-05-26
Implementation commit: `20f3231278` (`fix: trim lender names in data shaping`)

Scope:

- `src/utils/data-build.ts`
- `src/utils/data-runtime.ts`

What changed:

- Trimmed loaded lender names in build-time `getAllLenders()` so city, browse,
  comparison, and list surfaces do not render provider names with trailing
  whitespace.
- Trimmed runtime database lender names in `shapeBodyInlineToLender()` and
  `shapeCatalogToLenderStub()` so SSR review and related-provider surfaces use
  the same normalized display names.
- Fixed rendered artifacts such as `Brightbridge ` headings and
  `alt="Brightbridge  logo"` without editing source JSON records.
- Preserved lender source records, routes, slugs, categories, rankings, pricing,
  ratings, logos, badges, city mappings, and card layout.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered scan returned no matches for double-space logo alt text in city,
  browse, compare, or search pages.
- Rendered scan returned no matches for provider-card `<h3>` names ending with
  trailing whitespace in city, browse, compare, or search pages.
- Targeted Lawrence rendered check showed `Brightbridge` without trailing
  whitespace and `alt="Brightbridge logo"`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/city/lawrence-ma/`, `/review/brightbridge/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Data-shaping normalization only; no source lender JSON records changed.
- A draft check against `/browse/credit-unions/lawrence-ma/` and
  `/browse/credit-unions/` returned 404 because those exact routes are not
  generated locally; this was treated as a bad check path, not a site outage.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 082: Comparison Zero Monthly Price Clarification

Date: 2026-05-26
Implementation commit: `3096ad5821` (`fix: clarify zero monthly price in comparisons`)

Scope:

- `src/pages/compare/[slug].astro`
- `src/components/ComparisonTable.astro`

What changed:

- Changed comparison monthly-price rendering for stored `0` values from
  `From Free/mo` to `No monthly subscription listed`.
- Stopped zero monthly subscription values from receiving the `Lower` badge in
  side-by-side comparison tables.
- Updated comparison FAQ answers so zero monthly subscription values do not
  read as free borrowing, free card usage, or a lower total-cost claim.
- Added a narrow capitalization cleanup for softened comparison summary copy
  that produced `. for national-access...` after YMYL-safe rewrites.
- Preserved source comparison records, source lender records, slugs, routes,
  pricing data, table structure, cards, JSON-LD structure, and review links.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for `Free/mo`,
  `same monthly price of Free/mo`, `lower monthly price at Free/mo`, or
  `From Free/mo`.
- Targeted rendered checks covered
  `/compare/the-credit-repairmen-vs-cosmo-credit-repair/`,
  `/compare/ace-cash-express-miami-fl-vs-amscot-the-money-superstore-orlando/`,
  and `/compare/kikoff-vs-opensky-secured-credit-card/`.
- Targeted rendered checks confirmed `No monthly subscription listed`,
  contextual zero-price FAQ language, and no zero-monthly `Lower` badge.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/the-credit-repairmen-vs-cosmo-credit-repair/`,
  `/compare/ace-cash-express-miami-fl-vs-amscot-the-money-superstore-orlando/`,
  `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Render-only comparison clarification; no source pricing or comparison records
  changed.
- The language now distinguishes no listed recurring monthly subscription from
  total product cost, borrowing cost, card fees, interest, and transaction fees.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 083: Slug-Like Lender Display Name Normalization

Date: 2026-05-26
Implementation commit: `575d73e79c` (`fix: normalize slug-like lender display names`)

Scope:

- `src/utils/data.ts`
- `src/utils/data-build.ts`
- `src/utils/data-runtime.ts`
- `src/pages/compare/[slug].astro`

What changed:

- Added shared `normalizeLenderDisplayName()` helper for all-lowercase
  hyphenated lender names.
- Applied display-name normalization to build-time and runtime lender data
  shaping.
- Replaced raw comparison participant slugs inside stored comparison summary and
  FAQ copy with current lender display names.
- Fixed rendered visible text, logo alt text, and JSON-LD artifacts such as
  `lakeview-law-group`, `safe-credit-solutions`, and `recovery-law-group`.
- Preserved source lender JSON records, route slugs, review URLs, logo paths,
  categories, pricing, ratings, badges, and layouts.

Verification:

- Initial `npm run build` attempt failed because the new helper was imported
  from the wrong module in runtime data shaping; the import was corrected before
  final verification.
- `git diff --check` passed.
- Final `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered scan returned no matches for visible raw-slug artifacts in logo alt
  text, card headings, or JSON-LD display names.
- Targeted rendered checks confirmed `Lakeview Law Group`,
  `Safe Credit Solutions`, and `Recovery Law Group` display text while stable
  URL and logo-path slugs remain unchanged.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/browse/debt-relief/new-york-ny/`,
  `/compare/american-profit-recovery-vs-lakeview-law-group/`, `/robots.txt`,
  and `/sitemap-index.xml`.

Notes:

- Render/data-shaping normalization only; no source lender JSON records changed.
- Existing route slugs, review URLs, and logo filenames intentionally remain
  slug-based.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 084: Comparison Risk Recommendation Copy Softening

Date: 2026-05-26
Implementation commit: `2bdc62480a` (`fix: soften comparison risk recommendation copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared safe-copy replacements for comparison winner/summary fragments
  that read like direct recommendations or unsupported superiority claims.
- Replaced `less problematic choice` with `profile with fewer listed risk
  flags`.
- Replaced `more problematic choice` with `profile with more listed risk flags`.
- Replaced `superior APR range` with `lower listed APR range`.
- Replaced `better accessibility and value` with `broader access and
  listed-cost context`.
- Replaced `better accessibility` with `broader access context`.
- Preserved source comparison JSON, lender JSON, pricing fields, route slugs,
  cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for
  `less problematic choice`, `more problematic choice`, `superior APR range`,
  `better accessibility and value`, or `better accessibility`.
- Targeted rendered checks confirmed the replacement phrases on
  `/compare/ace-cash-express-new-orleans-la-vs-ace-cash-express-orlando/` and
  `/compare/advance-america-oklahoma-city-vs-ace-cash-express-terrytown/`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/ace-cash-express-new-orleans-la-vs-ace-cash-express-orlando/`,
  `/compare/advance-america-oklahoma-city-vs-ace-cash-express-terrytown/`,
  `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Render-only safe-copy cleanup; no source comparison or lender records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 085: Comparison Zero Setup Fee Clarification

Date: 2026-05-26
Implementation commit: `48ed11457f` (`fix: clarify zero setup fee in comparisons`)

Scope:

- `src/components/ComparisonTable.astro`

What changed:

- Changed comparison setup-fee table rendering for stored `0` values from
  `Free` to `No setup fee listed`.
- Stopped zero setup-fee values from receiving the `Lower` badge in side-by-side
  comparison tables.
- Preserved source comparison records, source lender records, pricing values,
  routes, cards, table structure, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for setup-fee rows rendering
  `<span>Free</span>` or zero setup-fee `Lower` badges.
- Targeted rendered checks confirmed `No setup fee listed` on
  `/compare/ace-cash-express-new-orleans-la-vs-ace-cash-express-miami-fl/`.
- Targeted rendered checks confirmed `/compare/self-credit-builder-vs-discover-it-secured/`
  renders `$9.00` against `No setup fee listed` without a zero-fee `Lower`
  badge.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/self-credit-builder-vs-discover-it-secured/`,
  `/compare/ace-cash-express-new-orleans-la-vs-ace-cash-express-miami-fl/`,
  `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Render-only comparison clarification; no source pricing records changed.
- The table now distinguishes no listed setup fee from a broader claim that the
  product or service is free.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 086: Comparison Free Access Copy Softening

Date: 2026-05-26
Implementation commit: `2cbfdbdcef` (`fix: soften comparison free access copy`)

Scope:

- `src/utils/safe-copy.ts`
- `src/pages/compare/[slug].astro`

What changed:

- Added shared safe-copy replacements for broad free-access, no-hard-pull,
  encryption, recommendation, and superiority-style comparison language.
- Replaced `completely free` monitoring/sign-up/pricing language with
  no-listed-monthly-subscription or no-listed-upfront-fee context.
- Replaced `legitimate free access`, `robust encryption`, `professional credit
  repair assistance`, `product recommendations`, and `more comprehensive bureau
  coverage` with listed-context language.
- Replaced `is highlighted` and the comparison FAQ wrapper `stored comparison
  note highlights` with comparison-record phrasing.
- Replaced no-hard-pull and immediate score-impact wording with claims-to-verify
  language.
- Added cleanup replacements for awkward generated phrases after the first pass.
- Preserved source comparison records, source lender records, pricing values,
  route slugs, cards, tables, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json`
  changes affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for the targeted raw phrases:
  `completely free`, `legitimate free`, `professional credit repair assistance`,
  `is highlighted`, `stored comparison note highlights`,
  `more comprehensive bureau coverage`, `product recommendations`,
  `robust encryption`, `eliminating immediate score impact`,
  `no hard credit pull`, `superior overall value`,
  `more accessible and cost-effective`, `through its profile lists`, or
  `stronger listed-cost context`.
- Targeted rendered checks confirmed replacement language on
  `/compare/transunion-vs-credit-karma-credit-repair/`,
  `/compare/dovly-vs-the-credit-bureau/`, `/compare/dovly-vs-lookout/`, and
  `/compare/kikoff-vs-chime/`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/transunion-vs-credit-karma-credit-repair/`,
  `/compare/dovly-vs-the-credit-bureau/`, `/compare/dovly-vs-lookout/`,
  `/compare/kikoff-vs-chime/`, `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- The comparison FAQ now says CreditDoc records the stored comparison note rather
  than highlighting a provider.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 087: Comparison Consumer Protection Copy Softening

Date: 2026-05-26
Implementation commit: `19987ab63d` (`fix: soften comparison consumer protection copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared safe-copy replacements for consumer-protection, superiority,
  borrower-profile, and recommendation-style comparison fragments.
- Replaced `critical 72-hour listed satisfaction term` with
  `listed 72-hour satisfaction term`.
- Replaced `genuine consumer protection`, `substantial consumer protection`,
  and broad `consumer protections` phrasing with listed consumer-protection
  context.
- Replaced `superior consumer-facing tools`, `is superior for`, `superior for`,
  `better serves consumers`, and `better addresses actual emergency expenses`
  with listed-context language.
- Replaced `risk-averse borrowers`, `for qualified borrowers`, and
  `riskier for most users seeking` with borrower/provider-criteria and
  comparison-risk context.
- Added final-pass cleanup for generated `profile with more listed fields for...`,
  `the profile the profile...`, `stored outcome fields serving`,
  `trustworthy for`, and `Compare ... only when` / `compare ... only when`
  fragments.
- Preserved source comparison records, source lender records, pricing values,
  route slugs, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged JSON changes
  affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for targeted raw phrases:
  `the profile the profile`, `profile with more listed fields for`,
  `stored outcome fields serving`, `is superior for`, `superior for`,
  `riskier for most users`, `for most users seeking`,
  `Consumers should explore`, or `trustworthy for`.
- Targeted rendered checks confirmed replacement language on:
  `/compare/ace-cash-express-miami-fl-vs-ace-cash-express/`,
  `/compare/midland-credit-management-vs-american-profit-recovery/`,
  `/compare/incharge-debt-solutions-vs-detroit-wealth-club/`,
  `/compare/smartcredit-vs-dovly/`,
  `/compare/greenlight-financial-vs-the-credit-gal/`,
  `/compare/kikoff-vs-gocreditme-lake-western/`,
  `/compare/cambridge-credit-counseling-vs-clarifi/`, and
  `/compare/ace-cash-express-miami-fl-vs-advance-america-claymont/`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/ace-cash-express-miami-fl-vs-advance-america-claymont/`,
  `/compare/kikoff-vs-gocreditme-lake-western/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 119: Educational Teaser and Comparison Residue Normalization

Date: 2026-05-27
Implementation commit: `affda69017` (`fix: normalize educational teaser residue`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared render-time cleanup for residual educational teaser and
  comparison phrases surfaced in rendered `learn`, `financial-wellness`, and
  comparison output.
- Normalized awkward/generated phrases including `quick has more listed
  context`, `lower listed-cost profile`, `profile signals for simple cases`,
  `actual customer satisfaction`, `actual profile`, `that plague traditional
  payday lenders`, `proven service quality`, `sustained excellence`,
  `meaningful improvement`, `top financial priority`, `dangerously easy`, and
  `most responsible option`.
- Reframed wording into progress-marker, listed-cost, fit-signal,
  stored-context, operating-history, overspending-risk, and qualified
  professional discussion language.
- Preserved source comparison records, source wellness guide records, route
  slugs, JSON-LD structure, city pages, category pages, and sitemap generation.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Focused rendered scan across `dist/compare`, `dist/financial-wellness`, and
  `dist/learn` returned zero matches for the targeted Batch 119 phrase set.
- Production spot checks returned HTTP 200 for `/`, `/learn/`,
  `/financial-wellness/`,
  `/compare/brigit-vs-advance-america-missouri-city/`,
  `/compare/incharge-debt-solutions-vs-take-charge-america/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-only safe-copy cleanup; no source comparison, source wellness guide,
  lender, city, or category records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 117: Comparison Recommendation Residue Softening

Date: 2026-05-27
Implementation commit: `4164de7b33` (`fix: soften comparison recommendation residue`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared render-time safe-copy coverage for remaining comparison
  recommendation residue including `clearer choice`, `clearer profile to
  compare`, `more reliable option`, `most users`, `most clients`, `proven
  experience`, `measurable results`, `delivers measurable results`,
  `predatory lending terms`, `debt-trap`, and `riskier`.
- Reframed direct recommendation wording into listed-context,
  available-trust-signal, documented-experience, documented-outcome,
  high-cost-term, repeat-borrowing-risk, or higher-risk comparison language.
- Preserved source comparison records, lender records, route slugs, JSON-LD
  routing, comparison tables, diagnosis cards, city pages, category pages, and
  sitemap generation.

Verification:

- `git diff --check` passed.
- Valid `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Focused rendered `dist/compare` scan returned zero matches for `clearer
  choice`, `clearer profile to compare`, `more reliable choice`, `more
  reliable option`, `most consumers`, `most clients`, `most users`, `proven
  experience`, `measurable results`, `delivers measurable results`,
  `predatory lending terms`, `debt-trap`, `debt trap`, or `riskier`.
- Targeted rendered checks returned zero matches on representative affected
  pages including `/compare/cambridge-credit-counseling-vs-incharge-debt-solutions/`,
  `/compare/brigit-vs-ace-cash-express/`,
  `/compare/greenlight-financial-vs-self-credit-builder/`,
  `/compare/cambridge-credit-counseling-vs-premisien-credit-counseling/`,
  `/compare/american-consumer-credit-counseling-vs-detroit-wealth-club/`, and
  `/compare/brigit-vs-advance-america-missouri-city/`.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/cambridge-credit-counseling-vs-incharge-debt-solutions/`,
  `/compare/brigit-vs-ace-cash-express/`,
  `/compare/greenlight-financial-vs-self-credit-builder/`,
  `/compare/cambridge-credit-counseling-vs-premisien-credit-counseling/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-layer cleanup only; no source comparison, lender, city, category,
  wellness, or generated provider data was edited.
- Non-comparison educational/legal references such as state-law `actual
  results` language remain intentionally out of scope for this batch.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.
- Workpack notes:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_117_notes_2026-05-27.md`.

### Monitoring Checkpoint: 2026-05-27 Quality and Uptime Pass

Date: 2026-05-27

Scope:

- Site build health.
- Sitemap/robots generation.
- Production availability spot checks.
- Documentation and git hygiene check.

Verification:

- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Production spot checks returned HTTP 200 for `/`,
  `/credit-guide/amarillo-tx/`,
  `/compare/cambridge-credit-counseling-vs-incharge-debt-solutions/`,
  `/compare/brigit-vs-ace-cash-express/`, `/sitemap-index.xml`, and
  `/robots.txt`.
- Repo documentation and memory documentation were current through Batch 116
  before this monitoring checkpoint.

Notes:

- No source implementation files were changed during this checkpoint.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 110: Best Listicle Safe-Copy Softening

Date: 2026-05-27
Implementation commit: `248f2c923a` (`fix: soften best listicle copy`)

Scope:

- `src/pages/best/[slug].astro`

What changed:

- Added a listicle-specific render-time copy softener for `/best/[slug]` SSR
  pages.
- Softened listicle title, SEO title, description, SEO description, intro,
  TL;DR, key takeaways, visible FAQ, and FAQ JSON-LD output.
- Covered risky listicle phrases observed on live `/best/` samples, including
  `5 Best...`, `Cheapest...`, `expert reviews`, `real results`, `top pick`,
  `highest approval rate`, `approval speed`, `settlement success rates`,
  `best rates`, `best option`, `best choice`, `best combination`, `best for`,
  `best if`, `lowest APR`, and `Top 10 SBA lender`.
- Changed the no-credit-check listicle badge from `No Credit Check` to
  `No-credit-check claim`.
- Preserved runtime Supabase fetches, source listicle records, source lender
  records, ranked-lender order, provider names, route slugs, review links,
  card layouts, pricing values, star ratings, and schema structure.

Verification:

- `git diff --check` passed.
- Valid `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Production availability spot checks returned HTTP 200 for `/`,
  `/best/best-credit-repair-companies/`, `/best/best-no-credit-check-cards/`,
  `/best/best-sba-loans/`, `/credit-guide/amarillo-tx/`, and
  `/sitemap-index.xml`.

Notes:

- This is a render-layer cleanup for SSR `/best/` pages; the live production
  copy will reflect the softer wording after this commit is deployed and cache
  expires.
- No source listicle or lender data was edited.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 111: Deals Page Warning-Copy Softening

Date: 2026-05-27
Implementation commit: `03890d4f8b` (`fix: soften deals page warning copy`)

Scope:

- `src/pages/deals.astro`

What changed:

- Updated founder-protected `/deals/` copy under the active cleanup permission
  for this project.
- Replaced hard-edged consumer-facing phrasing around `"guaranteed" score
  jumps`, `legitimate company`, `Most legitimate disputes`, `results in days`,
  `selling you something`, `guarantee a score increase`, `walk away`, and
  `done legitimately`.
- Reframed the same compliance points as warning signs, verification context,
  bureau investigation windows, and consumer-protection-rule context.
- Preserved the protected page structure, deal cards, provider data, promo-code
  behavior, CTA links, education links, FAQ structure, and redirect from
  `/specials/`.

Verification:

- `git diff --check` passed.
- Targeted source scan returned no matches in `src/pages/deals.astro` for:
  `guaranteed`, `legitimate`, `walk away`, `results in days`,
  `selling you something`, or `guarantee a score increase`.
- Valid `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan returned no matches in `dist/deals/index.html` for
  the same old phrases.
- Production spot checks returned HTTP 200 for `/`, `/deals/`, `/specials/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Copy-only cleanup on a founder-protected page; no source deal or lender data
  was edited.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 112: Education and Resource Safe-Copy Softening

Date: 2026-05-27
Implementation commit: `c9e9dc292e` (`fix: soften education resource copy`)

Scope:

- `src/utils/safe-copy.ts`
- `src/pages/courses/credit-fundamentals/[slug].astro`
- `src/pages/courses/credit-fundamentals/index.astro`
- `src/components/LetterTemplatePage.astro`

What changed:

- Broadened the shared educational teaser safe-copy helper for education,
  course, and resource surfaces.
- Applied the helper to course module markdown, lesson titles, quiz questions,
  quiz answers, module titles/descriptions, visible breadcrumbs, H1 copy,
  Course JSON-LD, and CTA labels.
- Applied the helper to debt/credit letter template JSON-LD, usage guidance,
  template body lines, and checklist items.
- Replaced course overview heading `What You'll Walk Away With` with
  `What This Course Covers`.
- Covered targeted education/resource phrases found in rendered pages:
  `walk away`, `guaranteed outcome`, `guaranteed removal`,
  `guaranteed score jumps`, `guaranteed results`, `guarantees approval`,
  `legitimate company`, `legitimate services`, `legitimate disputes`,
  `best rates`, `lowest APR`, and `cheapest` variants.
- Added a cleanup for `not guaranteed` so checklist copy renders as
  `not certain` instead of the mechanical fallback.
- Preserved source course JSON, source markdown, source template data,
  resource routes, enrollment behavior, Sendy form behavior, quiz behavior,
  related-guide links, and page layouts.

Verification:

- `git diff --check` passed.
- Valid `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan returned no matches across `/learn/`, course overview,
  five course module pages, and debt/credit letter template pages for the old
  risky phrase set or `not claimed certain`.
- Production spot checks returned HTTP 200 for `/`, `/learn/`,
  `/courses/credit-fundamentals/`,
  `/resources/debt-credit-letter-templates/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-layer cleanup only; no source course, markdown, template, comparison,
  wellness, lender, or city data was edited.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 113: Resource and Research Residual Copy Softening

Date: 2026-05-27
Implementation commit: `c54dcdcf58` (`fix: soften resource research residual copy`)

Scope:

- `src/components/LetterTemplatePage.astro`
- `src/pages/resources/debt-credit-letter-templates/index.astro`
- `src/pages/research/most-responsive-consumer-finance-providers-2026.astro`

What changed:

- Extended the letter-template renderer so the educational safe-copy helper also
  covers hero H1 text, hero intro text, `Designed for` list items, where-to-send
  card copy, official-source descriptions, related template cards, related
  answer cards, more-guide cards, and tool CTA copy.
- Softened the debt/credit letter templates index copy from guarantee framing
  to certain-outcome framing.
- Softened the pay-for-delete template card language from `never guaranteed` to
  `removal may not happen`.
- Reframed the responsive-provider research disclaimer from `best, cheapest,
  safest` language to `universally preferable, lower-cost, lower-risk`
  language.
- Preserved source template data, pay-for-delete route behavior, research data,
  table rows, methodology links, internal graph links, and layouts.

Verification:

- `git diff --check` passed.
- Valid `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan returned no matches on the affected template index,
  pay-for-delete template, and responsive-provider report for `guaranteed
  deletion`, `not guaranteed`, `never guaranteed`, `do not guarantee`,
  `guarantee a collector`, `best, cheapest`, `cheapest, safest`, or `safest`.
- Broader rendered scan over `dist/resources`, `dist/tools`, `dist/research`,
  `dist/categories`, and `dist/answers` returned no matches for the residual
  phrase set.
- Production spot checks returned HTTP 200 for `/`,
  `/resources/debt-credit-letter-templates/`,
  `/resources/debt-credit-letter-templates/pay-for-delete-letter/`,
  `/research/most-responsive-consumer-finance-providers-2026/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render/source copy cleanup only; no comparison, wellness, lender, city, or
  generated provider data was edited.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 114: State and Blog Residual Safe-Copy Softening

Date: 2026-05-27
Implementation commit: `73614cf347` (`fix: soften state blog residual copy`)

Scope:

- `src/utils/safe-copy.ts`
- `src/pages/state/[slug]/lending-laws.astro`

What changed:

- Added educational teaser safe-copy coverage for singular `legitimate lender`
  language and the specific blog teaser phrase `No legitimate lender advertises
  certain approval`.
- Applied the existing YMYL safe-copy helper to state credit-repair key
  provisions so legal/regulatory source text such as `guaranteed results`
  renders as neutral result-claim language.
- Preserved source state data, blog post source metadata, state page routing,
  state legal page layout, blog index layout, city guides, category pages, and
  sitemap generation.

Verification:

- `git diff --check` passed.
- Valid `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan returned no matches on
  `/state/west-virginia/lending-laws/`, `/state/alaska/lending-laws/`, and
  `/blog/` for `guaranteed results`, `legitimate lender`, or
  `No legitimate lender`.
- Broader rendered scan over `dist/state`, `dist/financial-wellness`,
  `dist/blog`, `dist/tools`, `dist/city`, `dist/browse`, `dist/review`, and
  `dist/trends` returned zero matches for the current residual YMYL phrase set.
- Production spot checks returned HTTP 200 for `/`,
  `/state/west-virginia/lending-laws/`, `/state/alaska/lending-laws/`,
  `/blog/`, `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-layer cleanup only; no source state, blog, comparison, wellness,
  lender, city, or generated provider data was edited.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 115: Comparison Residual Claim Softening

Date: 2026-05-27
Implementation commit: `c4b7fbf338` (`fix: soften comparison residual claims`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared render-time safe-copy coverage for residual comparison claims
  using `significantly better` and `dramatically lower entry pricing`.
- Reframed customer-satisfaction, reputation/reliability, consumer-trust,
  validation/risk, and value wording into stored-signal or listed-context
  language.
- Preserved source comparison records, lender records, comparison routes,
  JSON-LD routing, comparison table behavior, diagnosis cards, city pages,
  category pages, and sitemap generation.

Verification:

- `git diff --check` passed.
- Valid `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan returned no matches for `significantly better` or
  `dramatically lower` on the seven affected comparison pages:
  `/compare/midland-credit-management-vs-accredited-debt-relief/`,
  `/compare/tang-associates-law-office-vs-lakeview-law-group/`,
  `/compare/brigit-vs-advance-america-missouri-city/`,
  `/compare/self-credit-builder-vs-opensky-secured-credit-card/`,
  `/compare/national-debt-relief-vs-new-era-debt-solutions/`,
  `/compare/american-consumer-credit-counseling-vs-clarifi/`, and
  `/compare/kikoff-vs-first-progress-platinum-elite/`.
- Broader rendered scan over `dist/compare`, `dist/categories`,
  `dist/answers`, `dist/resources`, `dist/research`, `dist/deals`,
  `dist/specials`, `dist/learn`, `dist/courses`, `dist/state`,
  `dist/financial-wellness`, `dist/blog`, `dist/tools`, `dist/city`,
  `dist/browse`, `dist/review`, and `dist/trends` returned zero matches for
  the current residual YMYL phrase set.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/midland-credit-management-vs-accredited-debt-relief/`,
  `/compare/kikoff-vs-first-progress-platinum-elite/`,
  `/compare/self-credit-builder-vs-opensky-secured-credit-card/`,
  `/compare/brigit-vs-advance-america-missouri-city/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Notes:

- Render-layer cleanup only; no source comparison, lender, city, category,
  wellness, or generated provider data was edited.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 116: Comparison Overclaim Residue Softening

Date: 2026-05-27
Implementation commit: `da4bb8e4a1` (`fix: soften comparison overclaim residue`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared render-time safe-copy coverage for remaining comparison
  overclaim residue including `superior`, `exceptional`, `vastly outweighs`,
  `proven credibility`, `proven client history`, `stronger option`, `zero
  interest`, `zero upfront`, and `no upfront costs`.
- Reframed residual comparative language into listed-feature,
  stored-review-signal, documented-history, or no-listed-upfront-cost language.
- Preserved source comparison records, lender records, route slugs, JSON-LD
  routing, comparison tables, diagnosis cards, city pages, category pages, and
  sitemap generation.

Verification:

- `git diff --check` passed.
- Valid `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Focused rendered `dist/compare` scan returned zero matches for `stronger
  choice`, `stronger option`, `superior`, `overwhelming social proof`, `proven
  credibility`, `proven client history`, `verified customer reviews`,
  `exceptional`, `vastly outweighs`, `zero interest`, `zero upfront`, `no
  upfront costs`, or `cannot match`.
- Targeted rendered checks returned zero matches on representative affected
  pages including `/compare/tang-associates-law-office-vs-lakeview-law-group/`,
  `/compare/cambridge-credit-counseling-vs-incharge-debt-solutions/`,
  `/compare/national-debt-relief-vs-new-era-debt-solutions/`,
  `/compare/american-consumer-credit-counseling-vs-clarifi/`,
  `/compare/transunion-vs-experian/`, and
  `/compare/credit-supreme-credit-repair-miami-fix-credit-fast-miami-fl-vs-the-credit-people/`.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/tang-associates-law-office-vs-lakeview-law-group/`,
  `/compare/cambridge-credit-counseling-vs-incharge-debt-solutions/`,
  `/compare/national-debt-relief-vs-new-era-debt-solutions/`,
  `/compare/transunion-vs-experian/`, `/credit-guide/amarillo-tx/`, and
  `/sitemap-index.xml`.

Notes:

- Render-layer cleanup only; no source comparison, lender, city, category,
  wellness, or generated provider data was edited.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 109: Comparison Overclaim Copy Softening

Date: 2026-05-27
Implementation commit: `00544bfa85` (`fix: soften comparison overclaim copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added render-time safe-copy coverage for comparison-page overclaim language
  including `clear winner`, `verified legitimacy`, `significantly stronger`,
  `risk-free`, `low-risk`, `transparent`, `superior value`, `substantially`
  lower-cost claims, `dramatically` lower-cost/value claims, and `proven`
  creditor-negotiation/result language.
- Added cleanup for awkward generated fragments such as `vastly has more listed
  context than`, `has more listed context than with`, and `has more listed
  context than on`.
- Preserved source comparison records, source lender records, provider names,
  route slugs, category assignments, cards, maps, tables, comparison FAQs, and
  layouts.

Verification:

- `git diff --check` passed.
- Valid `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for targeted comparison
  phrases including `clear winner`, `verified legitimacy`, `significantly
  stronger`, `low-risk trial`, `risk-free`, `superior value`, `substantially
  lower costs`, `dramatically lower costs`, `dramatically better value`,
  `transparent pricing`, `transparent fees`, `transparent fee structure`,
  `transparent stated terms`, `proven results`, `verified A+ BBB
  accreditation`, `proven creditor negotiation`, `vastly has more listed
  context`, `has more listed context than with`, `has more listed context than
  on`, ` wins`, and ` win`.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/accredited-debt-relief-vs-american-profit-recovery/`,
  `/compare/kikoff-vs-debt-freedom-ga/`,
  `/compare/smartcredit-vs-boost-my-fico-scores/`,
  `/compare/brigit-vs-ace-cash-express-terrytown/`,
  `/browse/credit-repair/brooklyn-ny/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 108: Residual YMYL Claim Softening

Date: 2026-05-27
Implementation commit: `22af51757b` (`fix: soften residual YMYL claims`)

Scope:

- `src/utils/safe-copy.ts`
- `src/pages/compare/[slug].astro`

What changed:

- Added safe-copy coverage for residual rendered claims around `legitimate`,
  `legally questionable`, tradelines, credit-score improvement, score-change
  claims, valuation/expert language, and market-pricing language.
- Added comparison-page final cleanup for compound phrases produced after shared
  safe-copy rewrites.
- Reframed affected language as provider claims to verify, compliance context,
  credit-score context to review, stored outcome context, or listed profile
  fields.
- Preserved source comparison records, source lender records, provider names,
  category assignments, route slugs, cards, maps, tables, city pages, browse
  pages, comparison pages, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- Valid `npm run build` passed after rejecting one known incomplete sitemap
  timeout build.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/city`, `dist/browse`, and `dist/compare` scan returned no
  matches for targeted residual phrases including `legitimate`, `sustainable
  credit building`, `average 49-point score increases`, `averaging 49-point
  score increases`, `help improve credit scores`, `improve credit scores`,
  `legally gray`, `legally questionable`, `controversial tradeline`, `fair
  market pricing`, `expert valuation`, `expert evaluation`, `hometown experts`,
  `methodology context for credit-building context to review`, `valuation
  contexts`, `evaluation contexts`, `genuine financial habits`, and `risky score
  improvements`.
- Production spot checks returned HTTP 200 for `/`, `/city/amarillo-tx/`,
  `/credit-guide/amarillo-tx/`,
  `/compare/self-credit-builder-vs-boost-credit-101/`,
  `/compare/greenlight-financial-vs-boost-credit-101/`,
  `/browse/credit-repair/brooklyn-ny/`,
  `/browse/pawn-shops/los-angeles-ca/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only safe-copy cleanup; no source comparison or lender records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 107: City Credit-Score Claim Softening

Date: 2026-05-27
Implementation commit: `550407f7a4` (`fix: soften city credit-score claims`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added targeted safe-copy replacements for city and browse provider-card copy
  that framed credit repair as direct credit-score improvement.
- Reframed `remove negative accounts and improve credit scores`, `remove
  negative items and improve credit scores`, `help clients improve credit
  scores`, `works to improve credit scores`, and `raise credit scores quickly`
  language as dispute/context/claim-to-verify language.
- Added grammar cleanup for rendered profile-signal phrases produced by the
  broad `to improve credit scores` replacement.
- Preserved provider names, source lender records, category assignments, route
  slugs, cards, maps, tables, city pages, and browse-page layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/city` and `dist/browse` scan returned no matches for targeted
  old phrases or grammar artifacts: `remove negative accounts`,
  `raise credit scores quickly`, `help clients improve credit scores`,
  `works to improve credit scores`, `and improve credit scores`,
  `to improve credit scores`, `seeking for credit-score`, or
  `structured plan for credit-score`.
- Production spot checks returned HTTP 200 for `/`, `/city/philadelphia-pa/`,
  `/browse/credit-repair/philadelphia-pa/`,
  `/browse/credit-repair/new-york-ny/`, `/city/tempe-az/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only city/browse safe-copy cleanup; no source lender records changed.
- Provider names containing phrases such as `Fix Your Credit` were preserved in
  this batch to avoid corrupting entity names.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 106: Self Eligibility Profile-Note Softening

Date: 2026-05-27
Implementation commit: `352b4426d4` (`fix: soften Self eligibility profile notes`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added targeted safe-copy replacements for broad Self profile-note language
  rendered on comparison pages.
- Reframed `People with no credit who need to build history from scratch` as
  `People with no credit comparing ways to build history from scratch`.
- Reframed `Anyone who wants to save money while building credit
  simultaneously` as `Consumers comparing savings-linked credit-building
  features`.
- Reframed `No credit check — anyone can apply` and `anyone can apply` as
  eligibility claims to verify against provider criteria.
- Preserved source lender records, comparison records, route slugs, pricing
  fields, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for targeted old phrases:
  `Anyone who wants to save money`, `anyone can apply`,
  `People with no credit who need to build history`, `save money while building
  credit simultaneously`, or `No credit check — anyone can apply`.
- Rendered checks confirmed replacement text on
  `/compare/self-credit-builder-vs-chime/`,
  `/compare/self-credit-builder-vs-discover-it-secured/`, and
  `/compare/self-credit-builder-vs-gocreditme-lake-western/`.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/self-credit-builder-vs-discover-it-secured/`,
  `/compare/self-credit-builder-vs-gocreditme-lake-western/`,
  `/compare/self-credit-builder-vs-chime/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 105: No-Subscription Safe-Copy Cleanup

Date: 2026-05-27
Implementation commit: `3472247df4` (`fix: clean no-subscription safe copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared safe-copy replacements for rendered comparison sentences that
  used awkward no-subscription wording such as `listed with no monthly
  subscription credit building`, `listed with no monthly subscription banking`,
  `listed with no monthly subscription counseling`, `listed with no monthly
  subscription financial coaching`, and `listed with no monthly subscription
  service`.
- Normalized duplicate connector phrases including `with no listed monthly
  subscription with no monthly fees`, `service with no listed monthly
  subscription with`, `counseling with no listed monthly subscription with`,
  `monitoring with no listed monthly subscription with`, and `credit monitoring
  with no listed monthly subscription with`.
- Cleaned remaining comparison output for `listed refund term terms`,
  `more listed-cost and reputable option`, and credit-building no-subscription
  variants.
- Preserved source comparison records, lender records, route slugs, pricing
  fields, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for targeted raw phrases:
  `listed with no monthly subscription`, `listed refund term terms`,
  `more listed-cost and reputable option`, `with listed with no monthly
  subscription credit building`, `offers listed with no monthly subscription
  credit building`, or `with no listed monthly subscription with`.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/self-credit-builder-vs-chime/`,
  `/compare/credit-saint-vs-credit-blueprint/`,
  `/compare/kikoff-vs-chime/`,
  `/compare/smartcredit-vs-credit-karma-credit-repair/`,
  `/compare/greenlight-financial-vs-chime/`,
  `/compare/transunion-vs-credit-karma-credit-repair/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 104: Refund-Term Safe-Copy Normalization

Date: 2026-05-26
Implementation commit: `bba1684f41` (`fix: normalize refund-term safe copy`)

Scope:

- `src/utils/safe-copy.ts`
- `astro.config.mjs`

What changed:

- Normalized redundant safe-copy output from `provider-stated listed refund
  term(s)` to `provider-stated refund term(s)`.
- Covered both sentence-case and lowercase variants, and both singular and
  plural term wording.
- Raised the Supabase city-guide sitemap fetch timeout from 60 seconds to 120
  seconds after repeated non-fatal fetch timeouts produced invalid reduced
  build inventory.
- Preserved source comparison records, lender records, route slugs, cards,
  tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- First fresh `npm run build` after the copy patch was discarded as verification
  evidence because city-guide sitemap generation timed out and only injected
  16,057 SSR route URLs.
- After raising the sitemap fetch timeout, `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for the old redundant
  phrases `provider-stated listed refund term` or
  `Provider-stated listed refund term`.
- Rendered `dist/compare` scan confirmed replacement output for
  `provider-stated refund term` / `Provider-stated refund term`.
- Production spot checks returned HTTP 200 for `/`,
  `/compare/the-credit-pros-vs-safeport-law/`,
  `/compare/the-credit-repairmen-vs-credit360-credit-repair/`,
  `/compare/credit360-credit-repair-vs-lenders-choice-credit-solutions/`,
  `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Sanitizer-only copy repair plus build reliability timeout change; no source
  comparison or lender JSON records were rewritten.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.
- Workpack notes:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_104_notes_2026-05-26.md`.

### Batch 103: Safe-Copy Entity Preservation

Date: 2026-05-26
Implementation commit: `a65ca0d245` (`fix: preserve mortgage brand names in safe copy`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Preserved `Guarantee Mortgage` when broad safe-copy refund-term rewrites
  would otherwise corrupt the provider name into `listed refund term Mortgage`.
- Softened provider-stated timing language for Instant Loan Processing from
  `guaranteed 24-hour turnaround times` to `advertised 24-hour turnaround
  times`.
- Preserved source lender records and route generation.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered HTML scan found no `listed refund term Mortgage`,
  `listed refund term mortgage`, or `refund term Mortgage` output.
- Rendered browse-page checks confirmed `Guarantee Mortgage is a
  California-based mortgage banker...` and `advertised 24-hour turnaround
  times`.
- Production spot checks returned HTTP 200 for `/`,
  `/browse/mortgages/san-francisco-ca/`, `/review/guarantee-mortgage/`,
  `/review/instant-loan-processing/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Sanitizer-only repair; no lender JSON records were rewritten.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.
- Workpack notes:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_103_notes_2026-05-26.md`.

### Batch 102: State Law Date Label

Date: 2026-05-26
Implementation commit: `43f2fdf6f7` (`fix: soften state law date label`)

Scope:

- `src/pages/state/[slug]/lending-laws.astro`

What changed:

- Reframed the state lending-law page metadata label from `Last verified` to
  `Law summary checked`.
- Preserved the underlying `legislation_last_updated` data, state-law routes,
  page layout, rule summaries, and state research context.

Verification:

- `git diff --check` passed.
- Source scan confirmed no remaining `Last verified` phrase in
  `src/pages/state`.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered scan confirmed `Law summary checked` across generated state
  lending-law pages and returned no old `Last verified` output in the scanned
  state build paths.
- Production spot checks returned HTTP 200 for `/`,
  `/credit-guide/amarillo-tx/`, `/state/texas/lending-laws/`,
  `/state/california/lending-laws/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Static label cleanup only; no state law records, lender records, or sitemap
  routing logic were rewritten.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.
- Workpack notes:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_102_notes_2026-05-26.md`.

### Batch 101: Editorial and CFPB Verification Labels

Date: 2026-05-26
Implementation commit: `5d9bf5b491` (`fix: soften editorial and CFPB verification labels`)

Scope:

- `src/pages/about/harvey-brooks.astro`
- `src/pages/trends/[slug].astro`

What changed:

- Reframed the editor bio page from an absolute every-fact verification claim
  to source-check language tied to available provider and regulator sources.
- Reframed CFPB trend profile header dates from `Last verified` to
  `Data checked`.
- Preserved trend data, CFPB dates, routes, metrics, chart content, editor page
  layout, and source links.

Verification:

- `git diff --check` passed.
- Source scan returned no matches for targeted old phrases:
  `Every fact in the written review is verified` or `Last verified` in the
  patched files.
- First `npm run build` completed but was discarded as verification evidence
  because city-guide sitemap generation timed out and only injected 16,057 SSR
  route URLs.
- Rerun `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered scan returned no matches for `Every fact in the written review is
  verified` or `Last verified` across rendered about/trends pages and trend SSR
  output.
- Replacement-language checks confirmed `source-checked against` on
  `/about/harvey-brooks/` and `Data checked:` on trend pages.
- Production spot checks returned HTTP 200 for `/`, `/about/harvey-brooks/`,
  `/trends/afterpay/`, `/trends/citizens-bank-columbia/`, `/trends/`,
  `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Static/SSR label cleanup only; no CFPB data records or editor profile routes
  were rewritten.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 100: Provider Caution Profile Signals

Date: 2026-05-26
Implementation commit: `3ee8edae17` (`fix: soften provider caution profile signals`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared safe-copy replacements for raw provider profile-signal language
  that displayed `(NOT recommended)` or `not recommended`.
- Reframed those labels as `flagged for caution` while preserving the caution
  signal for users.
- Applied at the shared `softenYmylCopy` layer so the cleanup covers lender
  cards, top-picks tables, review pages, best/listicle pages, city pages, and
  browse pages without rewriting provider records.

Verification:

- `git diff --check` passed.
- First `npm run build` completed but was discarded as verification evidence
  because city-guide sitemap generation timed out and only injected 16,057 SSR
  route URLs.
- Rerun `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered scan returned no matches for `NOT recommended` or `not recommended`
  across rendered browse, city, state, review SSR, and best SSR output.
- Replacement-language check confirmed `flagged for caution` on
  `/browse/credit-repair/miami-fl/`.
- Production spot checks returned HTTP 200 for `/`,
  `/browse/credit-repair/miami-fl/`, `/city/miami-fl/`,
  `/review/optimum-credit-solutions-credit-score-fix/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-layer cleanup only; no lender/provider records were rewritten.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 099: Educational Authority Copy

Date: 2026-05-26
Implementation commit: `8a0d9c6672` (`fix: soften educational authority copy`)

Scope:

- `src/pages/index.astro`
- `src/pages/financial-wellness/index.astro`
- `src/pages/credit-guide/[slug]/index.astro`

What changed:

- Reframed visible educational authority language away from broad
  finance-professional and expert-guide claims.
- Replaced homepage wellness teaser copy with CreditDoc research and editorial
  review language.
- Replaced financial wellness hub meta, hero, JSON-LD, and commitment copy with
  research-led editorial-process language.
- Replaced city-guide wellness teaser copy with research-led guide language
  focused on credit habits, debt decisions, and financial planning basics.
- Preserved page routes, page structure, guide records, city records, provider
  records, and founder/about factual bio copy.

Verification:

- `git diff --check` passed.
- Source scan returned no matches for the targeted old phrases:
  `Free educational guides written by finance professionals`,
  `CreditDoc's finance professionals`, `Written by finance professionals`,
  `written and reviewed by our finance team`, or
  `Expert guides to help consumers`.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered scan returned no matches for the targeted old phrases across static
  HTML, SSR worker modules, and client bundles.
- Replacement-language checks confirmed rendered output on `/`, the financial
  wellness hub, and the credit-guide SSR worker module.
- Production spot checks returned HTTP 200 for `/`, `/financial-wellness/`,
  `/credit-guide/amarillo-tx/`, `/city/amarillo-tx/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Static/SSR template copy cleanup only; no content records or provider data
  were rewritten.
- A positive rendered-check command included a static `dist/credit-guide`
  filepath that does not exist because city guide pages are SSR; the relevant
  replacement text was confirmed in `dist/_worker.js/pages/credit-guide/_slug_.astro.mjs`
  and the live route returned HTTP 200.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 098: Static Trust and Rating Copy

Date: 2026-05-26
Implementation commit: `5fff633ae7` (`fix: soften static trust and rating copy`)

Scope:

- `src/pages/about.astro`
- `src/pages/about/creditdoc-data.astro`
- `src/pages/best/[slug].astro`
- `src/pages/contact.astro`
- `src/pages/editorial-policy.astro`
- `src/pages/methodology.astro`
- `src/pages/review/[slug].astro`
- `src/pages/search.astro`

What changed:

- Reframed static trust, editorial, and methodology copy away from direct
  verification and expert-positioning claims.
- Replaced `verified user review platforms` with `public user review
  platforms`.
- Replaced `Pricing is verified monthly` and `Pricing Verification` language
  with pricing-reference review language.
- Replaced `No verified Google rating` with `No stored Google rating` in
  dynamic rating fallbacks.
- Replaced `Guarantee listed` with `Refund policy listed` in search filters.
- Reframed data-correction and removal copy around source-supported corrections
  and public-data context.
- Preserved routes, layouts, content records, pricing data, provider records,
  and dynamic page structure.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted source and rendered scans returned no matches for old risky phrases:
  `verified user review platforms`, `Pricing is verified monthly`,
  `No verified Google rating`, `verified mistakes`, `verified negative data`,
  `expert commentary`, `correction is verified`, `Guarantee listed`,
  `Verified customer reviews`, `Pricing Verification`,
  `direct pricing verification`, `Verified quarterly`,
  `How we verify information`, or `Verified through`.
- Replacement-language checks confirmed rendered output on `/about/`,
  `/about/creditdoc-data/`, `/contact/`, `/editorial-policy/`,
  `/methodology/`, dynamic review/best SSR modules, and the search client
  bundle.
- Production spot checks returned HTTP 200 for `/`, `/about/`,
  `/editorial-policy/`, `/methodology/`, `/about/creditdoc-data/`,
  `/contact/`, `/search/`, `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Static page and fallback-label cleanup only; no provider or comparison data
  records were rewritten.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 097: State Lending-Law Provider Copy Softening

Date: 2026-05-26
Implementation commit: `a149a5a3eb` (`fix: soften state lending law provider copy`)

Scope:

- `src/pages/state/[slug]/lending-laws.astro`

What changed:

- Replaced the state lending-law sidebar sentence that could render as
  `Compare  verified credit repair companies...` for zero-count states.
- Added singular/plural provider-count handling for states with listed credit
  repair provider profiles.
- Reframed the sidebar CTA away from `verified credit repair companies` into
  listed provider-profile and state-rule context.
- Preserved state law data, provider records, routes, CTA destination, legal
  resources, and page layout.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted rendered `dist/state` scan returned no matches for `Compare
  verified credit repair companies`, numbered `Compare ... verified credit
  repair companies`, blank-count `Compare  verified credit repair companies`,
  or `verified credit repair companies`.
- Positive rendered scan confirmed replacement language including listed credit
  repair provider profiles and local provider listings/state-rule context.
- Production spot checks returned HTTP 200 for `/`,
  `/state/texas/lending-laws/`, `/state/alaska/lending-laws/`,
  `/state/wisconsin/lending-laws/`, `/state/ohio/lending-laws/`, `/robots.txt`,
  and `/sitemap-index.xml`.

Notes:

- Remaining `guarantee` and `qualify` matches in state lending-law rendered
  scans were legal-context uses, such as VA-guaranteed loans, property-tax
  eligibility, or warnings that credit repair outcomes cannot be guaranteed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 095: Remaining Category Metadata and Provider Snippet Claim Softening

Date: 2026-05-26
Implementation commit: `46d9419f6e` (`fix: soften remaining category metadata claims`)

Scope:

- `src/content/categories.json`
- `src/utils/safe-copy.ts`
- `src/pages/credit-guide/[slug]/[category].astro`

What changed:

- Softened remaining category metadata for pawn shops, ATMs, credit cards,
  business loans, mortgages, bankruptcy, banks, credit unions, and fintech.
- Removed remaining `Best ...` category SEO titles for cards, business loans,
  mortgages, banks, credit unions, and fintech.
- Reframed pawn and ATM metadata away from cash-fast, no-credit-check, and
  surcharge-free claims into stored review, fee-context, and claim-verification
  language.
- Added shared safe-copy replacements for surcharge-free ATM/cash-access
  snippets and standalone no-credit-check snippets.
- Applied `softenYmylCopy` to dynamic credit-guide category provider snippets so
  SSR city-category pages use the same YMYL-safe provider summary boundary as
  browse cards.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered raw-phrase scan returned no matches for the Batch 095 phrase set,
  including `Best Credit Cards`, `Best Small Business Loans`, `Best Mortgage
  Lenders`, `Best Banks`, `Best Credit Unions`, `Best Fintech Apps`, `Get cash
  fast without a credit check`, `surcharge-free cash access`,
  `surcharge-free ATM access`, `surcharge-free ATMs`, `surcharge-free ATM
  network`, `no credit check.`, and `without a credit check`.
- Positive rendered/source scan confirmed replacement language including
  `eligibility context`, `consultation terms`, `experience signals`,
  `fee-context details`, `stored review signals`, `no-credit-check claims to
  verify`, `membership context`, and `ATM network fee context`.
- Built worker/source scan confirmed dynamic credit-guide category provider
  snippets route through `safeProfileCopy` / `softenYmylCopy`.
- Production spot checks returned HTTP 200 for `/`,
  `/browse/credit-cards/new-york-ny/`,
  `/browse/business-loans/new-york-ny/`,
  `/browse/mortgages/new-york-ny/`,
  `/browse/banking/new-york-ny/`,
  `/browse/credit-unions/phoenix-az/`,
  `/credit-guide/amarillo-tx/`, `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Source lender/provider records were not rewritten in this batch; provider
  snippet cleanup is render-time through shared safe-copy.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 096: Residual Guide, Review, Course, and Tool Claim Softening

Date: 2026-05-26
Implementation commit: `f073e71722` (`fix: soften residual guide and tool claim copy`)

Scope:

- `src/pages/credit-guide/[slug]/[category].astro`
- `src/pages/review/[slug].astro`
- `src/pages/courses/index.astro`
- `src/pages/courses/credit-fundamentals/index.astro`
- `src/pages/tools/borrowing-power-quiz.astro`
- `src/utils/inline-linker.ts`

What changed:

- Reframed dynamic pawn-shop guide intro away from `without a credit check` and
  immediate-cash language into collateral, fee, redemption, and item-recovery
  verification context.
- Reframed payday-alternative guide intro away from broad better-rate language
  into listed cost, eligibility, repayment, and lower-cost context.
- Removed `make an informed choice` from the dynamic guide fallback and replaced
  it with stored Google rating context.
- Replaced course meta descriptions' `No cost, no credit check` language with
  `No payment or account application required`.
- Reframed review-page secured-card cross-sell copy and button labels around
  bureau reporting, deposits, fees, and eligibility profile context.
- Reframed borrowing-power quiz urgent-need guidance from finding same-day or
  next-day options to comparing funding-timing claims, fees, and repayment
  terms.
- Softened inline-link title metadata for no-credit-check card links to `Card
  Eligibility Profiles`.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Targeted raw-phrase scan returned no matches for `without a credit check`,
  `you get cash immediately`, `make an informed choice`, `better rates than
  traditional payday loans`, `No cost, no credit check`, `Several options
  require no credit check`, `For urgent needs, look for same-day or next-day
  funding options`, `No Credit Check Cards`, or `Best No Credit Check Cards`
  across the batch-owned source files, rendered course pages, SSR worker route
  modules, inline-linker worker chunk, and borrowing-power client bundle.
- Positive scan confirmed replacement language in rendered course pages, SSR
  worker modules, source files, inline-linker worker chunk, and the
  borrowing-power client bundle.
- Production spot checks returned HTTP 200 for `/`, `/courses/`,
  `/courses/credit-fundamentals/`, `/tools/borrowing-power-quiz/`,
  `/credit-guide/amarillo-tx/`, `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- The route names under `/best/best-no-credit-check-cards/` were not changed;
  this batch only softened labels, metadata, and rendered guidance around those
  links.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 093: Static Support Authority and Safety Claim Softening

Date: 2026-05-26
Implementation commit: `58332ce3a0` (`fix: soften support page authority claims`)

Scope:

- `src/content/categories.json`
- `src/pages/about.astro`
- `src/pages/about/creditdoc-data.astro`
- `src/pages/faq.astro`
- `src/pages/financial-wellness/index.astro`

What changed:

- Softened the homepage Payday Alternatives category copy from broad safety,
  speed, and cost assertions to comparison-oriented language around advertised
  APR caps, eligibility, fees, speed, and repayment terms.
- Replaced About-page authority labels including `Expertise`, `Verified
  Pricing`, `Consumer Finance Specialist`, and `deep expertise` with research
  and direct-experience language.
- Reframed the data methodology page from `verified company information` and
  `lowest advertised monthly cost` to public/provider-source information and
  lowest listed monthly cost.
- Replaced FAQ language around `verified monthly where available` and
  `convenience and expertise` with reviewed-monthly and process-support wording.
- Replaced the Financial Wellness byline section heading and specialist wording
  with finance-background and research-lead language.

Verification:

- `git diff --check` passed.
- Initial `npm run build` attempt hit the known non-fatal city-guide timeout
  and injected only 16,057 SSR route URLs; that build was discarded for
  verification.
- Follow-up `npm run build` passed with 124 city guides, 2,232 city-category
  sub-pages, and 18,413 SSR route URLs; postbuild sitemap/robots check passed.
- Rendered targeted raw-phrase scan returned no matches for `Safer
  alternatives`, `same speed, far less cost`, `Our Mission, Team & Expertise`,
  `Verified Pricing`, `Consumer Finance Specialist`, `deep expertise`, `Written
  by Finance Professionals`, `consumer finance specialist`, `verified company
  information`, `lowest advertised monthly cost`, `verified monthly where
  available`, or `convenience and expertise`.
- Positive rendered checks confirmed replacement language on `/`, `/about/`,
  `/about/creditdoc-data/`, `/faq/`, and `/financial-wellness/`.
- Production spot checks returned HTTP 200 for `/`, `/about/`,
  `/about/creditdoc-data/`, `/faq/`, `/financial-wellness/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Static support/homepage copy cleanup; no comparison records or lender records
  changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.
- Workpack notes:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_093_notes_2026-05-26.md`.

### Batch 091: Comparison Proof, Pricing-Cap, and Refund Claim Softening

Date: 2026-05-26
Implementation commit: `145a43b931` (`fix: soften comparison proof and refund claims`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared safe-copy replacements for generated comparison fragments that
  framed review/testimonial proof, independent verification, social proof,
  capped pricing, mortgage specialization, refund terms, hidden pricing, and
  outcome claims as broad claims.
- Softened targeted phrases including `verified reviews`, `verified
  testimonials`, `independent verification`, `stronger social proof`,
  `transparent, capped pricing`, `transparent 6-month price cap`,
  `transparent 6-month cap`, `6-month maximum cap`, `6-month cost cap`, `price
  cap`, `cost cap`, `specialized mortgage-qualification experience`,
  `specialized mortgage-qualification expertise`, `specialized mortgage
  qualification`, `mortgage-qualification experience`, `no-hassle
  cancellation`, `full refund`, `full refunds`, `100% listed refund term`,
  `proven 27-year track record`, `comprehensive debt management
  specialization`, `hidden pricing`, `lower entry price is offset by`, `lack of
  specialization`, `significantly lower total cost`, `superior
  consumer-protection context`, and `documented/verifiable results`.
- Added cleanup for duplicate generated context artifacts such as repeated
  `listed` wording and repeated mortgage-qualification context.
- Preserved source comparison records, source lender records, pricing values,
  route slugs, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` targeted raw-phrase scan returned no matches.
- Targeted rendered checks confirmed replacement language on comparison pages
  including `/compare/ecreditadvisor-vs-national-credit-fixers/`,
  `/compare/ecreditadvisor-vs-safeport-law/`,
  `/compare/incharge-debt-solutions-vs-creditorg/`,
  `/compare/the-credit-repairmen-vs-cosmo-credit-repair/`,
  `/compare/self-credit-builder-vs-the-credit-gal/`, and
  `/compare/ace-cash-express-terrytown-vs-advance-america-montebello/`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/ecreditadvisor-vs-national-credit-fixers/`,
  `/compare/ecreditadvisor-vs-safeport-law/`,
  `/compare/incharge-debt-solutions-vs-creditorg/`,
  `/compare/the-credit-repairmen-vs-cosmo-credit-repair/`,
  `/compare/self-credit-builder-vs-the-credit-gal/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- Earlier retry hit a non-fatal city guide timeout and produced 16,057 SSR
  route URLs; that degraded build was discarded and not used for verification.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 092: Comparison Guarantee, Trust, and Specialist Claim Softening

Date: 2026-05-26
Implementation commit: `3b36c5857a` (`fix: soften comparison guarantee and trust claims`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared safe-copy replacements for generated comparison fragments that
  framed guarantees, specialist credentials, trusted status, verified clients,
  verified results, and settlement outcomes as broad claims.
- Softened targeted phrases including `refund guarantee`, `guarantee`,
  `guaranteed approval`, `guaranteed satisfaction`, `guaranteed outcomes`,
  `guaranteed credit bureau reporting`, `guaranteed 45-day refund option`,
  `NACSO-certified specialists`, `dedicated named specialist`, `specialist`,
  `specialists`, `specialized debt category`, `specialized debt`, `specialized`,
  `verified results`, `verified customer reviews`, `verified clients`,
  `trusted by 90% of lenders`, `trusted`, `trustworthy`, `documented 55-61%
  debt reductions`, `successful settlements`, `greater overall value`, and
  `expert consultation`.
- Added cleanup for generated grammar artifacts such as `staff context provide`
  after specialist-claim softening.
- Preserved source comparison records, source lender records, pricing values,
  route slugs, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` targeted raw-phrase scan returned no matches for the
  Batch 092 phrase set.
- Targeted rendered checks confirmed replacement language on comparison pages
  including `/compare/the-credit-pros-vs-safeport-law/`,
  `/compare/greenlight-financial-vs-boost-credit-101/`,
  `/compare/the-credit-repairmen-vs-credit360-credit-repair/`,
  `/compare/kikoff-vs-first-progress-platinum-elite/`,
  `/compare/dovly-vs-boost-my-fico-scores/`,
  `/compare/dickmann-tax-group-vs-grt-financial/`,
  `/compare/credit-blueprint-vs-continental-credit/`,
  `/compare/american-profit-recovery-vs-grt-financial/`,
  `/compare/greenlight-financial-vs-capital-one-platinum-secured/`, and
  `/compare/kikoff-vs-capital-one-platinum-secured/`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/the-credit-pros-vs-safeport-law/`,
  `/compare/greenlight-financial-vs-boost-credit-101/`,
  `/compare/the-credit-repairmen-vs-credit360-credit-repair/`,
  `/compare/kikoff-vs-first-progress-platinum-elite/`,
  `/compare/dickmann-tax-group-vs-grt-financial/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 090: Comparison Pricing and Credibility Claim Softening

Date: 2026-05-26
Implementation commit: `bbeb0116ea` (`fix: soften comparison pricing and credibility claims`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared safe-copy replacements for generated comparison fragments that
  framed pricing, savings, premium cost, perfect ratings, industry ranges,
  transparency, free/no-cost access, dispute timing, mortgage results,
  credibility, and refund protection as broad claims.
- Replaced `significantly lower pricing`, `saving clients`, `premium pricing`,
  `perfect 5.0/5`, `industry ceiling`, `transparency concerns`, `genuinely
  comprehensive`, `without paying anything`, `at no cost`, `same-day dispute
  filing`, `mortgage-focused results`, `verified credibility`, and
  `outcome-based refund protection` with listed/stored profile-context wording.
- Preserved source comparison records, source lender records, pricing values,
  route slugs, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged JSON changes
  affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for targeted raw phrases:
  `significantly lower pricing`, `saving clients`, `premium pricing`, `perfect
  5.0/5`, `industry ceiling`, `transparency concerns`, `genuinely
  comprehensive`, `without paying anything`, `at no cost`, `same-day dispute
  filing`, `mortgage-focused results`, `verified credibility`, or
  `outcome-based refund protection`.
- Targeted rendered checks confirmed replacement language on
  `/compare/credit-supreme-credit-repair-miami--vs-continental-credit/`,
  `/compare/dickmann-tax-group-vs-american-debt-relief/`,
  `/compare/dovly-vs-wallethub/`, and
  `/compare/ecreditadvisor-vs-credit-saint/`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/credit-supreme-credit-repair-miami--vs-continental-credit/`,
  `/compare/dickmann-tax-group-vs-american-debt-relief/`,
  `/compare/dovly-vs-wallethub/`, `/compare/ecreditadvisor-vs-credit-saint/`,
  `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 088: Comparison Review and Pricing Claim Softening

Date: 2026-05-26
Implementation commit: `10039854e1` (`fix: soften comparison review and pricing claims`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared safe-copy replacements for comparison summaries and winner notes
  that framed review ratings, pricing predictability, and user fit as broad
  recommendations.
- Replaced `superior Google review ratings` with `higher stored Google review
  signals`.
- Replaced `provides better predictable pricing` with `lists more predictable
  pricing context`.
- Replaced `appeals only to clients` with `may be relevant to clients`.
- Replaced `for most consumers` and `For most clients` with comparison-context
  wording.
- Replaced `predictable subscription costs outweigh` and `fees that easily
  exceed` with less deterministic pricing-comparison language.
- Preserved source comparison records, source lender records, pricing values,
  route slugs, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged JSON changes
  affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for targeted raw phrases:
  `superior Google review ratings`, `provides better predictable pricing`,
  `for most consumers`, `For most clients`, `appeals only to clients`,
  `predictable subscription costs outweigh`, `fees that easily exceed`, or
  `clients comparing with minimal`.
- Targeted rendered checks confirmed replacement language on
  `/compare/the-credit-repairmen-vs-credit360-credit-repair/` in visible
  summary, JSON-LD article description, FAQ JSON-LD, research note, and FAQ body.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/the-credit-repairmen-vs-credit360-credit-repair/`,
  `/compare/credit-blueprint-vs-the-credit-repairmen/`, `/robots.txt`, and
  `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.

### Batch 089: Comparison Value and Eligibility Claim Softening

Date: 2026-05-26
Implementation commit: `95ebf947a7` (`fix: soften comparison value and eligibility claims`)

Scope:

- `src/utils/safe-copy.ts`

What changed:

- Added shared safe-copy replacements for comparison summaries and winner notes
  that framed long-term value, credit-line potential, monitoring cost, and
  qualification as broad user-fit claims.
- Replaced `provide/provides better long-term value` and `better long-term
  value` with listed long-term comparison context.
- Replaced `for users who can qualify` and `users who can qualify` with
  eligibility-comparison context.
- Replaced `free CreditWise monitoring` with `CreditWise monitoring with no
  listed annual fee`.
- Replaced `potential for higher credit limits than deposit amounts` with
  listed potential credit-line context beyond deposit amounts.
- Replaced `established reputation` and `lacks critical compliance disclosures`
  with stored reputation signals and listed-disclosure context.
- Replaced `for consumers comparing profile details,` with stored-comparison
  context and added sentence-start capitalization cleanup.
- Preserved source comparison records, source lender records, pricing values,
  route slugs, cards, tables, FAQs, and layouts.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,413 SSR route URLs because unrelated unstaged JSON changes
  affect generated inventory.
- Postbuild sitemap/robots check passed.
- Rendered `dist/compare` scan returned no matches for targeted raw phrases:
  `better long-term value`, `users who can qualify`, `for users who can
  qualify`, `free CreditWise monitoring`, `potential for higher credit limits
  than deposit amounts`, `for consumers comparing profile details,`,
  `. for consumers comparing profile details`, `. in this stored comparison`,
  `established reputation`, or `lacks critical compliance disclosures`.
- Targeted rendered checks confirmed replacement language on
  `/compare/self-credit-builder-vs-capital-one-platinum-secured/` and
  `/compare/xperia-credit-solutions-vs-lenders-choice-credit-solutions/`.
- Production spot checks returned HTTP 200 for `/`, `/credit-guide/amarillo-tx/`,
  `/compare/self-credit-builder-vs-capital-one-platinum-secured/`,
  `/compare/xperia-credit-solutions-vs-lenders-choice-credit-solutions/`,
  `/robots.txt`, and `/sitemap-index.xml`.

Notes:

- Render-only comparison safe-copy cleanup; no source comparison or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged changes and were not staged or committed.
