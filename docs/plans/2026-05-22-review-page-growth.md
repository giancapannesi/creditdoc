# CreditDoc Review Page Growth Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn CreditDoc review pages from broad directory entries into high-trust, high-CTR review pages that lift rankings, earn clicks, and support the embedded-finance lead-routing strategy.

**Architecture:** Use the existing SSR review route and database-backed lender rows as the core. Add relevance and trust through measured template improvements, category-aware internal linking, answer-page connections, stronger SERP metadata, and controlled data-quality upgrades for pages already showing in Google Search Console.

**Tech Stack:** Astro SSR on Cloudflare Workers, Supabase runtime data via `src/lib/db.ts`, local SQLite mirror at `data/creditdoc.db`, GSC workpack CSVs, existing review template `src/pages/review/[slug].astro`, existing answer route `/answers/[slug]/`, existing tools under `/srv/BusinessOps/tools/`.

---

## Strategic Context

CreditDoc is building toward an embedded-finance and lead-routing engine. The directory/review layer is the SEO foothold. Review pages were created before city pages, blogs, and answer pages, so they are currently the first section showing meaningful GSC visibility.

The saved workpack for this plan is:

`/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Click_Growth_Review_Pages_2026-05-22`

Real data from that workpack:

- Latest stored GSC pull: `pull_id=10`, window `2026-04-17` to `2026-05-15`.
- Priority review worklist rows: `250`.
- Zero-click rows in that priority set: `245`.
- Missing custom SEO titles: `214`.
- Missing meta descriptions: `53`.
- Page-one / near-page-one priority categories:
  - `credit-repair`: 47
  - `emergency-cash`: 43
  - `check-cashing`: 43
  - blank category joins: 33
  - `business-loans`: 18
  - `personal-loans`: 15
  - `debt-relief`: 15
- Page status in the priority set:
  - `ready_for_index`: 197
  - blank joins: 33
  - `raw`: 18
  - `failed_quarantine`: 1
  - `pending_approval`: 1

The strongest near-term opportunity is not bulk content creation. It is improving pages that Google is already testing, especially page-one / near-page-one pages with zero clicks.

## External Search Guidance Used

Google guidance checked on 2026-05-22:

- Helpful content: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Review snippets: https://developers.google.com/search/docs/appearance/structured-data/review-snippet
- FAQ structured data: https://developers.google.com/search/docs/appearance/structured-data/faqpage
- General structured data guidelines: https://developers.google.com/search/docs/appearance/structured-data/sd-policies
- Link best practices: https://developers.google.com/search/docs/crawling-indexing/links-crawlable

Implications for CreditDoc:

- Do not rely on FAQ schema as a ranking shortcut. Google restricts FAQ rich results heavily, and FAQ structured data must match visible page content.
- Review and rating markup must be visible, specific, and not misleading.
- Internal links should use descriptive anchor text and help users understand the site.
- The page must add original value, not just summarize generic company data.
- Do not display unverified pricing or unsupported claims.

## Current Review Page Mechanics Verified

Review template:

`/srv/BusinessOps/creditdoc/src/pages/review/[slug].astro`

Verified current behaviour:

- SSR route: `export const prerender = false`.
- Runtime lender lookup: `getLenderWithBodyBySlugRuntime(slug, env)`.
- Runtime shaping: `shapeBodyInlineToLender(primaryRow)`.
- Canonical: `https://www.creditdoc.co/review/${lender.slug}/`.
- `noindex` if `isSkeleton || primaryRow.processing_status !== 'ready_for_index'`.
- `isSkeleton` if `quality_score < 3`, `pending_approval`, or `lender.no_index`.
- Existing sections include:
  - breadcrumbs
  - header and rating
  - description
  - services/features
  - pros/cons
  - rating breakdown
  - category cross-sell banners
  - regulatory and HMDA blocks where available
  - generated on-page FAQs
  - quick facts
  - diagnosis card
  - CFPB transparency block where available
  - compare-with section
  - related lenders
  - mini fit quiz
  - related financial wellness guides
  - course and borrowing-power quiz CTAs
  - glossary appendix

