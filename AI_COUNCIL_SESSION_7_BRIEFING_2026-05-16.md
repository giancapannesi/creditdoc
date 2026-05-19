# AI Council Session 7 — Briefing Document
## CreditDoc Data Integrations & Monetization Sequencing
### May 16, 2026

---

## Council Roster (Session 7)
- **Elon Musk** — First principles, 10x thinking, API-as-product
- **Jack Dorsey** — Fintech, underserved markets, simplicity
- **Chamath Palihapitiya** — Unit economics, growth metrics, market timing
- **Naval Ravikant** — Leverage, compounding, philosophical clarity
- **Gary Vaynerchuk** (NEW) — Content distribution, brand, social proof, attention economy
- **Peter Thiel** (NEW) — Monopoly strategy, contrarian bets, 0-to-1 thinking

**Dropped from last session:** Bill Ackman, Steve Jobs

---

## State of CreditDoc (May 16, 2026)

### What's Live
- 15,529 lender profiles (SSR on Cloudflare Workers)
- 9.8M CFPB complaints + regulatory badges on matched pages
- 27,832 FDIC institutions + 78,347 branch locations
- 373K SBA loans with national + state rankings
- 7,193 entity matches (CFPB → FDIC → NCUA → lender directory)
- ~250 city guides (growing at 10/day)
- 89 financial wellness guides
- 10-module Credit Fundamentals course + 21-day email drip
- Borrowing power quiz
- 148 inline keyword→money page mappings (SSR linker)
- llms.txt rebuilt with 187 verified URLs + weekly cron
- Course + quiz CTAs on homepage, all review pages, answers, blog sidebar

### Traffic & Revenue
- **25,000 impressions/month** (Google Search Console)
- **27 clicks/month** (CTR ~0.1%)
- **Zero CreditDoc revenue** — CJ approved but individual advertisers rejecting (low traffic)
- **First paying customer** on TraderTrac/InsiderEdge ($119/yr, May 15)

### What the Last Council Said (Session 4 Priority Stack)
1. Accelerate city guides (10-15/day) ← IN PROGRESS
2. Internal linking sprint ← DONE (148 mappings)
3. Indexing pipeline priority ← DONE (dedup + reorder)
4. Original research piece ← NOT STARTED
5. llms.txt ← DONE
6. Light social media ← NOT STARTED
7. Affiliate applications ← CJ approved, individual rejections

---

## Items for Council Review

### Tier A — Quick Wins (Free, 1-2 days each)

**A1. Freddie Mac PMMS Mortgage Rate Widget**
Weekly 30yr/15yr/ARM rates. Free API. Auto-updating widget on mortgage/bank pages.
- Freshness signal for YMYL pages
- ~4 hours to build

**A2. OFR Federal Funds / SOFR Rate Feed**
Live Fed Funds and SOFR rates on HELOC/ARM/business credit pages.
- Auto-updates when Fed moves
- ~4 hours to build

**A3. HUD Housing Counselor API**
ZIP-based directory of HUD-approved housing counselors. Free.
- Trust signal on low-credit pages and city guides
- Consumer advocacy backlink magnet
- ~6 hours to build

### Tier B — High-Moat Data Layer (2-3 weeks)

**B1. CFPB HMDA Lending Data**
Denial rates, approval rates, income brackets served — per lender, per geography.
- "Community Lending Score" — unique content no competitor has
- Entity resolution pipeline already built (same FDIC cert numbers)
- Press-linkable (journalists love lending discrimination data)
- 2-3 weeks dev time

### Tier C — Monetization (Need Traffic)

**C1. Lendflow SMB Marketplace** — 75+ SMB lenders, revenue-share model
**C2. Soft Pull Pre-Qualification Widget** — real-time pre-qual, warm leads
**C3. Plaid Income Verification** — 2-3x CPL on pre-verified leads

### Previously Parked (B2B Fintech Layer)
- FDIC Call Report capital allocation scoring
- CRA rating enrichment
- Open Banking tech-stack fingerprinting
- Stateless matching engine API
- B2B SaaS distribution (GET /v1/lenders/match)

---

## Questions for the Council

1. **Sequencing:** Do the Tier A quick wins first, or does something else deserve priority over city guides?
2. **HMDA:** Worth the 2-3 week investment now, or wait until traffic proves the regulatory moat works?
3. **Social angle:** How do we turn these data layers into shareable content that drives awareness?
4. **Monopoly question:** Which of these creates an unassailable competitive moat?
5. **What are we NOT seeing?** What opportunity is obvious from the outside that we're missing?
6. **The B2B play:** Is there an earlier trigger than 25K visitors for the API/embedded finance path?
