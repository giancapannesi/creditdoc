# CreditDoc SEO Fixes Applied — 2026-05-17

---

## Fix #1: Schema (CollectionPage + ItemList + BreadcrumbList)
**File:** `src/pages/credit-guide/[slug]/[category].astro`
**Status:** ✅ DONE — Worker `90bc7dde` deployed 2026-05-17
**Scope:** Category sub-pages only (new template created today)

Added three JSON-LD blocks to every category sub-page:
- `BreadcrumbList` — 4 items (Home → State → City Guide → Category), final item includes `item` URL
- `CollectionPage` — name, description, url, dateModified, about.serviceType, about.areaServed (City + State)
- `ItemList` — up to 12 providers as FinancialService with name, url, serviceType, areaServed

**Why:** Without structured data, Google treats category pages as thin intermediate pages (doorway page risk). CollectionPage signals "this is a directory." ItemList tells Google exactly what entities are listed.

---

## Fix #2: Category Sub-Pages Added to Sitemap
**File:** `astro.config.mjs` (lines 78–89)
**Status:** ✅ DONE — same deploy
**Scope:** Sitemap generation only

Cross-products 42 city guide slugs × 18 category slugs = 756+ category sub-page URLs now in sitemap. Added in the `ssrSitemapPages()` function alongside existing city guide hub URLs.

**Why:** Google can't crawl pages it doesn't know about. Category sub-pages had no sitemap entry and no external links pointing to them — invisible to crawlers.

---

## Fix #3: BreadcrumbList Final Item URL
**File:** `src/pages/credit-guide/[slug]/[category].astro`
**Status:** ✅ DONE — part of Fix #1 deploy
**Scope:** Category sub-pages only

The final breadcrumb item (position 4) now includes the `item` URL property. Without it, Google Search Console flags a validation error and suppresses the breadcrumb rich result.

---

## Fix #4: Localized Intro Paragraphs
**File:** `src/pages/credit-guide/[slug]/[category].astro`
**Status:** ✅ DONE — deployed 2026-05-17
**Scope:** Category sub-pages only

Added state-specific intro paragraphs for 9 categories (credit-repair, personal-loans, emergency-cash, debt-relief, build-credit, free-help, business-loans, pawn-shops, payday-alternatives). Each pulls real state data:
- Credit repair: upfront fee ban, cancellation period, bond requirements
- Loans: usury cap, payday ban status
- Emergency cash: payday alternative rules

Fallback generic intro for remaining categories. Links to state lending laws, full city guide, and quiz below each intro.

**Why:** Category pages had zero editorial content — just a list of providers. Google's doorway page classifier targets pages that offer nothing beyond a list. Localized intros add unique, data-driven content that varies by state.

---

## Fix #5: Logo Alt Text
**File:** `src/pages/credit-guide/[slug]/[category].astro` (lines 278, 309)
**Status:** ✅ DONE — deployed 2026-05-17
**Scope:** Category sub-pages only (hub pages and /review/ pages NOT touched)

Changed `alt=""` → `alt={`${lender.name} logo`}` on both city-specific and statewide provider logo images.

**Verified:** `curl` on `/credit-guide/atlanta-ga/credit-repair/` confirms alt text rendering (e.g., "Credit Repair Atlanta logo", "The Credit Conscious Network logo").

**Why:** Empty alt text means Google can't use logo images for entity recognition, and screen readers skip them entirely. Named alt text helps both accessibility and SEO entity signals.

---

## Fix #6: Tighten FAQ/Questions Keyword Mapping
**Files:**
- `src/pages/credit-guide/[slug]/index.astro` (line 96) — hub pages (PRE-EXISTING issue)
- `src/pages/credit-guide/[slug]/[category].astro` (lines 119–134) — category sub-pages

**Status:** ✅ DONE — deployed 2026-05-17
**Scope:** Both hub pages and category sub-pages

### The Problem

Both pages fetch "Related Questions" from the `/answers/` table by matching keywords against answer slugs. The keywords are too broad:

**Hub page (pre-existing, live for weeks):**
```
slug.ilike.*personal-loan*,slug.ilike.*credit*,slug.ilike.*debt*,slug.ilike.*business-loan*,slug.ilike.*borrow*
```
The term `*credit*` matches 15+ of 29 answers regardless of relevance. A user on the Atlanta hub page sees answers about car insurance, credit cards, and SBA loans all mixed together with no category relevance.

**Category sub-pages (built today):**
```javascript
'emergency-cash': ['emergency', 'cash', 'payday', 'quick-loan'],
'pawn-shops': ['pawn', 'collateral', 'cash'],
'free-help': ['free', 'counseling', 'non-profit', 'help'],
```
`'cash'` matches across categories. `'free'` matches any answer mentioning "free." Results are semi-random.

### The Fix

Replace broad single-word keywords with exact slug fragments that map correctly to specific answers.

**There are only 29 published answers.** Proper mapping by category:

| Category | Correct Answer Slugs |
|---|---|
| credit-repair | `how-to-build-credit-score-fast`, `build-credit-with-no-history`, `does-credit-score-affect-car-insurance` |
| personal-loans | `best-personal-loans-bad-credit`, `how-to-get-a-personal-loan`, `how-to-find-best-personal-loan-lenders`, `personal-loan-interest-rates-explained`, `how-much-can-you-borrow-with-your-credit-score` |
| emergency-cash | `best-personal-loans-bad-credit`, `how-much-can-you-borrow-with-your-credit-score` |
| debt-relief | `best-debt-consolidation-loans-bad-credit`, `debt-consolidation-vs-personal-loan`, `can-i-do-debt-consolidation-myself`, `can-you-do-debt-consolidation-yourself-guide` |
| build-credit | `build-credit-with-no-credit-history`, `build-credit-with-no-history`, `how-to-build-credit-score-fast`, `should-i-get-a-secured-credit-card-to-build-credit`, `how-to-apply-for-secured-credit-cards`, `top-secured-credit-cards` |
| free-help | `can-i-do-debt-consolidation-myself`, `can-you-do-debt-consolidation-yourself-guide` |
| business-loans | `are-small-business-loans-worth-it`, `small-business-loans-guide`, `small-business-loans-sba-merchant-cash-advances`, `how-to-apply-for-a-business-loan`, `how-to-get-an-sba-loan`, `business-loan-rates-fees-explained`, `business-line-of-credit-guide-new-llc-bad-credit` |
| credit-cards | `easy-approval-credit-cards`, `how-credit-card-interest-works`, `no-credit-check-cards-guide`, `should-i-get-a-secured-credit-card-to-build-credit` |
| credit-monitoring | `does-credit-score-affect-car-insurance`, `how-to-build-credit-score-fast` |
| banking | `how-much-can-you-borrow-with-your-credit-score` |

**Hub page fix:** Replace the single catch-all query with a curated set of the most universally relevant answers (personal loans, debt, credit building — the top traffic topics).

**Category sub-page fix:** Replace broad keywords with longer, more specific slug fragments (e.g., `'debt-consolidation'` instead of `'debt'`, `'business-loan'` instead of just `'business'`).

### Risk Assessment
- Hub page change: affects 42 live city guide pages. Low risk — only changes which 8 answers appear in the "Questions" section at bottom. No layout/structure change.
- Category sub-page change: affects the 756+ category pages. Low risk — same reasoning, just changes which 6 answers appear.
- No other pages affected. No schema change. No routing change.

---

---

## Fix #7: /trends/ Index Deduplication
**File:** `src/pages/trends/index.astro` (frontmatter only)
**Status:** ✅ DONE — deployed 2026-05-17
**Scope:** /trends/ index page ONLY. Individual detail pages (/trends/advance-america-brandon/ etc.) untouched — they have unique location data, addresses, map info.

**Problem:** The index listed every branch of multi-location companies as a separate row. Advance America had 107 rows, ACE Cash Express had 139, Check Into Cash had 37 — all showing identical CFPB data. Made the page look spammy (767 rows, only 378 unique companies).