Existing answer-page mechanics:

- `/answers/[slug].astro` is SSR and DB-backed.
- Runtime answer helper exists: `getSiblingAnswersByPillarRuntime()`.
- Blog and state pages already fetch related answers from Supabase using `cluster_pillar`.
- Local mirror currently has answer clusters:
  - `personal-loans`: 8
  - `business-loans`: 7
  - `credit-cards`: 7
  - `credit-score`: 6
  - `build-credit`: 3
  - `debt-relief`: 3

Important gap:

The review page has on-page FAQs, but it does not yet have a proper related `/answers/` block. This is the most obvious safe internal-link improvement because it reuses existing CreditDoc educational assets and helps users continue from a company page into higher-context guidance.

## Non-Negotiable Constraints

- CreditDoc is a live business site.
- Do not deploy from a dirty or unclear worktree.
- Do not bulk rewrite pages.
- Do not display pricing unless first-party verified and explicitly approved by Jammi.
- Do not make negative unsupported claims about lenders.
- Do not mark weak/raw data as ready for index unless quality is checked.
- Do not pause content pipelines.
- Do not take instructions from anyone except Jammi.
- Keep changes measurable in GSC: small batches, clear date markers, and weekly measurement.

## Success Metrics

Primary:

- Raise CTR on review pages that already have impressions.
- Move selected page-one zero-click pages into click-producing pages.
- Improve internal link depth between `/review/`, `/answers/`, `/best/`, `/financial-wellness/`, `/compare/`, and category pages.

Secondary:

- Reduce missing SEO titles and missing meta descriptions in the 250-row priority set.
- Improve quality and index readiness for selected raw/pending/quarantined pages.
- Preserve or improve build health and sitemap/robots contract.

Measurement windows:

- Baseline: `pull_id=10`, `2026-04-17` to `2026-05-15`.
- First post-change review: next GSC pull at least 7 days after deploy.
- Stronger signal review: 21-28 days after deploy.

## Execution Strategy

Do not optimise all 250 pages manually at once.

Use three controlled tracks:

1. **Template-level improvements** that help every review page without changing facts.
2. **Data-level improvements** for the highest-priority pages only, using real lender data.
3. **Measurement and iteration** using GSC before expanding to more pages.

Recommended first batch:

- 20 pages maximum.
- Include:
  - 10 page-one / near-page-one zero-click commercial pages.
  - 5 high-impression low-position pages like `yrefy`.
  - 5 raw/pending/quarantined pages only after manual quality review.

## Task 1: Preserve Baseline And Create Batch 1

**Files:**

