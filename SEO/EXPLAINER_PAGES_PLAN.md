# CreditDoc — Data Explainer Page Plan

**Date:** 2026-05-17
**Purpose:** Single comprehensive page at `/about/creditdoc-data/` explaining every data element on our review pages. Demonstrates E-E-A-T authority, gives users confidence the data is real, and creates 18K+ internal link targets from every /review/ page.
**Status:** PLANNED — awaiting founder GO to build
**URL:** `/about/creditdoc-data/`

---

## What Already Exists

| Page | URL | Covers |
|---|---|---|
| Methodology | `/methodology/` | 5-factor rating system (Value, Effectiveness, Reputation, Transparency, Customer Experience) |
| Consumer Complaints Explainer | `/research/consumer-complaints/` | How we use CFPB data, what complaint trends mean |
| Lending Transparency | `/research/lending-transparency/` | HMDA mortgage approval data |
| State of Subprime | `/research/state-of-subprime-lending-2026/` | Research report |
| Editorial Policy | `/editorial-policy/` | Review standards, listing criteria |
| About | `/about/` | Mission, team |
| FAQ | `/faq/` | General questions |

---

## The Page: `/about/creditdoc-data/`

One comprehensive page with anchored sections. Each section of the /review/ template links to its relevant anchor on this page.

**File:** `src/pages/about/creditdoc-data.astro`

---

### Intro: Data Transparency Statement

Opening paragraph before any sections. Sets the tone for the whole page:

- CreditDoc is built on publicly verifiable data — every number on our pages has a source you can check yourself
- We use federal databases (CFPB, FDIC, HMDA, SBA), state regulatory filings, and verified company information
- Everything we display is designed to help you make better financial decisions — not to sell you a product or push you toward a specific company
- We don't accept payment for higher ratings or better placement. Our ratings come from data, not deals.
- Our methodology is completely transparent — this page explains exactly what every metric means, how it's calculated, and where the data comes from
- We believe you deserve to understand what you're looking at. Every label, score, and data point exists to benefit YOU — the consumer trying to navigate a confusing financial landscape
- If you find an error, contact us — we correct mistakes within 24 hours

- Our data is constantly updated — CFPB complaints sync daily, company information refreshes automatically, state regulatory changes are incorporated as they happen. You're never looking at stale information.
- Every page shows when it was last updated so you know how fresh the data is

This signals to both Google and users: "We have nothing to hide. Everything here exists to serve the user, and it's always current."

---

### Section 1: CreditDoc Rating (#rating)
- What the star rating IS (5-factor weighted average: Value, Effectiveness, Reputation, Transparency, Customer Experience)
- How each factor is scored (1.0–5.0)
- How it differs from Google reviews (methodology vs user votes) and BBB rating (operational vs satisfaction)
- Where the data comes from for each factor
- Why some companies score high on response but low overall
- Updates: recalculated when new data arrives

**Linked from:** Hero rating on every /review/ page

---

### Section 2: CFPB Transparency Report (#cfpb-data)
- What the CFPB is and why their data matters (federal consumer protection agency)
- "Complaints (12 months)" — what counts as a complaint vs an inquiry
- "Response Rate" — % of complaints company replied to (does NOT mean consumer was helped)
- "On-Time Response" — within CFPB's 15-day window
- "Resolved with Relief" — consumer received monetary or non-monetary relief
- Why a company can have 100% response and 0% relief (they reply but deny the claim)
- "Complaint Trend" — how we calculate Stable/Rising/Declining (12mo vs prior 12mo)
- "Most Common Complaint Categories" — CFPB product/issue taxonomy
- Why high volume ≠ bad company (Bank of America has 100K+ complaints but 67M customers)
- Color coding: green ≥90%, yellow ≥70%, red <70%
- Data freshness: synced daily from CFPB public API
- Limitations: complaints only, not positive experiences; self-reported by consumers

**Linked from:** CFPB card heading + footnotes on every /review/ page

---

### Section 3: CreditDoc Diagnosis (#diagnosis)
- What the "Doctor's Verdict" represents (editorial summary of strengths/weaknesses)
- How it's generated (from company data: services, pricing, complaints, user reviews)
- What "Ideal for" means (matched from category + service type analysis)
- What "Strength" means (highest-scoring factor or unique differentiator)
- What "Watch out for" means (lowest-scoring factor or common complaint theme)
- Why the medical metaphor (diagnosing the financial health of the company)
- How often it updates (when underlying data changes)