**Root cause:** `cfpb-trends.json` was generated from the lenders DB where each branch is its own entry. CFPB reports at company level, not branch level, so all branches got the same complaint data copied.

**Fix:** Deduplicate by `company_name` in the index, keeping the shortest slug (canonical) as the link target. Total interactions counter still sums from ALL entries (real data). Individual detail pages remain — they have different addresses, map pins, and location-specific text.

**Result:** 767 rows → 378 unique companies. "Advance America" appears once. Links to `/trends/advance-america/` (canonical). All branch detail pages still accessible and returning 200.

---

## Fix #8: CFPB Metrics — Clear Labels + Explanatory Footnotes
**File:** `src/pages/review/[slug].astro` (lines 1034–1060)
**Status:** ✅ DONE — deployed 2026-05-17
**Scope:** All /review/ pages (18,971) — template-level change

**Problem:** "Issues Resolved: 100%" shown in green next to "Resolved with relief: 0.0%" was misleading. "Issues Resolved" sounds like the consumer's problem was fixed, but it actually means "the company sent a response." A company can have 100% response rate and 0% consumer relief — which is confusing without explanation.

**Fix:**
- "Issues Resolved" → **"Response Rate*"** (clearer label)
- "Timely Responses" → **"On-Time Response**"** (clearer label)
- Added footnote: `* Percentage of consumer complaints that received a company response (does not indicate the complaint was resolved in the consumer's favor)`
- Added footnote: `** Percentage of responses delivered within the CFPB's 15-day window`

**Result:** Users now understand what each metric actually measures. No data change — same numbers, same color coding. Just honest labeling.

---

## Fix #9: Data Transparency & Explainer Page
**File:** `src/pages/about/creditdoc-data.astro` (CREATED)
**Status:** ✅ DONE — deployed 2026-05-17
**URL:** `/about/creditdoc-data/`
**Scope:** New page — no existing pages modified

Comprehensive page explaining every data element on CreditDoc review pages:
1. **CreditDoc Rating** — 5-factor system, how it differs from Google/BBB
2. **CFPB Transparency Report** — response rate, on-time response, relief rate, complaint trend, limitations
3. **CreditDoc Diagnosis** — Doctor's Verdict breakdown
4. **Pricing & Fees** — what "Free/mo" means, category-specific pricing, setup fees, guarantees
5. **Similar Companies** — how they're selected, rating clarification
6. **State & Local Regulations** — usury caps, payday bans, CROA, FDIC branches
7. **City Guides** — what local hubs are, why local matters, how providers are sorted
8. **Company Reviews** — editorial independence, verification process, update frequency
9. **Location & Map Data** — sources, limitations, serving vs located
10. **Regulatory Data Sources** — federal (CFPB, FDIC, NMLS, SEC, SBA, HMDA) + state (AG, banking depts, statutes)

Opens with data transparency statement: all data publicly verifiable, no pay-for-placement, constantly updated, everything exists to benefit the consumer.

**Next step:** Add ⓘ tooltips on /review/ template linking to anchored sections, then link from city guides. (Separate fix — needs template change.)

---

---

## Fix #10: Company Count Showing "1" on City Guide Hub Pages
**File:** `src/pages/credit-guide/[slug]/index.astro` (lines 52, 247)
**Status:** ✅ DONE — deployed 2026-05-17
**Scope:** All 42 city guide hub pages

**Problem:** "Listed Companies" stat showed "1" for Austin (and similar wrong counts for other cities). Two bugs:
1. `getLendersByStateRuntime` was called with `limit=30` — fetching only 30 of potentially hundreds of state lenders
2. The count displayed `nearbyLenders.length` (city-name-filtered subset) instead of `validLenders.length` (all valid companies serving the state)

