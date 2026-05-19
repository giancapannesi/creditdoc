# CreditDoc — Strategic Execution Plan

**Prepared: May 13, 2026**
**Engagement: Post-Advisory Council Strategy Activation**
**Principal: Gian Capannesi, Founder — Cosmic Phoenix LLC**
**Advisory Council: Dorsey, Musk, Jobs, Ackman, Palihapitiya, Ravikant, Vaynerchuk**

---

## Executive Summary

CreditDoc is an embedded finance marketplace disguised as a consumer-finance directory. The front end — 18,968 lender profiles, 215 comparisons, 41 blog posts, 27 listicles, 26 answer pages, 11 city guides, and a regulatory intelligence layer built on 9.8M CFPB complaints — generates organic search traffic. The back end — quiz funnels, email nurture sequences, and loan origination infrastructure — converts that traffic into revenue through affiliate, embedded origination (MoneyLion/Lendio at scale), and direct brokerage (Cosmic Phoenix BrokerOS for SMB).

The business is pre-revenue. 26 monthly clicks. 8,086 impressions. ~287 indexed pages. Operating cost: $0/month infrastructure (Cloudflare Workers + Supabase free tier). One founder plus AI automation.

This plan translates the Advisory Council's strategic direction into a week-by-week operating cadence, starting today, with clear ownership, dependencies, and measurable gates. Every initiative traces back to one objective: reach the 25,000-visitor threshold that unlocks Phase 2 embedded finance revenue.

---

## I. Current State Assessment

### Asset Inventory (as of May 13, 2026)