**Linked from:** Diagnosis card on every /review/ page

---

### Section 4: Pricing & Fees (#pricing)
- What "Starting Price" means (lowest advertised monthly cost for base service)
- Why some show "Free/mo" (no monthly subscription — BNPL lenders, free credit monitoring)
- Categories where pricing displays differently:
  - Credit repair: monthly subscription + setup fee
  - Personal loans: no monthly fee, pricing = APR/origination fee
  - BNPL: no monthly fee, pricing = interest on longer terms
  - Free services: genuinely $0
- What "Setup Fee" means (one-time enrollment cost)
- "Money-Back Guarantee" — what qualifies (written policy, not just cancellation)
- Source: company websites, verified quarterly

**Linked from:** Pricing badge + Quick Facts sidebar on every /review/ page

---

### Section 5: Similar Companies (#similar-companies)
- How similar companies are selected (same category + same state, sorted by rating)
- The ratings shown are THEIR ratings, not the main company's
- How we determine "similar" (category match, geographic proximity, service overlap)
- Why comparing is useful (apples-to-apples within your state/category)

**Linked from:** "Similar Companies" section heading on every /review/ page

---

### Section 6: State & Local Data (#state-data)
- What usury caps are and how they protect consumers
- Payday loan ban/allow status by state
- Credit repair regulations (upfront fee bans, cancellation periods, surety bonds)
- FDIC branch data — what it shows (physical presence in your area)
- How state laws affect which services are available to you
- Data sources: state statutes, FDIC BankFind, NMLS
- Update frequency: quarterly manual review of statute changes

**Linked from:** City guide intros, category sub-page intros, state pages

---

### Section 7: City Guides (#city-guides)
- What city guide pages are (local financial resource hubs for your specific city)
- How we determine which cities to cover (population, search demand, financial service density)
- What you'll find: local providers, state-specific regulations, HMDA lending data, localized questions
- Category sub-pages: drilling into specific needs (credit repair, loans, debt relief) for YOUR city
- How providers are listed (local companies serving your city first, then statewide providers)
- Why local matters: state laws determine what's legal, what fees are allowed, and what protections you have
- Cross-city links: comparing options in nearby cities in your state

**Linked from:** City guide hub pages, category sub-page intros

---