- Read: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Click_Growth_Review_Pages_2026-05-22/review_pages_priority_worklist.csv`
- Create: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Growth_Batch_1_2026-05-22.csv`
- Create: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Growth_Batch_1_Notes_2026-05-22.md`

**Step 1: Build the batch file**

Select no more than 20 pages:

- Highest priority pages with commercial categories.
- Exclude blank-join pages until the slug-to-lender join issue is understood.
- Include high-impression low-position pages only if they have `ready_for_index` and quality score >= 8.
- Include raw/pending/quarantined pages only in a separate review section.

**Step 2: Add required columns**

Batch CSV columns:

```csv
slug,page,name,category,city,state,clicks,impressions,ctr,position,processing_status,quality_score,current_seo_title,current_meta_description,batch_reason,planned_action,status
```

**Step 3: Manual review checklist**

For each selected page, record:

- Live URL returns `200`.
- Canonical is the expected `www.creditdoc.co/review/<slug>/`.
- Page is not `noindex` unless it should be.
- Main title describes the actual lender.
- Page has visible services/features/pros/cons/FAQ.
- Page links to at least one relevant user-next-step page.
- No unverified pricing appears.

**Step 4: Save batch notes**

Include:

- Baseline pull ID.
- Selection criteria.
- Pages selected.
- Pages excluded and why.

**Step 5: Commit only if appropriate**

This is a planning artifact only. Commit only after checking unrelated dirty files:

```bash
git -C /srv/BusinessOps/creditdoc status --short
```

Expected: dirty files may exist. Do not stage unrelated lender JSON or unrelated config changes.

## Task 2: Add Related Answers To Review Pages

**Files:**

- Modify: `/srv/BusinessOps/creditdoc/src/lib/db.ts`
- Modify: `/srv/BusinessOps/creditdoc/src/pages/review/[slug].astro`
- Test: `npm run build`

**Goal:**

Add a category-aware "Related Questions" block to review pages using existing `/answers/` content. This gives users a next step and strengthens internal linking between directory pages and educational content.

**Design:**

Add a helper in `src/lib/db.ts`:

```ts
export async function getAnswersByPillarRuntime(
  pillar: string,
  env?: RuntimeLenderEnv,
  limit = 4
): Promise<RuntimeAnswer[]> {
  if (!pillar || !env?.SUPABASE_URL || !env?.SUPABASE_ANON_KEY) return [];
  const url =
    `${env.SUPABASE_URL}/rest/v1/answers` +
    `?cluster_pillar=eq.${encodeURIComponent(pillar)}` +
    `&select=slug,title,cluster_id,cluster_pillar,banner_category,target_money_page,compliance_score,compliance_passed,body_inline,updated_at` +
    `&order=updated_at.desc` +
    `&limit=${limit}`;
  const rows = await _restGet<RuntimeAnswer>(url, env);
  return rows ?? [];
}
```

Import it in `review/[slug].astro`.

Map lender categories to answer pillars:

```ts
const answerPillarMap: Record<string, string> = {
  'personal-loans': 'personal-loans',
  'business-loans': 'business-loans',
  'debt-relief': 'debt-relief',
  'credit-repair': 'credit-score',
  'credit-counseling': 'debt-relief',
  'build-credit': 'build-credit',
  'credit-monitoring': 'credit-score',
  'emergency-cash': 'personal-loans',
  'payday-alternatives': 'personal-loans',
  'check-cashing': 'personal-loans',
};
const relatedAnswerPillar = answerPillarMap[lender.category] || 'credit-score';
const relatedAnswers = await getAnswersByPillarRuntime(relatedAnswerPillar, env, 4);
```

Render after the on-page FAQ or near related wellness guides:

```astro
{relatedAnswers.length > 0 && (
  <section class="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
    <div class="glass-card p-6">
      <div class="flex items-center justify-between gap-4 mb-4">
        <h2 class="text-lg font-bold text-text">Related Questions</h2>
        <a href="/answers/" class="text-sm text-primary hover:underline">View all</a>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {relatedAnswers.map(answer => (
          <a href={`/answers/${answer.slug}/`} class="glass-card p-4 block hover:border-primary transition-colors group">
            <span class="text-sm font-medium text-text group-hover:text-primary transition-colors">
              {answer.title.replace(/ \\| CreditDoc$/, '')}
            </span>
          </a>
        ))}
      </div>
    </div>
  </section>
)}
```

**Important:**

- Do not add FAQ schema for the related answer block.
- Do not invent new answer links.
- Use only published rows returned by the DB.

**Verification:**

Run:

```bash
cd /srv/BusinessOps/creditdoc
npm run build
```

Expected:

- Build passes.
- Sitemap/robots postbuild check still passes.

## Task 3: Fix The Review Quiz Category Matching

**Files:**

- Modify: `/srv/BusinessOps/creditdoc/src/pages/review/[slug].astro`
- Test: `npm run build`

**Problem verified:**

The mini quiz currently checks strings such as `cats.includes('credit repair')`, but `lender.category` values are slug strings like `credit-repair`, `personal-loans`, and `debt-relief`. That means some quiz scoring is weaker than intended.

**Change:**

Replace category substring checks with explicit category sets:

```js
const creditRepairCats = new Set(['credit-repair', 'credit-monitoring', 'build-credit']);
const loanCats = new Set(['personal-loans', 'business-loans', 'mortgages', 'emergency-cash', 'payday-alternatives']);
const debtCats = new Set(['debt-relief', 'credit-counseling', 'bankruptcy']);
const buildCats = new Set(['build-credit', 'credit-repair', 'credit-monitoring', 'banking']);
```

Then score:

```js
if (goal === 'repair' && creditRepairCats.has(cats)) score += 2;
if (goal === 'loan' && loanCats.has(cats)) score += 2;
if (goal === 'debt' && debtCats.has(cats)) score += 2;
if (goal === 'build' && buildCats.has(cats)) score += 1;
if (credit === 'poor' && (creditRepairCats.has(cats) || loanCats.has(cats))) score += 1;
```

**Verification:**

Run:

```bash
cd /srv/BusinessOps/creditdoc
npm run build
```

Expected:

- Build passes.
- No pricing display returns.

## Task 4: Improve SERP Titles And Meta For Batch 1

**Files:**

- Use DB API only: `/srv/BusinessOps/tools/creditdoc_db.py` or the established CreditDoc DB update path.
- Do not edit lender JSON files directly.
- Update batch notes: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Growth_Batch_1_Notes_2026-05-22.md`

