# CreditDoc — AI Council Execution Plan

**Compiled from 5 Council Sessions — May 13, 2026**
**Council: Musk, Jobs, Dorsey, Ackman, Chamath Palihapitiya, Naval Ravikant, Gary Vaynerchuk**

---

## Vision (Council Consensus)

CreditDoc is an **embedded finance marketplace** — a directory frontend with a loan origination engine at the back. Everything built today (30K pages, CFPB data, city guides, content) is infrastructure feeding the conversion layer.

**The path:** SEO Traffic → Quiz Capture → Email Nurture → Origination Chain

**Current state:** 26 clicks/month, 8,086 impressions, ~287 indexed pages of 15,529+. YMYL sandbox expected 6-12 months. $0 infrastructure cost. 1 founder + AI agents.

**Revenue gates:**
- Phase 1 (now–25K visitors): Affiliates ($200–2K/mo)
- Phase 2 (25K+ visitors): MoneyLion/Lendio embedded origination ($8K–50K/mo)
- Phase 3 ($50K/mo+): BrokerOS direct deals ($50K–120K/mo)

---

## Priority Stack (Ordered by Impact)

### #1 — Accelerate City Guides to 10–15/day
**Council source:** Dorsey (Session 4), Musk (Session 4), Chamath (Session 4)
**Status:** Currently 5/day at 09:00 UTC. Pipeline LIVE with 6 cities published.

**Why #1:** City guides rank positions 1-5 almost immediately (local YMYL is less competitive). Every city guide is a landing page for the quiz funnel. At 15/day, you cover 500 cities in ~5 weeks. Musk: "500 city guides + 2K profiles = inevitable traffic."

**Actions:**
- [ ] Increase cron from 5/day to 10/day (double the batch in `creditdoc_city_guide_generator.py`)
- [ ] Validate OpenRouter rate limits can handle 10/day without throttling
- [ ] Monitor indexing rate — if Google indexes city guides faster than other page types, push to 15/day
- [ ] Priority order: population × FDIC branch density (already implemented)

**Timeline:** Week 1
**Effort:** Low — config change + monitoring

---

### #2 — Internal Linking Sprint
**Council source:** Dorsey (Session 4), Musk (Session 4)

**Why:** 287 pages indexed out of 15,529+. Internal links from indexed pages to unindexed pages are the fastest way to get Google to crawl and index more content. Every indexed page is a doorway.

