# City Guide Pages — SEO Audit & Fix Plan

**Date:** 2026-05-17
**Audited by:** Technical SEO, Schema, and Content Quality agents
**Overall Score:** 51/100 (technical) | Hub=61 | Category pages=22-28
**Status:** FIXES IN PROGRESS

---

## Executive Summary

Hub pages (/credit-guide/atlanta-ga/) are genuinely strong — real data, localized stats, legal citations, FAQPage schema. The category sub-pages (/credit-guide/atlanta-ga/credit-repair/) are HIGH RISK for Google's doorway page classifier: thin content, wrong FAQ links, no schema beyond breadcrumbs, identical templates. At 54,000 pages scale, this WILL trigger a quality demotion unless fixed.

---

## CRITICAL FIXES (All Template-Level)

### Fix 1: ItemList + CollectionPage Schema on Category Pages
**Impact:** Critical | **Effort:** Low | **Status:** TODO

Category pages have ONLY a BreadcrumbList. Need:
- `CollectionPage` schema (signals directory page type to Google)
- `ItemList` with `FinancialService` per provider (name, url, areaServed, serviceType)
- `AggregateRating` where ratings exist

Without this, Google cannot identify these as directory pages — they look like thin intermediate pages.

```json
{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "Credit Repair in Atlanta, GA — Local Directory",
  "url": "https://www.creditdoc.co/credit-guide/atlanta-ga/credit-repair/",
  "dateModified": "2026-05-17",
  "about": {
    "@type": "FinancialService",
    "serviceType": "Credit Repair",
    "areaServed": {"@type": "City", "name": "Atlanta", "containedInPlace": {"@type": "State", "name": "Georgia"}}
  }
}
```

Plus ItemList wrapping all providers:
```json
{
  "@type": "ItemList",
  "name": "Credit Repair Companies Serving Atlanta, GA",
  "numberOfItems": 17,
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "item": {"@type": "FinancialService", "name": "...", "url": "...", "areaServed": {...}}}
  ]
}
```

**File:** `src/pages/credit-guide/[slug]/[category].astro` — add jsonLd blocks

**Status: ✅ DONE — Worker `90bc7dde` deployed 2026-05-17**

Schema now on every category sub-page:
- `BreadcrumbList` — 4 items, final item now includes `item` URL (fixes breadcrumb bug too)
- `CollectionPage` — name, description, url, dateModified, about.serviceType, about.areaServed (City + State)
- `ItemList` — up to 12 providers as FinancialService with name, url, serviceType, areaServed (City for local, State for statewide)

Verified on `/credit-guide/atlanta-ga/credit-repair/`: 3 schema blocks, 17 items listed, dateModified present, breadcrumb URL fixed.

---

### Fix 2: Add Category Pages to Sitemap
**Impact:** Critical | **Effort:** Low | **Status:** ✅ DONE — Worker `90bc7dde` (same deploy)

Category sub-pages now in sitemap. Added 18 category slugs cross-product with city guide slugs in `ssrSitemapPages()` in `astro.config.mjs`.

**Result:** 970 credit-guide URLs now in sitemap (42 hubs + ~798 category sub-pages).

**File:** `astro.config.mjs` — lines 77-87

---

### Fix 3: Fix BreadcrumbList Bug
**Impact:** Medium | **Effort:** Low | **Status:** TODO

The final breadcrumb item (position 4) is MISSING the `item` URL property. Google Search Console flags this as a validation error and suppresses the breadcrumb rich result.

Current (broken):
```json
{"@type": "ListItem", "position": 4, "name": "Credit Repair in Atlanta"}
```

Fixed:
```json
{"@type": "ListItem", "position": 4, "name": "Credit Repair in Atlanta", "item": "https://www.creditdoc.co/credit-guide/atlanta-ga/credit-repair/"}
```

**File:** `src/pages/credit-guide/[slug]/[category].astro` — jsonLd breadcrumb array

---

### Fix 4: Localized Intro Paragraph per Category Page
**Impact:** High | **Effort:** Medium | **Status:** TODO

Category pages have ~950 words (mostly link text). NO localized editorial content. A human searching "credit repair atlanta" expects to learn something about credit repair IN Atlanta. Currently gets a list identical to what Google Maps shows.

**Solution:** Add 150-200 word intro pulled from existing data:
- State-specific laws for that category (already in state data)
- CFPB complaint count for that category in that state (already in regulatory layer)
- What to look for when choosing a provider in this state
- Georgia-specific regulations (licensing, fee caps, consumer protections)

This data ALREADY EXISTS in the hub page and regulatory layer. Template pulls it to category level automatically.

**Category-specific content hooks:**
| Category | Local data to pull |
|---|---|
| credit-repair | Georgia CROA rules, no state licensing requirement, upfront fee ban |
| personal-loans | Georgia usury cap, payday ban status, APR limits |
| emergency-cash | Payday alternative rules, title loan regulations |
| debt-relief | Georgia statute of limitations on debt, garnishment protections |
| build-credit | Secured credit card availability, credit union membership |
| free-help | HUD-approved counseling agencies, Legal Aid offices |
| business-loans | SBA district office, SCORE chapters, CDC/504 programs |

**File:** `src/pages/credit-guide/[slug]/[category].astro` — new section between hero and listings

**Status: ✅ DONE — deployed 2026-05-17**

Localized intros now render for 9 categories (credit-repair, personal-loans, emergency-cash, debt-relief, build-credit, free-help, business-loans, pawn-shops, payday-alternatives). Each pulls state-specific data: usury caps, payday ban status, credit repair regulations (upfront fee ban, cancellation period, bond requirements). Fallback generic intro for remaining categories. Links to state lending laws, full city guide, and quiz below each intro.