### Section 8: Company Reviews (#reviews)
- What a CreditDoc review page IS (a data profile, not an opinion piece)
- How companies get listed (we track every licensed financial services provider — not just ones who pay us)
- What's on every review page: rating, CFPB data, diagnosis, pricing, location, similar companies, FAQ
- How we verify company information (state licensing databases, NMLS, Secretary of State filings, company websites)
- What "processing_status" means internally (why some companies show and others don't yet)
- Our editorial independence: no company can pay to be listed, removed, or rated differently
- How often profiles are updated (data refreshes daily; editorial review on quarterly cycle)

**Linked from:** /review/ page breadcrumb or "About this page" link

---

### Section 9: Location & Map Data (#locations)
- Where geographic data comes from (company-reported addresses, state licensing records, FDIC BankFind)
- What the map shows (company headquarters or nearest branch — not necessarily where you'll be served)
- Multi-location companies: why we show individual branches (each may serve different areas, have different hours)
- "Serving [City]" vs "Located in [City]" — some companies serve your area remotely without a local office
- FDIC branch count: what it tells you (physical presence = regulated by state banking laws, FDIC insured deposits)
- How we determine which providers serve which cities (state licensing + service area declarations)
- Limitations: map pins are approximate, always verify hours/address with the company directly

**Linked from:** Map embed on /review/ pages, city guide provider listings

---

### Section 10: Regulatory Data (#regulatory-data)
- CreditDoc tracks regulatory information from multiple federal and state sources to give you a complete picture of how financial companies are governed
- Federal sources: CFPB (consumer complaints + enforcement), FDIC (bank supervision + insurance status), NMLS (licensing verification), SEC (public company filings), SBA (small business lending programs)
- State sources: state banking department records, Attorney General enforcement actions, state usury statutes, credit repair organization acts (CROA)
- What enforcement actions mean: a company with CFPB consent orders or state AG settlements has been formally disciplined — this is public record and factored into our assessment
- Licensing status: we verify companies are properly licensed in the states where they operate. Unlicensed operators are flagged.
- Why regulatory data matters to YOU: a company's regulatory history tells you how they've treated consumers in the past, whether they follow the law, and whether they're supervised by authorities who can intervene if something goes wrong
- This data is continuously refreshed as new enforcement actions, licensing changes, and regulatory filings become public

**Linked from:** CFPB card, city guide regulatory intros, /trends/ pages, state pages

---

## Internal Linking Strategy

Each /review/ page (18,971) links to one page with different anchors:
- Hero rating → `/about/creditdoc-data/#rating`
- CFPB card title → `/about/creditdoc-data/#cfpb-data`
- CFPB footnotes (* **) → `/about/creditdoc-data/#cfpb-data`
- Doctor's Verdict → `/about/creditdoc-data/#diagnosis`
- Pricing badge → `/about/creditdoc-data/#pricing`
- Similar Companies → `/about/creditdoc-data/#similar-companies`

City guides + category pages → `/about/creditdoc-data/#state-data`

**Total new internal links:** ~18,971 × 4-6 links per page = 75,000-115,000 contextual internal links to one authoritative page. Concentrates all link equity on a single high-authority explainer.

---

## E-E-A-T Impact

| Signal | Before | After |
|---|---|---|
| "Do they explain their methodology?" | One generic page | 7 deep-dive pages showing exactly how each metric works |
| "Is the data sourced?" | CFPB link at bottom | Every metric links to its own explainer with source attribution |
| "Do they understand limitations?" | No | Each page discusses limitations and edge cases |
| "Is this a real research operation?" | Unclear | /research/ section with 10+ data journalism pieces |
| "Can I trust the ratings?" | "CreditDoc methodology" link | Full breakdown of every factor, scoring, and update frequency |

---

## Build Steps

1. Create `src/pages/about/creditdoc-data.astro` — single page with all 6 sections, anchored headings, glass-card styling
2. Create tooltip component (`src/components/InfoTooltip.astro`) — small ⓘ icon next to each metric label, hover shows one-line summary, click goes to `/about/creditdoc-data/#anchor`
3. Update `src/pages/review/[slug].astro` — add InfoTooltip next to each metric label (Response Rate, On-Time Response, CreditDoc Rating, Starting Price, etc.)
4. Update city guide templates — link state data references to `#state-data` anchor
5. Add to sitemap (automatic — static prerender page)

## Tooltip UX

Each metric label on the /review/ page gets a small ⓘ icon. On hover (desktop) or tap (mobile), shows a one-line tooltip explaining the metric:

| Metric | Tooltip Text |
|---|---|
| Rating (4.2/5) | "CreditDoc's 5-factor score — Value, Effectiveness, Reputation, Transparency, Customer Experience" |
| Response Rate | "% of complaints the company replied to — not whether the consumer was helped" |
| On-Time Response | "% of responses within the CFPB's 15-day deadline" |
| Resolved with Relief | "% where the consumer received money back or a correction" |
| Starting Price | "Lowest monthly cost for the base service tier" |
| Doctor's Verdict | "Our editorial summary of this company's strengths and weaknesses" |

Each tooltip also links to the full explanation at `/about/creditdoc-data/#section`.

**Implementation:** Pure CSS tooltip (no JavaScript) using `title` attribute for accessibility + custom `::after` pseudo-element for styled popup. Falls back gracefully on mobile (tap → navigate to explainer page).

---

## Implementation Notes

- All pages go under `/research/` (existing section, already has 4 pages)
- Each page uses existing BaseLayout + glass-card styling
- Schema: `Article` with `author` (CreditDoc Research), `datePublished`, `dateModified`
- Add to sitemap via existing static prerender
- After pages are built: update /review/ template to add contextual links from each section heading to its explainer
- DO NOT change any data, ratings, or calculations — these pages EXPLAIN what already exists

---

## Relationship to Other Issues

- **Issue 3 (Free/mo):** Section 4 explains WHY some show "Free/mo" — makes it educational rather than confusing
- **Issue 4 (Templated FAQ):** This page is the OPPOSITE of thin content — deep, authoritative, unique
- **Issue 2 (Contradictory signals):** Sections 1-3 collectively explain why different numbers appear and what each measures
- **City guide intros:** Section 6 backs up the state-specific regulatory claims with methodology

---

## Files to Create/Modify

| File | Action |
|---|---|
| `src/pages/about/creditdoc-data.astro` | CREATE — the explainer page |
| `src/pages/review/[slug].astro` | MODIFY — add anchor links from section headings |
| `src/pages/credit-guide/[slug]/[category].astro` | MODIFY — link state data to #state-data |
| `src/pages/credit-guide/[slug]/index.astro` | MODIFY — link state data to #state-data |