**Actions:**
- [ ] Export list of 287 indexed pages from GSC
- [ ] Identify highest-value unindexed pages (city guides, /best/* money pages, state hubs)
- [ ] Add contextual internal links from indexed pages to target unindexed pages
- [ ] Use existing `inline-linker.ts` SSR system — add new phrase→URL mappings for city guides and money pages
- [ ] Cross-link city guides ↔ state pages ↔ /best/* pages ↔ lender reviews

**Timeline:** Week 1–2
**Effort:** Low–Medium

---

### #3 — Credit Repair Quiz → Homepage + Content
**Council source:** Dorsey (Session 5), Musk (Session 5), Jobs (Session 5), Chamath (Session 5), Naval (Session 5)

**Why:** The quiz is the bridge between content and commerce. Template already exists at `/tools/borrowing-power-quiz/` (908 lines, LIVE). Build ONE quiz (credit repair — strongest pillar), wire it everywhere, measure before replicating.

**Quiz Architecture (Musk):**
```
Quiz Config:
- pillar: "credit-repair"
- questions: [5 questions with branching logic]
- recommendations_source: database query by pillar + location + score range
- email_capture: after Q3
- result_page: personalized lender recs + CFPB trust data
- cta: "/best/credit-repair-companies/"
```

**Placement Hierarchy (Dorsey + Jobs):**
1. **Homepage hero** — "What do you need help with?" → quiz flow (primary CTA)
2. **End of every credit repair wellness guide** — contextual CTA
3. **End of every credit repair answer page** — contextual CTA
4. **Embedded in credit repair city guides** — "Looking for credit help in [City]?" pre-filled with location
5. **Sidebar on credit repair lender review pages** — "Compare your options"
6. **Standalone at `/qualify/credit-repair/`** — direct-intent landing page

**Pre-fill from context (Musk):** If visitor arrives from Denver city guide → pre-fill Denver, CO. From credit repair article → pre-fill intent. Reduce friction.

**Data logging from day one (Musk):**
```sql
CREATE TABLE quiz_completions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pillar TEXT NOT NULL,
  answers JSONB NOT NULL,
  location TEXT,
  email TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  source_page TEXT
);
```
Log every completion to Supabase even before any affiliate is connected. This data proves demand to future partners.

**Actions:**
- [ ] Build credit repair quiz from existing template
- [ ] Create reusable quiz component that accepts config (one component, N configurations)
- [ ] Wire to homepage as hero CTA
- [ ] Add end-of-article CTA to all credit repair wellness guides
- [ ] Add sidebar CTA to credit repair lender review pages
- [ ] Create `/qualify/credit-repair/` standalone page
- [ ] Create `quiz_completions` Supabase table
- [ ] Log all completions with source_page tracking

**Timeline:** Week 1–2
**Effort:** Medium

---

### #4 — Indexing Pipeline Priority Reorder
**Council source:** Musk (Session 4)

**Why:** Not all pages are equal. City guides rank fastest. /best/* money pages have highest conversion potential. Indexing API has a 200/day quota shared across sites. Prioritize what matters.

**Current order:** Mixed
**New order:**
1. City guides (rank fastest, quiz landing pages)
2. /best/* money pages (highest conversion)
3. State hub pages
4. /answers/* pages
5. Everything else

**Actions:**
- [ ] Update `creditdoc_priority_indexing.py` to enforce this tier order
- [ ] Ensure city guides get submitted within 1 hour of generation
- [ ] Monitor indexing success rate by page type

**Timeline:** Week 1
**Effort:** Low

---

### #5 — "Credit Repair 101" Course (7 Modules)
**Council source:** Dorsey (Session 5), Chamath (Session 5), Naval (Session 5), Jobs (Session 5)

**Why:** Courses turn isolated articles into a structured journey. AI-proof content (AI can answer questions, can't replicate a 7-module course with progress tracking). Highest-converting email capture format (40-60% open rates vs 20% for marketing). Built mostly from existing content (85 wellness guides + 26 answer pages).

**Course Modules:**

| # | Module | Content Source | New Writing |
|---|--------|---------------|-------------|
| 1 | Understanding Your Credit Report | Existing wellness guides | Minimal — reorganize |
| 2 | Your Rights Under Federal Law | Regulatory data + state pages | Some — synthesize |
| 3 | How to Dispute Errors | Existing answer pages | Minimal — reorganize |
| 4 | Choosing a Credit Repair Company | CFPB data + /best/ page | New — use database |
| 5 | Building Credit After Repair | Existing wellness guides | Minimal |
| 6 | Avoiding Predatory Lenders | CFPB enforcement data | New — use database |
| 7 | Your 90-Day Action Plan | Quiz results | New — dynamic |

**Delivery model (Chamath):**
- Email drip: 1 module every 3 days = 21-day sequence
- Email capture at Module 1 ("Get Module 1 free. Enter your email for the full course.")
- Course completion certificate (shareable badge for social media)
- Module 4 naturally recommends companies from database (ranked by CFPB resolution rate)
- Module 5 naturally recommends secured cards and credit builder products

**Monetization hooks:**
- Module 4 → credit repair affiliates ($80–200/sale)
- Module 5 → secured card + credit builder affiliates
- Module 7 → quiz → personalized recommendations → affiliate/origination

**Learn → Assess → Act Framework (Naval):**
```
LEARN: Course modules (free, builds trust, captures email)
    ↓
ASSESS: Quiz (evaluates specific situation)
    ↓
ACT: Personalized recommendations (database + CFPB data)
    ↓
CONVERT: Apply (affiliate → future embedded origination)
```

**Actions:**
- [ ] Audit existing wellness guides and answer pages for course-ready content
- [ ] Design course hub page template (progress tracking, module navigation)
- [ ] Build Module 1 from existing content
- [ ] Set up email drip infrastructure (capture at Module 1, deliver over 21 days)
- [ ] Build remaining 6 modules
- [ ] Create completion certificate (shareable badge)
- [ ] Wire course CTAs into wellness guides ("Want the full course? Start here")

**Timeline:** Week 3–4
**Effort:** Medium

---

### #6 — One Original Research Piece
**Council source:** Dorsey (Session 4), Chamath (Session 4)

**Why:** Backlinks. One data-driven research piece using CFPB data (which you uniquely have in analyzable form) → pitch to financial journalists → earn links → domain authority boost.

**Framing (CRITICAL — founder directive):** POSITIVE only. Not "worst lenders" — instead "America's Most Responsive Lenders" or "Which States Have the Highest Consumer Complaint Resolution Rates?" Make lenders WANT to be cited.

**Actions:**
- [ ] Query regulatory.db for compelling positive-frame story (highest resolution rates by state, by lender size, trend over time)
- [ ] Write research piece with charts and methodology
- [ ] Publish on CreditDoc at `/research/` (already have `/research/consumer-complaints/` live)
- [ ] Create media pitch list (financial journalists, personal finance bloggers)
- [ ] Pitch via Harvey email

**Timeline:** Week 2–3
**Effort:** Medium

---

### #7 — llms.txt + Structured Data
**Council source:** Dorsey (Session 4)

**Why:** Opens AI citation channel. When LLMs like ChatGPT, Perplexity, and Google AI Overviews reference financial data, having structured data and llms.txt makes CreditDoc citable. 30 minutes of work for a long-term channel.

**Actions:**
- [ ] Create `/llms.txt` with site structure, data sources, and key pages
- [ ] Verify JSON-LD structured data on all page types (lender reviews, city guides, money pages)
- [ ] Add `FinancialService` schema to lender review pages
- [ ] Add `FAQPage` schema to answer pages and city guide FAQ sections

**Timeline:** Week 2
**Effort:** Low (30 min for llms.txt, 1-2 hours for schema audit)

---

### #8 — Light Social Media (2-3/week)
**Council source:** Chamath (Session 4), Gary V (implied)

**Why:** Non-SEO traffic channel + brand awareness. Not heavy investment — just data insights from CFPB analysis shared on X and LinkedIn. 2-3 posts per week.

**Content types:**
- CFPB data insights ("Did you know? Lenders in Texas resolve 87% of complaints within 15 days")
- Credit tips from course content
- Quiz promotion ("Find out which credit repair approach is right for you")

**Actions:**
- [ ] Set up CreditDoc X account (if not exists) and LinkedIn company page
- [ ] Create 2-3 data insight posts per week from CFPB data
- [ ] Schedule via Blotato
- [ ] Track referral traffic from social

**Timeline:** Week 3+ (ongoing)
**Effort:** Low

---

### #9 — Shareable Quiz Results (Viral Loop)
**Council source:** Chamath (Session 5)

**Why:** Every quiz completion becomes a potential share. "I just found out I qualify for a 4.9% personal loan — check yours at creditdoc.co." Organic social distribution.

**Actions:**
- [ ] Generate unique results URL for each quiz completion
- [ ] Add share buttons (X, LinkedIn, Facebook, WhatsApp)
- [ ] Design shareable results card ("Your CreditDoc Financial Profile: Score Range 580-620 | Best Options: 3 lenders in Houston")
- [ ] The shared link brings new visitors to the quiz → viral loop

**Timeline:** Week 5–6 (after quiz is proven)
**Effort:** Low

---

### #10 — Apply to Accessible Affiliate Programs
**Council source:** Chamath (Session 4)

**Status:** CJ Affiliate approved at network level. Individual advertisers rejecting due to low traffic.

**Why:** Revenue infrastructure for Phase 1. Don't wait for CJ advertisers to accept — apply to programs with lower thresholds.

**Target programs (lower thresholds):**
- LeadNetwork
- LeadsMarket
- Self (credit builder)
- DisputeBee (credit repair)
- Direct affiliate programs from smaller lenders in database

**Actions:**
- [ ] Apply to lower-threshold affiliate programs
- [ ] Re-apply to CJ individual advertisers when traffic hits milestones (per IMPLEMENTATION_PLAN.md gates)
- [ ] Set up tracking for affiliate link clicks from quiz results and course modules

**Timeline:** Week 4+
**Effort:** Low

---

## Future Courses (After Credit Repair 101 Proves the Model)

| Priority | Course | Modules | Target Audience | Monetization |
|----------|--------|---------|-----------------|-------------|
| 2 | First-Time Borrower's Guide | 5 | Young adults, immigrants | Personal loan + credit builder affiliates |
| 3 | Small Business Funding Guide | 6 | Entrepreneurs | Business loan quiz → BrokerOS |
| 4 | Debt Freedom Roadmap | 6 | People in debt | Debt relief affiliates ($500–2K/enrollment) |
| 5 | Credit Building from Zero | 5 | Credit invisible | Secured cards + credit builder affiliates |

---

## Future Quiz Rollout (After Credit Repair Quiz Proves the Model)

| Priority | Quiz | Trigger |
|----------|------|---------|
| 2 | Personal Loans Quiz | Credit repair quiz shows >60% completion rate |
| 3 | Business Loans Quiz | BrokerOS integration ready |
| 4 | Debt Relief Quiz | Debt relief content pillar built out |
| 5-10 | Credit cards, auto, mortgage, student loans, banking, credit building | Pillar by pillar based on traffic data |

---

## CFPB Data Positioning (Founder-Approved Framing)

**DO:** "This lender has an 80% complaint resolution rate" — make lenders WANT to be featured.
**DO:** "America's Most Responsive Lenders" — positive frame.
**DO:** Consumer Trust Profile (not Report Card) — platform positioning.
**DON'T:** Grade or rank lenders negatively.
**DON'T:** "Most Complained-About Lenders" — adversarial framing.
**DON'T:** Pitch lenders until traffic proves value — "I will burn that relationship."

---

## Timeline Summary

| Week | Focus | Key Deliverable |
|------|-------|----------------|
| 1 | City guides 10-15/day + internal linking + indexing reorder | Infra acceleration |
| 1-2 | Credit repair quiz build + wire to site | Conversion infrastructure |
| 2 | llms.txt + structured data audit | AI citation readiness |
| 2-3 | Original research piece (positive CFPB) | Backlink campaign |
| 3-4 | Credit Repair 101 course (7 modules) | Email capture + trust engine |
| 3+ | Social media 2-3/week | Brand + non-SEO traffic |
| 4+ | Affiliate applications (lower-threshold) | Revenue infrastructure |
| 5-6 | Shareable quiz results | Viral loop |
| 7-8+ | Second quiz (personal loans) + second course | Pillar expansion |

---

## Success Metrics (Chamath's 6/7 Green Signals)

| Signal | Current | Target (Month 6) | Target (Month 12) |
|--------|---------|-------------------|---------------------|
| Pages indexed | ~287 | 2,000+ | 5,000+ |
| Monthly clicks | 26 | 500+ | 5,000+ |
| Monthly impressions | 8,086 | 50,000+ | 200,000+ |
| Quiz completions | 0 | 100/mo | 1,000/mo |
| Email list | 0 | 500 | 5,000 |
| Course enrollments | 0 | 200 | 2,000 |
| Revenue | $0 | $200-2K/mo (affiliates) | $8K-50K/mo (embedded) |

---

## The Founder's Commitment

*"This founder doesn't give up, he only doubles down."*

The math works. The infrastructure is built. The data moat (9.8M CFPB complaints) is real. $0 operating cost = infinite runway. The only risk is stopping before the S-curve inflects.

**Dorsey:** "Yes, unequivocally has legs. Only risk is giving up before it compounds."
**Musk:** "500 city guides + 2K profiles = inevitable traffic."
**Chamath:** "6/7 signals green. $0 infrastructure = infinite runway. Keep building."

---

*Execution plan compiled from AI Council Sessions 1-5, May 13, 2026.*
*Council: Jack Dorsey, Elon Musk, Steve Jobs, Bill Ackman, Chamath Palihapitiya, Naval Ravikant, Gary Vaynerchuk*