---

### Fix 5: Fix Logo Alt Text
**Impact:** High | **Effort:** Low | **Status:** ✅ DONE — deployed 2026-05-17

All provider logos previously rendered `alt=""`. Google uses alt text for entity recognition and accessibility scoring.

Fix: `alt={`${lender.name} logo`}` in the card template (both city-specific and statewide sections).

Verified on `/credit-guide/atlanta-ga/credit-repair/`: all logo images now have descriptive alt text (e.g., "Credit Repair Atlanta logo", "The Credit Conscious Network logo").

**File:** `src/pages/credit-guide/[slug]/[category].astro` (lines 278, 309) — category sub-page template only. LenderCard.astro NOT touched (used by hub pages, separate scope).

---

### Fix 6: Fix FAQ/Questions Mapping
**Impact:** High | **Effort:** Low | **Status:** ✅ DONE — deployed 2026-05-17

Current category→answer mapping is WRONG:
- Credit repair page shows "Does Credit Score Affect Car Insurance?" — irrelevant
- Emergency cash page shows "Small Business Loans Guide" — wrong category

**Root cause:** The `categoryAnswerKeywords` mapping uses broad terms that match unrelated answers.

**Fix:** Tighten keyword mapping + add category-specific inline FAQ content (2-3 questions answered directly on the page, not just linked).

Example for credit-repair:
- "How much does credit repair cost in Atlanta, GA?"
- "Is credit repair legal in Georgia?"
- "How long does credit repair take?"

These should be rendered directly on the page (not just links) AND wrapped in FAQPage schema.

**File:** `src/pages/credit-guide/[slug]/[category].astro` — categoryAnswerKeywords object + new FAQ section

---

### Fix 7: Add dateModified + Visible Freshness Signal
**Impact:** Medium | **Effort:** Low | **Status:** TODO

Zero freshness signals on any page. No `dateModified` in schema, no `<lastmod>` in sitemap, no visible "last updated" date. For financial services directories, Google expects freshness.

Fix: 
- Add `"dateModified": "2026-05-17"` to CollectionPage schema
- Add visible "Data last reviewed: May 2026" in hero section
- Add `<lastmod>` to sitemap entries

**File:** `src/pages/credit-guide/[slug]/[category].astro` + `astro.config.mjs`

---

### Fix 8: Cross-City Sibling Links
**Impact:** Medium | **Effort:** Low | **Status:** ALREADY DONE ✓

Category pages already link to same category in other state cities in the sidebar ("Credit Repair in Other Georgia Cities"). This was built into the template from the start.

---

## DOORWAY PAGE RISK MITIGATION

Google's doorway page criteria (September 2025 QRG):

| Criterion | Hub Page | Category Page | After Fixes |
|---|---|---|---|
| Unique localized content | ✓ (data, laws, stats) | ✗ (template only) | ✓ (intro paragraph) |
| Information beyond a list | ✓ (editorial prose) | ✗ (just a list) | ✓ (intro + FAQ) |
| Category-relevant questions | ✓ (7 FAQs) | ✗ (wrong links) | ✓ (inline FAQ) |
| Structured data | ✓ (WebPage+FAQ) | ✗ (breadcrumb only) | ✓ (Collection+ItemList) |
| Freshness signal | ✗ | ✗ | ✓ (dateModified) |
| Cross-linking pattern | ✓ | ✓ | ✓ |

**After all fixes: category pages become legitimate local directories with unique data, proper schema, and editorial context. The doorway page classifier should not trigger.**

---

## WHAT'S WORKING WELL (Don't Touch)

- Hub pages: genuine localized content (FDIC count, SBA data, state laws, HMDA table)
- SSR delivery via Cloudflare Workers — no JS rendering dependency
- Proper HTTPS/HSTS/security headers
- Self-referencing canonicals, no accidental noindex
- Quiz CTA placement (prominent in main content + sidebar)
- Internal linking density from hub to sub-pages
- Cross-city sidebar links in category pages
- Mobile viewport correct
- Consent Mode v2 GA4 implementation correct

---

## COMPETITIVE GAP — What #1 Results Have

Pages ranking #1 for "credit repair atlanta" have:
1. 1,500-2,500 words with editorial explanation of the service
2. Author byline or "reviewed by" attribution
3. Visible last-updated date
4. Comparison tables with methodology
5. Price ranges and qualification criteria
6. Real testimonials or aggregated review counts
7. State-specific regulatory context
8. ItemList or LocalBusiness schema

CreditDoc category pages currently have #0 of these. After fixes: will have #3, #4, #7, #8. Items #1, #2, #5, #6 require deeper content investment beyond template fixes.

---

## EXECUTION ORDER

1. **Schema (Fix 1 + 3)** — Pure code, instant across all pages
2. **Sitemap (Fix 2)** — Config change, enables crawl discovery
3. **Alt text (Fix 5)** — One-line template fix
4. **FAQ mapping (Fix 6)** — Tighten keyword map + add inline FAQ
5. **Localized intro (Fix 4)** — Pull existing data to category level
6. **Freshness (Fix 7)** — Add dateModified everywhere

All template-level. One deploy fixes 756+ existing pages and all future ones.

---

## FILES TO MODIFY

| File | Fixes |
|---|---|
| `src/pages/credit-guide/[slug]/[category].astro` | 1, 3, 4, 5, 6, 7 |
| `src/components/LenderCard.astro` | 5 |
| `astro.config.mjs` | 2 |
| `scripts/check_ssr_sitemap_parity.mjs` | 2 (already exempted) |
