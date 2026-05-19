# CreditDoc — LIVE STATE (LIVE / RESUME-CURSOR)

> **Read me first.** This file is rewritten at the end of every session. It is the resume-cursor — the next-spawned Claude reads this BEFORE MEMORY.md / DECISIONS.md to know "where are we right now."

---

## 2026-05-18 — SEO FIXES BATCH + PRICING REMOVAL + AI COUNCIL

**Status: 18 fixes shipped. Pricing stripped. Council rebuilt with real characters. FREEZE ON-PAGE CHANGES.**

**Shipped 2026-05-17:**
1. City x category sub-pages — 756 new pages (42 cities × 18 categories). Worker `8bb70ada`.
2. City guide linking overhaul — inline linker phrases, HMDA table links, lender matching. Worker `e7d4d4fd`.
3. Category sub-pages: schema (CollectionPage+ItemList+BreadcrumbList), sitemap (756+ URLs), breadcrumb URL fix, localized intros, alt text.
4. FAQ keyword mapping tightened (exact slug fragments replacing broad keywords).
5. /trends/ index dedup — 767→378 entries.
6. CFPB labels clarity — "Response Rate*" / "On-Time Response**" with footnotes.
7. Data explainer page at `/about/creditdoc-data/` — 10 anchored sections.
8. Company count fix — uses `getStateCountRuntime()` (lightweight DB view).

**Shipped 2026-05-18:**
9. Data-driven FAQ — 8-candidate priority system with real per-company data. Worker `51f5a284`.
10. Free/mo pricing fix — subscription-category-aware display; 834 pages fixed. Worker `be8ec518`.
11. Generic best_for — 9 fintech companies updated with specific text.
12. Inline linker BNPL/fintech — 24 new phrase mappings. Worker `df5b1641`.
13. Tooltip ⓘ component — `InfoLink.astro` wired to 6 locations on every /review/ page (rating, CFPB, similar companies). Worker `e5af42cc`.
14. **PRICING REMOVAL** — ALL unverified AI-generated pricing stripped from entire site. Pricing cards, header badges, FAQ candidates, sidebar fields, schema priceRange, card product schema, LenderCard price badges. 272 lines deleted. Workers `9f92c790` → `77f6711a` → `cf366386`. Commits `4e5f7012c4` + `2806923784`.

**Production incident (2026-05-17):**
- Worker 1102 crash — removing `limit=30` from `getLendersByStateRuntime` caused CPU exceeded on states with 1,800+ lenders. Fixed: restored limit=30, count from `state_lender_counts` view.
- Monitor email spam — cooldown hash changed per-run. Fixed: single cooldown key.

**Current Worker:** `cf366386` (latest deploy)

---

## AI Council Session 7 (REAL — 6 independent agents)

Unanimous: **backlinks are #1 bottleneck.** Freeze on-page changes 3-4 weeks.

Council members now have real character profiles at `ai_council/members/`:
| Role | Character |
|------|-----------|
| Growth Strategist | Chamath Palihapitiya |
| Technical Architect | Elon Musk |
| SEO & Distribution | Jack Dorsey |
| Monetization Advisor | Bill Ackman |
| Content & Strategy Auditor | Peter Thiel |
| Devil's Advocate | Naval Ravikant |

Full minutes: `ai_council/sessions/2026-05-18/MINUTES.md`

---

## What's Next (from Council Session 7)

1. **Backlink outreach** — CFPB data as hook, "America's Most Responsive Lenders" research piece. Target 10-15 referring domains in 30 days.
2. **Freeze on-page changes** for 3-4 weeks — let Google measure recent work.
3. **Conversion tracking** — quiz/email funnel events.
4. **817 failed_quarantine audit** — ~445 wrongly quarantined. Needs Jammi decision.
5. **HMDA data pages** — linkable asset for outreach.

## 2026-05-19 — Planned Resource Cluster

New plan added: `/srv/BusinessOps/CreditDoc Project Improvement/2026-05-19_DEBT_CREDIT_LETTER_TEMPLATE_LIBRARY_PLAN.md`

Idea: build a CreditDoc-owned Debt And Credit Letter Template Library under
`/resources/`, using only the existing approved resource-page format from
`src/pages/resources/credit-report-checklist/`. Do not create a new layout and
do not copy competitor templates.

---

## CRITICAL RULES

- **NEVER display pricing data.** All pricing fields in DB are unverified AI guesswork. YMYL liability. Can ONLY be re-enabled with written confirmation from Jammi + verified first-party data. See `feedback_creditdoc_no_unverified_pricing.md`.
- **NEVER display unverified data as fact on a financial site.** If it wasn't confirmed by a human or pulled from a verified public source, it doesn't go on the page.

---

## Traffic Reality (GSC 28-day as of 2026-05-16)

| Metric | Value |
|--------|-------|
| Impressions | 25,727 |
| Clicks | 27 |
| CTR | 0.10% |
| Avg position | 27.4 |
| Pages with impressions | 2,355 |

**By type:** /review/ 17,934 imp (70%) | /city/ 624 | /categories/ 89 | /best/ 72 | /blog/ 24 | /answers/ 20

**Best city positions:** Charlotte (2), Detroit (3), College Park (4), Las Vegas (5)

---

## Content Pipelines (all running, all self-feeding)

| Pipeline | Cron | Status |
|----------|------|--------|
| City guides | 04:00 UTC daily | 10/day, 42+ live, target 250 by June 7 |
| Blog posts | 10:00 UTC daily | Auto-refills from CSV topics |
| Wellness guides | 11:00 UTC daily | Self-feeds from answer titles at <10 queue |
| Answer pages | 12:00 UTC daily | Running |
| Indexation | 08:00 UTC daily | Deduped, tier-priority, daily GSC push |
| Content audit | 09:00 UTC daily | Autofix titles/metas + email report |
| Site monitor | */5 minutes | 9 routes + content checks + Harvey alert |

---

## Sendy Email System

| Item | Value |
|------|-------|
| Quiz leads list | `rCzcu8brUim88T892Y85IqRQ` |
| Course list | `Yj7BPjltZ5YG9nUBw892y93g` (ID=2) |
| Autoresponder | ares_id=1, 8 emails, immediately→+21d |
| API key | Stored in the Sendy credential store / environment; do not record secrets in repo docs |
| Login | Stored in the Sendy credential store / password manager; do not record secrets in repo docs |

---

## Current Counts

| Type | Count |
|------|-------|
| Lender profiles (total) | ~15,762 (ready_for_index) |
| CFPB trend pages | 378 (+index, deduped) |
| City x category pages | 756 (42 × 18) |
| Comparison pages | 185 |
| City guides | 42+ |
| Money pages (/best/) | 13 |
| Course pages | 10 |
| Tools/quizzes | 4 |

---

## What NOT to do

- **Don't display any pricing data** — stripped 2026-05-18, needs Jammi written approval + verified data to restore
- Don't make on-page changes for 3-4 weeks — Google needs to measure
- Don't rewrite titles/metas on pages indexed <7 days
- Don't rebuild the inline linker (patch the TS at `src/utils/inline-linker.ts`)
- Don't pause any content pipeline without Jammi approval
- Don't conflate Vercel with CreditDoc (it's Cloudflare Workers)
- Don't display unverified data as fact — ever — on a YMYL financial site