**Goal:**

Improve CTR for selected pages without fabricating facts.

**Rules:**

- Use lender name, service category, city/state, and real differentiators already present in the lender row.
- No unverified pricing.
- No claims like "best", "guaranteed", "approved", "top-rated", or "lowest rate" unless verified.
- Prefer descriptive, user-intent titles.

**Title patterns:**

For local/service pages:

```text
<Lender Name> Review: <Category Label> in <City>, <State>
```

For national or ambiguous pages:

```text
<Lender Name> Review: Services, Complaints & Alternatives
```

For personal-loan pages:

```text
<Lender Name> Review: Loan Options, Fit & Alternatives
```

For credit-repair pages:

```text
<Lender Name> Review: Credit Repair Services & Alternatives
```

For debt-relief pages:

```text
<Lender Name> Review: Debt Help, Risks & Alternatives
```

**Meta description patterns:**

```text
Read CreditDoc's <Lender Name> review with services, location, consumer complaint signals, alternatives, and a quick fit quiz.
```

If location exists:

```text
Review <Lender Name> in <City>, <State>: services, contact details, complaint signals, alternatives, and a quick CreditDoc fit quiz.
```

**Verification:**

After updating batch metadata:

```bash
cd /srv/BusinessOps/creditdoc
npm run build
```

Expected:

- Build passes.
- No static JSON surgery is required.

## Task 5: Review Raw/Pending/Quarantined Page-One Pages

**Files:**

- Read: batch CSV and local DB.
- Use DB API only for any status or field updates.
- Update: batch notes.

**Pages identified in current priority top set include:**

- `the-debt-crushers` — `raw`, quality `0`, position `2.6`, 74 impressions.
- `a-loans-checks-cashed` — `raw`, quality `0`, position `2.2`, 35 impressions.
- `tax-debt-relief-alphabet-city` — `raw`, quality `5`, position `7.6`, 80 impressions.
- `envios-de-dinero-money-orders-pago-de-billes` — `failed_quarantine`, quality `1`, position `2.9`, 26 impressions.
- `snap-loans-cash-orlando` — `pending_approval`, quality `10`, position `2.5`, 20 impressions.

**Goal:**

Decide whether each page should be:

- improved and made indexable,
- kept noindex,
- recategorised,
- merged/canonicalised,
- or excluded from the first optimisation batch.