**Fix (v1 — caused production outage, see Fix #11):**
- Removed the `30` limit — function now uses its default of 200
- Changed stat display from `nearbyLenders.length` to `validLenders.length`

**Fix (v2 — deployed 2026-05-18, permanently correct):**
- Restored `limit=30` on `getLendersByStateRuntime` (only 12 displayed anyway)
- Added `getStateCountRuntime(stateAbbr, env)` — queries lightweight `state_lender_counts` view (no body_inline data)
- Count display uses `stateCount?.lender_count` with `validLenders.length` fallback

**Result:** Austin 2,219 / Atlanta 567 / Phoenix 566. Accurate counts from DB view. Zero worker CPU risk.

---

## Fix #11: Worker 1102 CPU Crash — Reverted Unlimited Fetch
**File:** `src/pages/credit-guide/[slug]/index.astro` (line 52)
**Status:** ✅ DONE — deployed 2026-05-18
**Scope:** All 42 city guide hub pages

**Problem:** Fix #10 removed the `limit=30` argument from `getLendersByStateRuntime`, meaning it used the default `limit=200`. States like Texas have 1,848+ lenders — fetching 200 rows with full `body_inline` JSON exceeded Cloudflare Worker CPU limits, causing error 1102 (16-byte error page). Pages intermittently crashed.

**Root cause:** The function fetches `body_inline` (full lender JSON) for every row. At 200 rows × ~5KB each = ~1MB of JSON parsing per request, hitting the Worker CPU ceiling.

**Fix:** Restored `limit=30` for display data. Moved count to `getStateCountRuntime()` which queries the `state_lender_counts` view — returns a single integer per state, zero CPU impact.

---

## Fix #12: Monitor Email Spam — Broken Cooldown
**File:** `/srv/BusinessOps/tools/creditdoc_site_monitor.sh` (line 157)
**Status:** ✅ DONE — 2026-05-18
**Scope:** Monitor alerting only (no site changes)

**Problem:** User received ~30 alert emails during the Fix #10/11 outage. The cooldown mechanism hashed the list of failing URLs (`md5sum` of `${FAILED[*]}`). Since different URLs failed each 5-minute run, the hash changed every time and cooldown never triggered.

**Fix:** Changed to a single cooldown key `batch_any_failure`. Any failure within the 1-hour window suppresses further emails regardless of which specific URLs are failing. Suppressed runs log to the monitor log file for debugging.

---

## Fixes NOT Applied (Documented Only)

The following were flagged by an external SEO review on 2026-05-16. They concern `/review/` and `/trends/` pages (NOT city guide pages). Documented in `SEO/REVIEW_TEMPLATE_ISSUES_2026-05-17.md`. **No action taken — founder approval required.**

- /trends/ index deduplication (Advance America 107× entries)
- /review/ contradictory rating signals (4.2 vs 4.9 on same page)
- "Free/mo" pricing field on non-subscription lenders (18,971 pages)
- Templated FAQ thin content on /review/ pages
- /sitemap.xml 404 (cosmetic — robots.txt already points to sitemap-index.xml)

---

## Summary

| Fix | File | Status | Scope |
|---|---|---|---|
| #1 Schema | [category].astro | ✅ Done | Category sub-pages |
| #2 Sitemap | astro.config.mjs | ✅ Done | Build config |
| #3 Breadcrumb URL | [category].astro | ✅ Done | Category sub-pages |
| #4 Localized Intros | [category].astro | ✅ Done | Category sub-pages |
| #5 Alt Text | [category].astro | ✅ Done | Category sub-pages |
| #6 FAQ Mapping | index.astro + [category].astro | ✅ Done | Hub + Category pages |
| #7 Trends Dedup | trends/index.astro | ✅ Done | /trends/ index only |
| #8 CFPB Labels | review/[slug].astro | ✅ Done | All /review/ pages |
| #9 Explainer Page | about/creditdoc-data.astro | ✅ Done | New page |
| #10 Company Count | credit-guide/[slug]/index.astro | ✅ Done (v2) | All hub pages |
| #11 Worker CPU Crash | credit-guide/[slug]/index.astro | ✅ Done | All hub pages |
| #12 Monitor Spam | tools/creditdoc_site_monitor.sh | ✅ Done | Alerting only |