| Asset | Count | Status |
|-------|-------|--------|
| Lender profiles (ready_for_index) | 15,529 | Live, SSR on Cloudflare Workers |
| Lender profiles (raw/quarantine/pending) | 3,439 | Processing pipeline |
| Comparisons | 215 | Live |
| Blog posts | 41 | Live, 2/day auto-generation |
| Listicles (/best/* money pages) | 27 | Live |
| Answer pages (/answers/*) | 26 | Live, 1/weekday auto-generation |
| City guides (/credit-guide/*) | 11 | Live, 5/day auto-generation |
| Regulatory entities (CFPB) | 7,193 | Synced, daily cron |
| CFPB complaints | 9,804,908 | Full dataset ingested |
| FDIC institutions | 27,832 | Reference data |
| SBA loan records | 373,980 | Reference data |
| CFPB enforcement actions | 385 | Reference data |
| Wellness guides | ~85 | Live (Supabase) |

### Automated Pipeline Status

| Pipeline | Cadence | Output |
|----------|---------|--------|
| Blog generation | 2/day (06:00+06:30 UTC) | AI-written, auto-published |
| Wellness guides | 2/day (15:00 UTC) | Auto-generated topics |
| Comparisons | 5/day (15:30 UTC) | Auto-generated from DB |
| Answer pages (cluster) | 1/weekday (13:00 UTC) | From cluster_spec.json |
| City guides | 5/day (09:00 UTC) | Population-priority ordered |
| Content drip | Daily (12:00 UTC) | Multi-format distribution |
| CFPB sync | Daily (16:00 UTC) | 100 entities/run |
| Indexing API push | Daily (08:00 UTC) | Priority-tiered |
| DB guardian | Hourly | Drift healing |
| DB backup | Daily (06:50 UTC) | Point-in-time recovery |
| DB sync | Daily (07:00 UTC) | SQLite → Supabase |
| SEO engine report | Daily (09:00 UTC) | Per-site metrics |
| Weekly digest | Monday (07:00 UTC) | Email to founder |
| SERP winnability | Monday (09:00 UTC) | Top 30 phrases tracked |

### Traffic Position

| Metric | Value | Source |
|--------|-------|--------|
| Monthly clicks | ~26 | GSC |
| Monthly impressions | ~8,086 | GSC |
| CTR | 0.03% | GSC |
| Pages indexed | ~287 | GSC |
| Total indexable pages | 15,529+ | Site |
| YMYL sandbox | Active (expected 6-12 months) | Industry standard |

### Revenue Position

| Revenue stream | Status |
|----------------|--------|
| Affiliate (CJ network) | Approved at network level; individual advertisers rejecting (traffic too low) |
| Featured listings | Infrastructure exists, not marketed |
| MoneyLion Engine | Requires 25K monthly visitors |
| Lendio API | Requires 25K monthly visitors |
| BrokerOS (Cosmic Phoenix) | Entity exists, lender relationships in place; activation at $50K/mo |

---

## II. Strategic Framework

### The Thesis

CreditDoc's competitive advantage is structural, not operational. 9.8M federal complaint records + 27,832 FDIC institutions + 373,980 SBA loans create a data moat that no competitor can replicate without rebuilding the same regulatory intelligence layer. The directory's 15,529 lender profiles create a content moat that compounds with every city guide, every comparison, and every quiz completion.

The bottleneck is not the product. The bottleneck is traffic. Every initiative in this plan is evaluated against one criterion: **does it accelerate the path to 25,000 monthly visitors?**

### The Funnel

```
AWARENESS          Content (blog, wellness, answers, city guides)
                   ↓ organic search
EDUCATION          Course modules ("Credit Repair 101")
                   ↓ email capture at Module 1
ASSESSMENT         Quiz (evaluates situation, pre-fills from context)
                   ↓ completion logged to Supabase
RECOMMENDATION     Personalized lender matches (CFPB trust data)
                   ↓ affiliate click / origination
CONVERSION         Application → funded deal
                   ↓ revenue
RETENTION          Email drip, course progression, return visits
```

### Revenue Model by Phase

| Phase | Gate | Revenue Source | Target |
|-------|------|---------------|--------|
| **1 — Build** (now–Nov 2026) | Current | Accessible affiliates + featured listings | $200–2,000/mo |
| **2 — Embed** (~Nov 2026) | 25K visitors/mo | MoneyLion + Lendio embedded origination | $8,000–50,000/mo |
| **3 — Broker** (~May 2027) | $50K/mo revenue | BrokerOS direct SMB deals + voice agent | $50,000–120,000/mo |

---

## III. Execution Plan — 12-Week Sprints

### SPRINT 1: Infrastructure Acceleration (Weeks 1–2)

**Objective:** Triple the rate of indexable page creation and establish the conversion layer foundation.

#### 1A. City Guide Acceleration (Week 1, Day 1–2)

**Current:** 5 cities/day, 11 published.
**Target:** 10 cities/day.

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Update `creditdoc_city_guide_generator.py` batch size from 5 to 10 | Agent | None | Cron confirmed `--batch 10` |
| Validate OpenRouter rate limits handle 10/day without throttling | Agent | Batch change | 3 consecutive days, no failures |
| Monitor city guide indexing rate in GSC (weekly) | Founder | GSC access | First weekly check completed |
| Verify auto-submission to Google Indexing API within 1 hour of generation | Agent | Indexing script | Logs confirm same-day submission |

**Projected output:** 10 cities/day × 5 days = 50 cities/week. At this pace, top 250 population cities covered in 5 weeks. Full 500-city target in 10 weeks.

**Risk:** OpenRouter rate limiting at 10 concurrent Claude calls. **Mitigation:** Stagger generation across 2 cron windows (09:00 + 11:00 UTC, 5 each) if throttled.

#### 1B. Internal Linking Sprint (Week 1–2)

**Current:** 287 indexed pages with limited cross-linking.
**Target:** Every indexed page links to at least 3 high-priority unindexed pages.

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Export indexed page list from GSC (last 28 days, impressions > 0) | Agent | GSC script | CSV produced |
| Identify top 100 unindexed targets by page type priority: city guides → /best/* → state → /answers/* | Agent | Export | Priority list produced |
| Add contextual phrase→URL mappings to `inline-linker.ts` for top 50 city guide + money page URLs | Agent | Priority list | Deployed to Cloudflare Workers |
| Add end-of-article "Related" blocks on top 50 indexed lender review pages linking to relevant city guide + /best/* page | Agent | Priority list | Deployed |
| Cross-link city guides ↔ state regulatory pages ↔ /best/* money pages in sidebar | Agent | City guides live | Template updated |

**Why this matters:** Google discovers new pages primarily through internal links from already-indexed pages. 287 indexed pages are 287 doorways. Each link from an indexed page to an unindexed page is a crawl signal.

#### 1C. Indexing Pipeline Priority Reorder (Week 1, Day 1)

**Current:** Mixed priority order in `creditdoc_priority_indexing.py`.
**Target:** Strict tier order matching council recommendation.

| Tier | Page Type | Daily Allocation (of 30 max) |
|------|-----------|------------------------------|
| 1 | City guides (new, < 48 hours old) | 10 |
| 2 | /best/* money pages | 8 |
| 3 | State hub pages | 5 |
| 4 | /answers/* pages | 5 |
| 5 | All other (lender reviews, blog, wellness) | 2 |

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Update `creditdoc_priority_indexing.py` with tier-based allocation | Agent | None | Code deployed, verified in logs next day |
| Ensure city guides submitted within 1 hour of generation | Agent | Generator script | Timestamp check in logs |
| Add page-type tagging to indexing logs for weekly analysis | Agent | None | Logs show type breakdown |

#### 1D. Credit Repair Quiz — Build Phase (Week 1–2)

**Current:** Template exists at `/tools/borrowing-power-quiz/` (908 lines, LIVE). No credit repair quiz.
**Target:** Credit repair quiz live on `/qualify/credit-repair/` + homepage hero + content CTAs.

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Create reusable quiz component accepting pillar config (not 10 separate pages) | Agent | Existing template | Component renders with credit-repair config |
| Design 5 credit repair questions with branching logic | Agent + Founder review | None | Questions approved by founder |
| Build quiz results page showing personalized lender recommendations from DB + CFPB resolution rates | Agent | Supabase query | Results page renders with real data |
| Email capture after Q3 (existing pattern from template) | Agent | Quiz build | Email stored in Supabase |
| Create `quiz_completions` Supabase table (schema below) | Agent | Supabase access | Table created, first test row inserted |
| Wire quiz to homepage as hero CTA | Agent | Quiz build | Homepage renders quiz entry point |
| Add end-of-article quiz CTA to all credit repair wellness guides | Agent | Quiz build | CTA renders on 3+ guides |
| Add sidebar quiz CTA to credit repair lender review pages | Agent | Quiz build | Sidebar renders on review pages |
| Create standalone `/qualify/credit-repair/` page | Agent | Quiz build | Page returns 200 |
| Pre-fill location when visitor arrives from city guide | Agent | Quiz + city guide | URL param passed and consumed |
| Deploy to Cloudflare Workers | Agent | All above | Worker deployed, smoke test passes |

**Quiz completions table schema:**
```sql
CREATE TABLE quiz_completions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pillar TEXT NOT NULL,
  answers JSONB NOT NULL,
  location TEXT,
  email TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  source_page TEXT,
  result_lenders JSONB,
  shared BOOLEAN DEFAULT FALSE
);
```

**Pre-fill logic:**
- From city guide → location = city, state
- From credit repair article → pillar = credit-repair
- From lender review → category pre-selected
- Direct to /qualify/credit-repair/ → no pre-fill

**Founder checkpoint:** Quiz questions and results page design require founder approval before deployment. Schedule 15-minute review after build.

---

### SPRINT 2: Content Authority + AI Readiness (Weeks 3–4)

**Objective:** Launch the course engine, publish original research for backlinks, and enable AI citation.

#### 2A. "Credit Repair 101" Course — 7 Modules (Weeks 3–4)

**Current:** 85 wellness guides + 26 answer pages contain raw material. No course structure.
**Target:** 7-module course with email capture, drip delivery, and completion tracking.

| Module | Title | Primary Source Material | New Writing Required |
|--------|-------|------------------------|---------------------|
| 1 | Understanding Your Credit Report | Wellness guides on credit scores, reports | Minimal — reorganize + add structure |
| 2 | Your Rights Under Federal Law | Regulatory data, state pages, CFPB explainer | Moderate — synthesize from multiple sources |
| 3 | How to Dispute Errors | Answer pages on disputes, credit bureau contacts | Minimal — reorganize + add templates |
| 4 | Choosing a Credit Repair Company | CFPB entity data + /best/credit-repair-companies/ | New — dynamic lender recommendations from DB |
| 5 | Building Credit After Repair | Wellness guides on credit building | Minimal — reorganize |
| 6 | Avoiding Predatory Lenders | CFPB enforcement actions, complaint patterns | New — data-driven content from 9.8M complaints |
| 7 | Your 90-Day Action Plan | Quiz results + personalized recommendations | New — dynamic, personalized via quiz data |

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Audit existing wellness guides — map to modules | Agent | None | Mapping document produced |
| Design course hub page template (progress tracking, module navigation) | Agent | None | Template renders with 7 module cards |
| Build Module 1 content from existing guides | Agent | Audit | Module 1 live, returns 200 |
| Set up email capture at Module 1 ("Get Module 1 free, email for full course") | Agent | Module 1 | Email stored, confirmation sent |
| Build drip delivery infrastructure (AgentMail/Harvey) | Agent | Email capture | Test sequence delivers Module 2 after 3 days |
| Build Modules 2–6 | Agent | Module 1 approved | All modules return 200 |
| Build Module 7 (dynamic, pulls from quiz data) | Agent | Quiz live + Modules 1-6 | Personalized plan renders |
| Create completion certificate (shareable badge/image) | Agent | All modules | Certificate generates with name + date |
| Wire course CTAs into wellness guides ("Want the full course? Start here") | Agent | Course live | CTAs render on relevant guides |
| Wire course completion → quiz → recommendations flow | Agent | Course + quiz live | End-to-end path works |

**Delivery cadence:** Module every 3 days = 21-day email sequence.
**Expected email open rates:** 40–60% (course content, not marketing — industry benchmark).

**Monetization hooks built into course content (not bolted on):**
- Module 4: Recommends credit repair companies ranked by CFPB resolution rate (affiliate links)
- Module 5: Recommends secured cards and credit builder loans (affiliate links)
- Module 7: Quiz-driven personalized recommendations (affiliate + future origination)

#### 2B. Original Research Piece — CFPB Data Story (Week 3)

**Current:** 9.8M complaints, 7,193 entities, 385 enforcement actions. No public analysis.
**Target:** One data-driven research piece with original findings, designed to earn press links.

**Framing constraint (founder directive):** POSITIVE ONLY. Not "worst lenders." The angle must make lenders want to be featured.

**Candidate angles (choose one with highest press appeal):**

| Angle | Data Source | Headline Direction |
|-------|------------|-------------------|
| Most Responsive Lenders in America | CFPB complaint resolution rates by company | "These 25 Lenders Resolve 90%+ of Consumer Complaints" |
| State-by-State Consumer Protection Scorecard | CFPB complaints × FDIC branches × SBA loans by state | "Which States Protect Consumers Best? A Federal Data Analysis" |
| The Credit Repair Industry: What Federal Data Shows | CFPB complaints for credit repair companies | "What 150,000 Consumer Complaints Reveal About Credit Repair" |

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Run analysis queries on regulator.db for all 3 angles | Agent | None | Data tables produced |
| Present findings to founder — choose angle | Founder | Data | Angle selected |
| Write research piece (2,000–3,000 words with charts, methodology, data tables) | Agent | Angle selected | Draft reviewed by founder |
| Publish at `/research/[slug]/` | Agent | Draft approved | Page returns 200 |
| Create press pitch (3 paragraphs + key findings + quote) | Agent | Published | Pitch document ready |
| Build media list (30 financial journalists + personal finance bloggers) | Agent | None | List in Drive |
| Send pitches via Harvey | Agent | Pitch + list | 30 emails sent, opens tracked |

**Expected outcome:** 5–15 backlinks from DR 40–60 sites over 8–12 weeks. One piece is enough to move domain authority measurably at CreditDoc's current level.

#### 2C. llms.txt + Structured Data (Week 3, Day 1–2)

**Current:** No llms.txt. Structured data status unknown.
**Target:** AI-citable site with proper schema markup.

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Create `/llms.txt` with site purpose, data sources, key page URLs, API access info | Agent | None | File returns 200 |
| Audit JSON-LD on lender review pages — add `FinancialService` schema if missing | Agent | None | Schema validates on 3 sample pages |
| Add `FAQPage` schema to answer pages and city guide FAQ sections | Agent | None | Schema validates on 3 sample pages |
| Add `Course` schema to course hub page | Agent | Course live | Schema validates |
| Verify AI crawlers allowed in robots.txt (already confirmed clean) | Agent | None | Confirmed |

**Effort:** 2–4 hours total. High leverage — positions CreditDoc for AI Overview citations.

---

### SPRINT 3: Growth Loops + Revenue Foundation (Weeks 5–8)

**Objective:** Activate viral distribution, establish social presence, and wire initial revenue.

#### 3A. Shareable Quiz Results (Week 5–6)

**Current:** Quiz logs completions but results aren't shareable.
**Target:** Every quiz completion generates a unique, shareable URL with social share buttons.

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Generate unique results URL per completion (e.g., `/results/[uuid]/`) | Agent | Quiz live | URL returns personalized results |
| Design shareable results card (score range, lender count, city, resolution rate average) | Agent | Results URL | Card renders correctly |
| Add share buttons (X, LinkedIn, Facebook, WhatsApp) | Agent | Card design | Buttons generate correct share text |
| Track shares in `quiz_completions` table (`shared` boolean + `share_channel`) | Agent | Buttons | Analytics logging verified |
| Shared link routes new visitors to quiz start (viral loop) | Agent | Share flow | End-to-end loop works |

**Viral loop mechanics:**
```
User completes quiz → sees results → shares on X
→ Follower clicks shared link → lands on quiz → completes → shares
→ Each completion = email captured + intent logged + potential share
```

#### 3B. Social Media Launch (Week 5+, ongoing)

**Current:** No CreditDoc social presence.
**Target:** 2–3 posts/week on X + LinkedIn, built from CFPB data insights.

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Create CreditDoc X account (or verify existing) | Founder | None | Account active |
| Create CreditDoc LinkedIn company page | Founder | None | Page active |
| Build social content template library (3 formats: data insight, credit tip, quiz promo) | Agent | None | 10 template posts drafted |
| Write first 2 weeks of posts (6 posts total) | Agent | Templates | Posts approved by founder |
| Schedule via Blotato | Agent | Posts approved | First week scheduled |
| Create weekly social content generation cron (Mon, Wed, Fri) | Agent | Template library | Cron runs, posts generated |

**Content format examples:**
- **Data insight:** "Federal data shows: lenders in [State] resolve [X]% of consumer complaints within 15 days. National average: [Y]%. [chart image]"
- **Credit tip:** "Your credit repair rights: Under the FCRA, you can dispute any inaccuracy on your credit report — free. Here's the 3-step process: [link to Module 3]"
- **Quiz promo:** "Not sure which credit repair approach is right for you? Our 60-second assessment uses federal complaint data to match you. [link]"

#### 3C. Affiliate Applications — Lower-Threshold Programs (Week 5–6)

**Current:** CJ approved at network level, individual advertisers rejecting.
**Target:** 2–3 live affiliate programs generating first revenue.

| Program | Type | Threshold | Per-Lead Value | Application Status |
|---------|------|-----------|---------------|-------------------|
| LeadNetwork | Lead gen aggregator | Low | $10–25/lead | Apply Week 5 |
| LeadsMarket | Lead gen aggregator | Low | $10–25/lead | Apply Week 5 |
| Self (credit builder) | Direct | Low | $20–75/signup | Apply Week 5 |
| DisputeBee | Credit repair SaaS | Low | $50–200/referral | Apply Week 6 |
| SeedFi / MoneyLion (basic affiliate, not Engine) | Direct | Medium | $25–100/signup | Apply Week 6 |

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Apply to LeadNetwork, LeadsMarket, Self, DisputeBee | Agent | None | Applications submitted |
| Track acceptance/rejection in `AFFILIATE_GATES.md` | Agent | Applications | File updated |
| Wire accepted affiliate links into quiz results page | Agent | Acceptance + quiz | Links render with proper disclosures |
| Wire affiliate links into course Module 4 + Module 5 | Agent | Acceptance + course | Links render in modules |
| Set up click tracking | Agent | Links live | Clicks logged |

**CJ re-application schedule (traffic-gated):**

| Traffic Milestone | Action |
|-------------------|--------|
| 500 clicks/month | Re-apply to 3 CJ advertisers with traffic proof |
| 2,000 clicks/month | Re-apply to Awin |
| 5,000 clicks/month | Re-apply to Impact Radius (SoFi, Upstart, LendingClub) |
| 8,000 clicks/month | Re-apply to Experian Partner Network |
| 25,000 clicks/month | Apply to MoneyLion Engine + Lendio API Partner |

---

### SPRINT 4: Scaling + Second Pillar (Weeks 9–12)

**Objective:** Prove the model on credit repair, then replicate to personal loans.

#### 4A. Performance Measurement + Optimization (Week 9)

| Metric | Measurement Method | Action Threshold |
|--------|-------------------|-----------------|
| Quiz completion rate | `quiz_completions` count / quiz page views | < 40% → simplify questions |
| Email capture rate | Emails captured / quiz completions | < 30% → test earlier capture |
| Course enrollment rate | Module 1 views / email signups | < 20% → revise CTA copy |
| Course completion rate | Module 7 views / Module 1 views | < 10% → revise content quality |
| City guide indexing rate | GSC indexed count / published count | < 50% → diagnose |
| Affiliate click-through rate | Clicks / quiz results page views | < 5% → revise recommendations |
| Social share rate | Shares / quiz completions | < 2% → revise results card |

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Build analytics dashboard (Supabase queries) | Agent | 8 weeks of data | Dashboard renders |
| Identify lowest-performing funnel step | Agent | Dashboard | Analysis document produced |
| Optimize lowest-performing step | Agent + Founder | Analysis | A/B variant deployed |
| Document learnings in `OPTIMIZATION_LOG.md` | Agent | Optimization | File updated |

#### 4B. Second Quiz — Personal Loans (Week 10–11)

**Trigger:** Credit repair quiz completion rate ≥ 40%.

| Task | Owner | Dependency | Done When |
|------|-------|------------|-----------|
| Create personal loans quiz config (same component, new questions) | Agent | Reusable component | Quiz renders |
| Wire to personal loan content (wellness guides, answer pages, city guides) | Agent | Quiz build | CTAs render |
| Create `/qualify/personal-loans/` standalone page | Agent | Quiz build | Page returns 200 |
| Connect to personal loan affiliate programs (if accepted) | Agent | Affiliate acceptance | Links live |

#### 4C. Second Course — "First-Time Borrower's Guide" (Week 11–12)

**Trigger:** Credit Repair 101 enrollment ≥ 100.

| Module | Title |
|--------|-------|
| 1 | Understanding Credit Basics |
| 2 | Building Credit from Zero |
| 3 | How Personal Loans Work |
| 4 | Choosing the Right Lender (CFPB data-driven) |
| 5 | Your First Loan Application Checklist |

#### 4D. City Guide Expansion Assessment (Week 12)

| Check | Action |
|-------|--------|
| 250+ city guides published | If yes → maintain 10/day |
| City guide indexing rate > 60% | If yes → consider increase to 15/day |
| City guide indexing rate < 40% | Pause expansion, diagnose template quality |
| Quiz completions from city guides > 10% of total | City guide → quiz funnel is working |

---

## IV. Operating Cadence

### Daily (Automated)

| Time (UTC) | Action | Output |
|------------|--------|--------|
| 05:00 | Promotion report | Email to founder |
| 05:30 | CFPB regulatory sync | 100 entities updated |
| 06:00 | Blog scheduler + generation (2 posts) | Published to site |
| 06:50 | DB backup | Point-in-time recovery |
| 07:00 | DB sync (SQLite → Supabase) | Data consistency |
| 07:15 | Index tracker report | Email to founder |
| 08:00 | Priority indexing push | Up to 30 URLs submitted |
| 09:00 | City guide generation (10 cities) | Published to Supabase |
| 09:00 | SEO engine report | Metrics logged |
| 12:00 | Content drip | Multi-format distribution |
| 13:00 | Cluster answer page (Mon–Fri) | 1 /answers/ page published |
| 14:00 | Autonomous engine (500 profiles) | Enrichment pipeline |
| 15:00 | Wellness guide generation (2 guides) | Published |
| 15:30 | Comparison generation (5 comparisons) | Published |
| 16:00 | CFPB entity sync (100 entities) | Updated |
| 16:00 | Daily published report | Email to founder |
| Hourly | Guardian (drift healing) | Auto-correction |

### Weekly (Founder)

| Day | Time | Action | Duration |
|-----|------|--------|----------|
| Monday | 07:00 UTC | Review weekly digest email | 10 min |
| Monday | 09:00 UTC | Review SERP winnability report | 10 min |
| Tuesday | Morning | GSC review: impressions, clicks, position changes | 15 min |
| Tuesday | Morning | Approve/edit next 5 clusters from queue | 5 min |
| Friday | Afternoon | Sample review: 1–2 published pages end-to-end | 15 min |
| Friday | Afternoon | Check GSC manual actions (must always be empty) | 2 min |

**Total founder operating time:** ~1 hour/week during Sprint 1–2, ~30 min/week during Sprint 3–4 as automation matures.

### Monthly (Strategic Review)

| Review Item | Source | Decision |
|-------------|--------|----------|
| Traffic trend (clicks, impressions, indexed pages) | GSC | Increase/maintain/diagnose pace |
| Quiz funnel metrics (completion, capture, click-through) | Supabase dashboard | Optimize weakest step |
| Course metrics (enrollment, completion, email engagement) | AgentMail + Supabase | Content quality assessment |
| Affiliate revenue | Network dashboards | Re-application timing |
| City guide indexing rate by wave | GSC + Supabase | Expansion decision |
| Content pipeline health (queue depth by type) | DB queries | Refill before exhaustion |

---

## V. CFPB Data Positioning (Binding Directive)

The regulatory intelligence layer is CreditDoc's structural moat. Its positioning is a founder-level strategic decision, not a marketing tactic.

### Approved Framing

| Context | Language | Example |
|---------|----------|---------|
| Lender profile pages | "Consumer Trust Profile" | "Lexington Law: 87% complaint resolution rate based on 2,341 federal records" |
| Research publications | "America's Most Responsive Lenders" | "25 lenders that resolve 90%+ of consumer complaints" |
| Quiz results | CFPB resolution rate as trust signal | "We recommend lenders with above-average complaint resolution rates" |
| Course content | Educational, data-backed | "Federal data shows credit repair companies resolve 72% of complaints on average" |
| City guides | Localized trust data | "In Houston, the top 5 lenders by complaint resolution rate are..." |

### Prohibited Framing

| Never | Why |
|-------|-----|
| "Worst lenders" / "Most complained-about" | Adversarial positioning burns lender relationships |
| Letter grades (A–F) applied punitively | Same — positions CreditDoc as judge, not platform |
| Naming lenders with poor metrics | Legal risk + relationship damage |
| Unsolicited negative outreach to lenders | Burns the bridge to Phase 2/3 embedded origination |

### Future B2B Application (Not Now)

When traffic justifies it (25K+ visitors/month), the same CFPB data powers a **Lender Dashboard** — a private tool where lenders can see their own metrics, compare to industry averages, and understand their competitive position. This becomes the "claim your listing" upgrade path: basic profile (free) → enhanced profile ($49/mo) → lender dashboard ($249/mo).

**This is NOT in the current execution plan.** It activates at Phase 2. Do not pitch lenders until traffic proves value.

---

## VI. Risk Register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|------|-----------|--------|------------|-------|
| R1 | Google scaled-content penalty | Medium | Catastrophic | Pace ceiling enforced (RULE -2); city guides use real local data; editorial review on 10%+ | Founder |
| R2 | YMYL sandbox extends beyond 12 months | Medium | High | City guides bypass local YMYL faster; course + quiz create engagement signals Google values | Agent |
| R3 | OpenRouter rate limiting at 10 cities/day | Low | Medium | Split into 2 cron windows; cache templates | Agent |
| R4 | Quiz completion rate < 30% | Medium | Medium | Simplify to 3 questions; test different entry points | Agent |
| R5 | All affiliate programs reject | Low | Medium | 5 simultaneous applications + direct outreach to smaller programs | Agent |
| R6 | Lender relationships damaged by CFPB data use | Low | Catastrophic | Positive framing only (Section V binding); no adversarial content | Founder |
| R7 | Content pipeline exhaustion (queue runs dry) | Medium | Medium | Auto-refill mechanisms built into all pipelines; exit non-zero + email on exhaustion | Agent |
| R8 | Indexing API quota starvation (shared across 5 sites) | Low | Medium | Per-site caps (30/day CreditDoc); cooldown ledger; CreditDoc runs first at 08:00 UTC | Agent |
| R9 | Competitor clones the data moat | Very Low | High | CFPB data is public but the 9.8M record normalized database + matching to 18,968 profiles is non-trivial to replicate | — |
| R10 | Google algorithm update penalizes affiliate content | Medium | High | Phase 2 embedded origination reduces affiliate footprint; quiz IS the product, not the exit link | Agent |

---

## VII. Success Milestones

### 90-Day Checkpoints (from today)

| Day | Milestone | Measurement |
|-----|-----------|-------------|
| **14** | City guides at 10/day + credit repair quiz live | Cron logs + /qualify/credit-repair/ returns 200 |
| **28** | Internal linking deployed + llms.txt live + research piece published | GSC crawl stats + page live + pitch emails sent |
| **42** | Credit Repair 101 course live (all 7 modules) + email drip running | All module URLs return 200 + first drip email sent |
| **56** | Shareable quiz results + social media launched (2–3/week) | Share buttons work + first 8 social posts published |
| **70** | First affiliate revenue OR 2+ programs accepted | Revenue or acceptance confirmation |
| **84** | Performance review: quiz metrics + course metrics + traffic trend | Dashboard shows all KPIs |

### 6-Month Targets (November 2026)

| Metric | Target |
|--------|--------|
| Pages indexed | 2,000+ |
| Monthly clicks | 500+ |
| Monthly impressions | 50,000+ |
| City guides published | 250+ |
| Quiz completions (cumulative) | 500+ |
| Email list | 500+ |
| Course enrollments | 200+ |
| Monthly revenue | $200–2,000 |

### 12-Month Targets (May 2027)

| Metric | Target |
|--------|--------|
| Pages indexed | 5,000+ |
| Monthly clicks | 5,000+ |
| Monthly impressions | 200,000+ |
| City guides published | 500+ |
| Quiz completions/month | 1,000+ |
| Email list | 5,000+ |
| Course enrollments | 2,000+ |
| Active affiliate programs | 5–8 |
| Monthly revenue | $8,000–50,000 (Phase 2 if gate met) |

### The S-Curve Inflection

Based on council analysis and YMYL industry data:
- **Months 1–6:** Slow. Sandbox period. Traffic grows linearly with indexed pages.
- **Months 6–8:** Acceleration. Google lifts sandbox on proven content. Exponential impression growth.
- **Months 8–10:** Inflection. Traffic compounds as domain authority builds. City guides + content clusters create topical authority signal.
- **Months 10–14:** Threshold. 25K monthly visitors becomes achievable. Phase 2 embedded origination unlocks.

**The only way to miss the inflection is to stop building before it arrives.**

---

## VIII. Governance

### Decision Rights

| Decision Type | Who Decides | Agent Role |
|---------------|-------------|------------|
| Strategic direction (what to build) | Founder | Propose, execute after approval |
| Content quality standards | Founder | Sample for review, flag concerns |
| Lender relationship positioning | Founder | Follow Section V binding directives |
| Pace changes (city guides/day, content/day) | Founder | Recommend based on data, wait for GO |
| Technical implementation (how to build) | Agent | Execute within approved plan |
| Bug fixes and pipeline repairs | Agent | Fix and report |
| New paid API usage | Founder | State API + count + cost, wait for YES |
| Affiliate applications | Agent | Apply to pre-approved list; founder approves new networks |
| Bulk data operations | Founder | Generate report, wait for manual confirmation |

### Escalation Triggers

The agent must immediately escalate to the founder (via Harvey email) when:
1. GSC manual action received
2. Traffic drops > 30% week-over-week
3. Content pipeline exhaustion < 3 days of queue remaining
4. Affiliate program acceptance or rejection
5. Quiz completion rate < 20% over 7-day window
6. Any infrastructure failure affecting live site

### Review Cadence

| Cadence | Participants | Agenda |
|---------|-------------|--------|
| Weekly | Founder (async via digest email) | Pipeline status, traffic trend, blockers |
| Monthly | Founder + Agent (session) | KPI review, priority adjustment, next sprint planning |
| Quarterly | Founder + Council (optional) | Strategic review, phase gate assessment |

---

## IX. Appendices

### A. Technology Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| Frontend SSR | Cloudflare Workers (Astro) | $0 (free tier) |
| Database | Supabase (PostgreSQL) | $0 (free tier) |
| Local DB | SQLite (creditdoc.db) | $0 |
| Regulatory DB | SQLite (regulator.db) | $0 |
| DNS + CDN | Cloudflare | $0 (free tier) |
| Email | AgentMail (Harvey) | Included |
| Image Generation | Gemini API (Nanobanana) | Minimal |
| Content Generation | Claude CLI (Opus) | Included in plan |
| Social Posting | Blotato MCP | $29/mo |
| VPS | Current server | Existing |
| **Total monthly cost** | | **~$29/mo** |

### B. Data Assets

| Dataset | Records | Source | Refresh |
|---------|---------|-------|---------|
| CFPB consumer complaints | 9,804,908 | CFPB public database | Daily sync |
| CFPB company stats | 2,514 | Derived from complaints | Daily |
| CFPB enforcement actions | 385 | CFPB | Daily |
| Regulatory entities | 7,193 | CFPB + FDIC + SBA | Daily |
| FDIC institutions | 27,832 | FDIC BankFind | Quarterly |
| FDIC branch locations | 78,347 | FDIC BankFind | Quarterly |
| SBA loan records | 373,980 | SBA FOIA | Annual |
| SBA lender stats | 21,967 | Derived | Annual |
| Lender profiles | 18,968 | Aggregated | Continuous |

### C. Key File Locations

| Purpose | Path |
|---------|------|
| Execution plan (this document) | `creditdoc/CREDITDOC_STRATEGIC_EXECUTION_PLAN_2026.md` |
| Council sessions | `creditdoc/AI_COUNCIL_SESSION_[1-5]_2026-05-13.md` |
| Implementation plan (original) | `creditdoc/Keywords Project Folder/_project/IMPLEMENTATION_PLAN.md` |
| Business framework | `creditdoc/Keywords Project Folder/_project/FRAMEWORK.md` |
| Quiz funnel designs | `creditdoc/CREDITDOC_QUIZ_FUNNELS.md` |
| Master strategy | `creditdoc/CREDITDOC_MASTER_STRATEGY.md` |
| Live state | `creditdoc/CREDITDOC_NOW.md` |
| Next actions | `creditdoc/CREDITDOC_NEXT.md` |
| Affiliate gates | To be created: `creditdoc/AFFILIATE_GATES.md` |
| Drive folder (council docs) | `AI Council Research 2026-05-13` (ID: `1rfqoUnByrkXZBlY4lYo_KPS-0Okts2Al`) |

---

*This plan is a living document. It will be updated at each monthly review with actual metrics, adjusted timelines, and revised priorities based on what the data shows.*

*"This founder doesn't give up, he only doubles down."*

*Prepared May 13, 2026. Advisory Council: Dorsey, Musk, Jobs, Ackman, Palihapitiya, Ravikant, Vaynerchuk.*