**Manual review checklist:**

- Is the business real?
- Is category correct?
- Is location correct?
- Is the page useful to a consumer?
- Is there enough real data to justify indexation?
- Does the page risk misclassification or YMYL trust problems?

**Do not:**

- Promote low-quality pages just because they rank.
- Set `ready_for_index` only to chase impressions.
- Add facts not present in verified sources or lender row data.

## Task 6: Add A Review Page Quality Scorecard

**Files:**

- Create: `/srv/BusinessOps/tools/creditdoc_review_page_scorecard.py`
- Read: `/srv/BusinessOps/creditdoc/data/creditdoc.db`
- Output: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Scorecard_YYYY-MM-DD.csv`

**Goal:**

Create a repeatable scoring report so future work does not depend on manual eyeballing.

**Inputs:**

- GSC page rows.
- Lender category/status/quality score.
- Presence of `seo_title`.
- Presence of `meta_description`.
- Presence of city/state.
- Processing status.

**Output columns:**

```csv
slug,page,name,category,city,state,clicks,impressions,position,processing_status,quality_score,has_seo_title,has_meta_description,indexability_risk,ctr_opportunity_score,recommended_action
```

**Score logic:**

- CTR opportunity high when impressions > 10, clicks = 0, position <= 15.
- Indexability risk high when status is not `ready_for_index`, quality < 3, or joined lender row is missing.
- Metadata gap high when title or meta is missing.

**Verification:**

Run:

```bash
python3 /srv/BusinessOps/tools/creditdoc_review_page_scorecard.py
```

Expected:

- CSV created.
- Counts match the saved workpack within expected date differences.

## Task 7: Add Internal Link Audit For Review Pages

**Files:**

- Create: `/srv/BusinessOps/tools/creditdoc_review_internal_link_audit.py`
- Output: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Internal_Link_Audit_YYYY-MM-DD.csv`

**Goal:**

Check whether selected review pages have enough internal next-step links.

**Audit checks:**

- Link to category page.
- Link to related lenders.
- Link to comparison page where available.
- Link to relevant `/answers/` page after Task 2.
- Link to relevant `/best/` page for commercial category where appropriate.
- Link to guide/tool/quiz.

**Verification:**

Run:

```bash
python3 /srv/BusinessOps/tools/creditdoc_review_internal_link_audit.py --slugs-from /srv/BusinessOps/CreditDoc\\ Project\\ Improvement/CreditDoc_Review_Page_Growth_Batch_1_2026-05-22.csv
```

Expected:

- Report identifies pages with weak link depth.
- No live site changes.

## Task 8: Create Category-Specific Review Enhancements

**Files:**

- Modify: `/srv/BusinessOps/creditdoc/src/pages/review/[slug].astro`
- Possibly create component: `/srv/BusinessOps/creditdoc/src/components/ReviewNextSteps.astro`
- Test: `npm run build`

**Goal:**

Make review pages feel intentionally useful per vertical, not one-size-fits-all.

**Credit repair pages should emphasize:**

- dispute process
- bureau reporting concepts
- credit report review
- realistic timelines without promises
- link to credit-score/build-credit answers

**Personal loan/emergency cash/check-cashing pages should emphasize:**

- funding speed context without guarantees
- APR/fee caution without displaying unverified pricing
- alternatives and fit quiz
- link to personal-loan answers and borrowing-power quiz

**Debt relief/credit counseling pages should emphasize:**

- debt consolidation versus settlement versus counseling
- risks and consumer protection
- link to debt-relief answers and debt letter resources

**Business loan pages should emphasize:**

- funding type
- SBA/line-of-credit/working-capital context
- link to business-loan answers

**Implementation approach:**

Add a small category-aware "What to check before you apply/contact them" block based only on category, not fabricated lender claims.

Example:

```astro
<ReviewNextSteps category={lender.category} lenderName={lender.name} />
```

