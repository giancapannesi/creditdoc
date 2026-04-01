# CreditDoc SEO & Data Quality Fix Plan

**Created:** 2026-03-22
**Status:** PHASES 1-3 DONE, Phase 4 pending (re-index quality pages)
**Priority:** CRITICAL — Google is flagging invalid structured data

---

## CRITICAL UPDATE: Google Has NOT Indexed Any Pages Yet (Mar 22)

Google Search Console shows **zero pages indexed** as of Mar 22. The site is still in crawl/discovery phase. This means:
- We have a window to fix data quality BEFORE Google commits to indexing
- Fixing now prevents penalty — we're not recovering, we're preventing
- Pages should be noindexed until enriched, then submitted for indexing one by one as the agent improves them
- **We might still save it if we act fast**

---

## What Happened (Context)

### Data Cleanup Completed (Mar 22)

Removed ~1,170+ non-lending businesses (bakeries, cannabis, clothing, electronics, etc.) from the lender database. Recategorized 1,591 pawn-related businesses into new `pawn-shops` category and 96 ATMs into new `atm` category. All removed businesses archived to `/srv/BusinessOps/creditdoc/archived_lenders/` with manifests.

Two new categories added to `src/content/categories.json`:
- `pawn-shops` — collateral-based loans
- `atm` — ATMs & cash access

All changes committed and pushed to `giancapannesi/creditdoc` on `main`.

### The SEO Problem Google Is Flagging

Google Search Console reports: **"Rating value is out of range (in 'reviewRating') — Items with this issue are invalid. Invalid items are not eligible for Google Search's rich results."**

Investigation found:
- The template at `src/pages/review/[slug].astro` line 98 already has `lender.rating > 0` check that prevents `reviewRating` from appearing in JSON-LD for rating-0 pages
- **Live site confirms the check IS working** — rating-0 pages do NOT have `reviewRating` in their structured data
- Google is likely reporting **cached crawl data from before the fix was deployed**
- This will self-resolve as Google re-crawls, but re-indexing requests would speed it up

### Current Data Quality Numbers (27,828 total lender pages)

| Metric | Count | % of Total |
|--------|-------|------------|
| Rating = 0 (no rating at all) | 1,103 | 4.0% |
| Rating = 5.0 (fake/default) | 3,246 | 11.7% |
| Real Google Maps rating (0 < r < 5) | 23,479 | 84.4% |
| Empty `typical_results_timeline` (blank FAQ answer) | 15,157 | 54.5% |
| Empty `guarantee_details` | 24,980 | 89.8% |
| No `website_url` | 17,497 | 62.9% |
| Enriched by agent (`has_been_enriched`) | 0 | 0.0% |

### The Real Problem

The owner's directive: **"You shouldn't have listed them without proper ratings — they should be drip fed. As the agent enriches them then they need to be added."**

Pages with skeleton data (no real content, empty FAQs, default features) are thin content that damages the site's SEO credibility. The enrichment pipeline should gate publication.

---

## Fix Plan — 4 Phases

### Phase 1: Fix FAQPage Structured Data — DONE (Mar 22)

**Problem:** 15,157 pages output FAQPage JSON-LD with empty answers (`"text":""`). This is invalid structured data that Google will penalize.

**File:** `src/pages/review/[slug].astro` (lines 65-80, 123-134)

**Fix:** Only include FAQ entries that have non-empty answers. If ALL answers are empty, don't output FAQPage schema at all.

```javascript
// Replace lines 65-80 with:
const faqs = [
  {
    question: `Is ${lender.name} legitimate?`,
    answer: `Yes. ${lender.name} is a registered company headquartered in ${lender.company_info.headquarters}${lender.company_info.founded_year ? `, founded in ${lender.company_info.founded_year}` : ''}. They hold a ${lender.company_info.bbb_rating} rating with the Better Business Bureau${lender.company_info.bbb_accredited ? ' and are BBB-accredited' : ''}.`,
  },
  ...(hasPricing ? [{
    question: `How much does ${lender.name} cost?`,
    answer: `${lender.name} plans start at ${formatPrice(lowestPrice)} per month${lender.pricing.setup_fee > 0 ? ` with a ${formatPrice(lender.pricing.setup_fee)} setup fee` : ' with no setup fee'}. ${lender.pricing.money_back_guarantee ? lender.pricing.guarantee_details : 'No money-back guarantee is offered.'}`,
  }] : []),
  ...(lender.typical_results_timeline ? [{
    question: `How long does ${lender.name} take to show results?`,
    answer: lender.typical_results_timeline,
  }] : []),
].filter(faq => faq.answer && faq.answer.trim().length > 0);
```

