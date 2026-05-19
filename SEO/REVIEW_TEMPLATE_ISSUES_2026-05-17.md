# Review/Trends Template Issues — Flagged 2026-05-17

**Source:** External SEO review (unverified agent output — needs manual confirmation before acting)
**Status:** DOCUMENTED ONLY — DO NOT ACT WITHOUT FOUNDER APPROVAL
**Scope:** /review/ pages (18,971) and /trends/ index. NOT the city guide pages.

---

## Issue 1: /trends/ Index Deduplication

**Claim:** "Advance America" appears 100+ times, every branch as separate entry.

**Verified:** YES — grep confirms 107 occurrences of "Advance America" on /trends/ page.

**Impact:** Makes the trends index look spammy. Federal CFPB data is a moat — currently looks broken.

**Potential fix:** Collapse on normalized company name in the index. Detail pages can stay; index shows one canonical entry per brand.

**BUT:** Need to understand HOW the trends index is generated before proposing a fix. The data comes from CFPB which reports per-location. The dedup logic might be intentional or might have a reason.

**FIXED 2026-05-17:** Index deduplicated by company_name (shortest slug = canonical link). Detail pages untouched. 767→378 on index. See `fixes_applied.md` Fix #7.

---

## Issue 2: Affirm Page — Contradictory Signals

**Claim:** Same page shows 4.2/5 hero rating, 4.9/5 in Similar Companies card, "100% Issues Resolved", and "Doctor's Verdict" that contradicts CFPB data (6,724 complaints, 0.0% resolved with relief).

**Verified:** YES — curl confirms 4.2/5, 4.9/5, "Free/mo", "Doctor's Verdict", "Issues Resolved" all on same page.

**Impact:** Internal inconsistency = low-quality signal to both Google and users.

**Potential fix:** Single source-of-truth rating propagated everywhere. Non-generic verdict templated against actual data.

**BUT:** The rating system, Doctor's Verdict, and "Issues Resolved" metric all come from different data sources/calculations. Need to understand what each actually measures before declaring them "contradictory." They might represent different things (Google rating vs CreditDoc score vs CFPB resolution vs complaint response rate).

**FIXED 2026-05-17:** Relabeled "Issues Resolved"→"Response Rate*" and "Timely Responses"→"On-Time Response**" with footnotes explaining what each metric actually measures. The 4.9 vs 4.2 "contradiction" was FALSE — 4.9 is a different company in the Similar section, not Affirm. See `fixes_applied.md` Fix #8.

---

## Issue 3: "Free/mo" Pricing Field Bleed

**Claim:** "Starting Price: Free/mo" shows on Affirm (a BNPL lender that makes money on interest). Credit-repair template artifact.

**Verified:** YES — "Free/mo" appears twice on the Affirm page.

**Impact:** Misleading to users. Technically defensible (no monthly subscription) but confusing.

**Potential fix:** Context-aware pricing by category (subscription cost for credit repair, APR range for lenders, fee structure for banks).

**BUT:** This affects 18,971 pages. Any pricing field change is a BULK OPERATION requiring founder approval. The "Free/mo" might be intentional for lenders that genuinely don't charge monthly fees (many don't). Need category-level review first.

**DO NOT FIX without understanding the pricing data model and getting approval.**

---

## Issue 4: Templated FAQ on Review Pages

**Claim:** FAQ block is auto-generated thin content. "Is Affirm legitimate? Yes, registered in San Francisco." "How long does Affirm take to show results? Results vary by service type."

**Verified:** NOT YET VERIFIED against live page (would need to curl and check FAQ section).

**Impact:** If true, this is exactly what Google's Helpful Content Update targets.

**Potential fix:** Per-category FAQ templates with category-appropriate questions.

**BUT:** This is a content quality issue across 18,971 pages. Any fix is a massive template change. The FAQ generation logic needs to be understood first — it may already have category-aware branching that's just poorly calibrated.

**DO NOT FIX without reading the FAQ generation code and getting approval.**

---

## Issue 5: /credit-guide/charlotte/ → 404

**Claim:** Charlotte city guide returns no content.

**Verified:** FALSE. The correct URL is `/credit-guide/charlotte-nc/` which returns 200. Reviewer used wrong slug (no state suffix).

**No action needed.**

---

## Issue 6: /sitemap.xml → 404

**Claim:** /sitemap.xml returns soft 404, should redirect to sitemap-index.xml.

**Verified:** PARTIALLY TRUE. /sitemap.xml returns 404 BUT robots.txt already declares `Sitemap: https://www.creditdoc.co/sitemap-index.xml`. Google reads robots.txt first and follows that declaration. This is cosmetic.

**Potential fix:** Add a redirect rule in Cloudflare for /sitemap.xml → /sitemap-index.xml.

**Low priority — Google is already finding the sitemap correctly via robots.txt.**

---

## TRUST NOTES

This review came from an automated agent. Previous experience (lies_caught #13) shows agents can:
- Report "missing" things that actually exist (SSR fallbacks handle them)
- Conflate different metrics as "contradictory" when they measure different things
- Propose bulk fixes without understanding the data model

Before acting on ANY of these:
1. Read the relevant code that generates the flagged content
2. Understand what each data field actually represents
3. Check if there's a reason it's built this way
4. Get explicit founder approval before changing anything that touches 18K+ pages