**Verification:**

Run:

```bash
cd /srv/BusinessOps/creditdoc
npm run build
```

Expected:

- Build passes.
- The block is factual, generic, and clearly consumer-helpful.

## Task 9: Validate Structured Data And Avoid Schema Overreach

**Files:**

- Modify only if needed: `/srv/BusinessOps/creditdoc/src/pages/review/[slug].astro`
- Add test if project has suitable schema test pattern.

**Goal:**

Keep schema valid and compliant without trying to force rich results.

**Rules from Google guidance:**

- Marked-up content must be visible to users.
- Do not mark up misleading or irrelevant content.
- Review/aggregate ratings require extra care for local businesses and organizations.
- FAQ rich results are restricted and not a guaranteed traffic lever.

**CreditDoc approach:**

- Keep FAQ schema only for visible on-page FAQs.
- Do not add FAQ schema for related links.
- Keep review/rating schema aligned to visible rating methodology.
- Do not add pricing/Offer schema.

**Verification:**

Run:

```bash
cd /srv/BusinessOps/creditdoc
npm run build
```

Then spot-check rendered HTML for one selected review page in local preview or deployed preview before production deploy.

## Task 10: Deploy Only A Controlled Batch

**Files:**

- Use existing deploy path only.
- Do not deploy from unclear dirty worktree.

**Pre-deploy checks:**

```bash
git -C /srv/BusinessOps/creditdoc status --short
cd /srv/BusinessOps/creditdoc
npm run build
```

Expected:

- Build passes.
- Dirty files are understood.
- No unrelated lender JSON/content changes are accidentally included.

**Deploy rule:**

Use only the established CreditDoc deploy command documented in `CREDITDOC_NEXT.md`.

Do not use bare `wrangler deploy`.

**Post-deploy checks:**

- Live selected review URL returns `200`.
- Canonical is correct.
- No `noindex` on intended indexable pages.
- No pricing display.
- Related answer block appears where answer rows exist.
- Quiz still works.

## Task 11: Measure Results

**Files:**

- Read: GSC tables in `/srv/BusinessOps/creditdoc/data/creditdoc.db`.
- Create: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Growth_Results_YYYY-MM-DD.md`

**First measurement after next GSC pull:**

Compare selected batch pages:

- impressions
- clicks
- CTR
- average position
- indexed/not indexed state if available

**Do not judge too early:**

- First 7 days: only check for breakage and crawl/indexing changes.
- 21-28 days: evaluate ranking/CTR trend.

**Expansion rule:**

Only expand from 20 pages to 50 pages if:

- build/deploy was clean,
- no indexing regression,
- no structured data/manual risk,
- at least some CTR or position signal improves.

## Immediate Execution Order

1. Create Batch 1 from the saved workpack.
2. Add related answers block to review template.
3. Fix quiz category scoring.
4. Build-test.
5. Manually review the 20 selected pages.
6. Update SEO title/meta for selected ready pages through DB API only.
7. Build-test again.
8. Deploy only when the release scope is clean.
9. Measure after the next GSC pull.

## What To Avoid

- Do not rewrite the whole review page from scratch.
- Do not change all 15,000+ lender profiles.
- Do not use AI-generated facts as lender facts.
- Do not create fake review content.
- Do not restore pricing.
- Do not make schema the strategy.
- Do not optimise blank-join pages until the join issue is understood.
- Do not deploy documentation-only work unless there is an actual site change ready.

## Expected Outcome

The first successful version of this programme should produce review pages that feel more like useful consumer decision pages:

- clearer company/entity summary,
- better next-step links,
- visible FAQs that answer user concerns,
- stronger category fit,
- safer schema,
- improved SERP title/meta,
- and measured page-by-page GSC learning.

This supports the larger CreditDoc strategy: use the directory to earn organic discovery, then route users toward educational content, quizzes, comparison pages, and eventually finance origination/lead-routing flows.