And in the JSON-LD array (lines 123-134), only include FAQPage if there are valid FAQs:
```javascript
// Replace the FAQPage block with:
...(faqs.length > 0 ? [{
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: faqs.map(faq => ({
    '@type': 'Question',
    name: faq.question,
    acceptedAnswer: {
      '@type': 'Answer',
      text: faq.answer,
    },
  })),
}] : []),
```

**Note:** The `jsonLd` variable is an array. Currently it always has 3 items (FinancialProduct, BreadcrumbList, FAQPage). After this change it conditionally includes FAQPage. The BaseLayout must handle arrays properly — verify `jsonLd` is iterated in BaseLayout.

### Phase 2: Add `noindex` to Skeleton Pages — DONE (Mar 22)

**Problem:** Pages with no meaningful content (rating 0, no enrichment, empty data) should not be indexed by Google until the enrichment agent processes them.

**File:** `src/pages/review/[slug].astro` (line 138-141)

**Criteria for `noindex`** — a page is skeleton/unenriched if ALL of these are true:
- `rating === 0` OR `rating === 5.0` (no real rating)
- `typical_results_timeline` is empty
- `pros` array is empty or contains only template text
- Not enriched (no `has_been_enriched` flag, or it's false)

```javascript
// Add after line 40 (after priceDisplay):
const isEnriched = lender.has_been_enriched === true;
const hasRealRating = lender.rating > 0 && lender.rating !== 5;
const hasRealContent = lender.typical_results_timeline?.trim().length > 0
  && lender.pros?.length > 0;
const isSkeleton = !isEnriched && !hasRealRating && !hasRealContent;
```

Then pass to BaseLayout:
```astro
<BaseLayout
  title={...}
  description={lender.description_short}
  jsonLd={jsonLd}
  noindex={isSkeleton}
>
```

**Expected impact:**
- Pages with real Google Maps ratings (23,479) stay indexed — they have SOME real data
- Pages with rating 0 (1,103) get noindexed — truly empty
- Pages with fake 5.0 AND no content (~3,246 minus any with content) get noindexed
- As enrichment agent processes them, `has_been_enriched = true` removes the noindex

### Phase 3: Fix Feature Checklist — DONE (Mar 22)

**Problem:** The feature checklist (lines 42-55) shows credit repair features (goodwill letters, cease & desist, debt validation, etc.) on ALL pages, including pawn shops, ATMs, check cashing, etc. This is misleading.

**Fix:** Define feature labels per category type. The `filter_type` in `categories.json` can drive this.

```javascript
// Category-aware feature labels
const creditRepairFeatures: Record<string, string> = {
  credit_monitoring: 'Credit Monitoring',
  all_three_bureaus: 'All Three Bureaus',
  goodwill_letters: 'Goodwill Letters',
  cease_desist_letters: 'Cease & Desist Letters',
  debt_validation: 'Debt Validation',
  credit_education: 'Credit Education',
  identity_theft_protection: 'Identity Theft Protection',
  score_tracking: 'Score Tracking',
  mobile_app: 'Mobile App',
  online_portal: 'Online Portal',
  personal_advisor: 'Personal Advisor',
  ai_powered: 'AI-Powered Tools',
};

const loanFeatures: Record<string, string> = {
  mobile_app: 'Mobile App',
  online_portal: 'Online Portal',
  personal_advisor: 'Personal Advisor',
  credit_education: 'Credit Education',
};

const serviceFeatures: Record<string, string> = {
  mobile_app: 'Mobile App',
  online_portal: 'Online Portal',
  personal_advisor: 'Personal Advisor',
  credit_education: 'Credit Education',
  score_tracking: 'Score Tracking',
};

// Select based on category filter_type
const featureLabels = category?.filter_type === 'credit-repair'
  ? creditRepairFeatures
  : category?.filter_type === 'loan'
    ? loanFeatures
    : serviceFeatures;
```

Then only render features that exist in the selected label set (already happens via `featureLabels[key] || key` but should explicitly filter).

### Phase 4: Request Re-indexing for Rating-0 Pages

After deploying the template fixes:

1. Rebuild site: `npm run build` in creditdoc/
2. Push to GitHub to trigger Vercel deploy
3. Use Google Indexing API to request re-crawl of the 1,103 rating-0 pages:
   ```bash
   python3 tools/gsc_indexing.py --site creditdoc --urls-from <list_of_rating0_slugs>
   ```
4. This tells Google to re-crawl these pages, picking up:
   - No more `reviewRating` in structured data (already fixed)
   - `noindex` meta tag (new)
   - Cleaned up FAQPage schema (new)

---

## File Reference

| File | What Changes |
|------|-------------|
| `src/pages/review/[slug].astro` | FAQPage conditional, noindex logic, category-aware features |
| `src/layouts/BaseLayout.astro` | Already supports `noindex` prop — no changes needed |
| `src/content/categories.json` | Already updated with `pawn-shops` and `atm` — no changes needed |
| `src/content/lenders/*.json` | No changes — enrichment agent updates these over time |

## Enrichment Pipeline Changes — DONE (Mar 22)

Changes made to `tools/creditdoc_content_drip.py`:
1. **`has_been_enriched = True`** now set on every enriched lender (line 815). This is the flag the template uses to determine if a page should be noindexed or not.
2. **Tier 0 added** to enrichment queue: skeleton/noindexed pages (rating 0, fake 5.0, no content) are now TOP PRIORITY before validated profiles.
3. **`pawn-shops` and `atm` added** to valid categories in enrichment prompt + validation list.

Changes made to `tools/creditdoc_validator.py`, `tools/creditdoc_qa_auditor.py`, `tools/creditdoc_qa_fixer.py`:
- All three scripts updated with `pawn-shops` and `atm` in `VALID_CATEGORIES` and category labels/descriptions.

Queue priority order: tier0 (skeleton) → tier1 (validated+website) → tier2 (validated) → tier3 (unvalidated+website)

## What the Enrichment Agent Should Do (Reminder)

When the enrichment agent processes a lender, it should:
1. Set `has_been_enriched: true` in the lender JSON
2. Set a real `rating` based on actual research (not 0, not default 5.0)
3. Fill in `typical_results_timeline`
4. Fill in `pros` and `cons` arrays
5. Fill in `guarantee_details`
6. Update `description_long` with real editorial content
7. Find and set `website_url` if missing

Once `has_been_enriched = true`, the page automatically gets indexed (noindex removed).

## Important: What NOT to Do

- **DO NOT delete the 27,828 lender JSON files** — they represent real businesses
- **DO NOT remove pages from `getStaticPaths`** — they should still be built (for internal linking, category counts, etc.), just noindexed
- **DO NOT bulk-rewrite ratings** — let the enrichment agent handle it properly
- **DO NOT touch the 23,479 pages with real Google Maps ratings** — those have legitimate data
- **DO NOT re-submit the entire sitemap** — only re-index the affected pages

---

## Archived Lender Directories (for reference)

All non-lending businesses removed during cleanup are in:
`/srv/BusinessOps/creditdoc/archived_lenders/`

Subdirectories: antiques, bakeries, cannabis, clothing, coin_shops, convenience_stores, department_stores, electronics, fashion_retail, food_cafes, food_misc, furniture, gas_stations, gift_shops, grocery, guns, gyms, jewelry, junkyards, liquor, misc_retail, misc_retail2, bulk_cleanup, supermarkets

Each has `_manifest.json` with date, reason, and business list.

## Non-Lending Businesses Spreadsheet

On Google Drive: "VPS Business Ops > CreditDoc > creditdoc_non_lending_businesses.xlsx"
Drive ID: `1lWtXibpWYFIZHPM5vnhTdDp_uhpnd7DWuHFkzmJFQ0Y`
Contains 1,648 remaining non-lending entries after all ATMs/banks/credit unions/pawn/finance businesses were removed.
