# CreditDoc — LIVE STATE (LIVE / RESUME-CURSOR)

> **Read me first.** This file is rewritten at the end of every session. It is the resume-cursor — the next-spawned Claude reads this BEFORE MEMORY.md / DECISIONS.md to know "where are we right now."

---

## 2026-05-16 — CTR OPTIMIZATION SPRINT (IN PROGRESS)

**Status: AI Council Session 6 approved. Executing AggregateRating + Link Equity.**

**Shipped today (2026-05-16):**
1. **Autoresponder drip LIVE.** 8 emails in Sendy (ares_id=1, list 2). Module summaries sent immediately → +21 days, every 3 days. Dark theme HTML with takeaways + action steps + deep links.
2. **Course email gating.** Hub + module pages now gate content behind enrollment form. localStorage-based. Compelling copy, explicit consent for 8 emails.
3. **Nav links.** "Courses" added to desktop nav, mobile menu, footer Quick Links.
4. **Content audit autofix.** Daily 09:00 UTC audit now auto-corrects titles >60 and metas >160 in Supabase before emailing report.
5. **Wellness self-feeding.** Pipeline auto-generates new topics from answer page titles when queue drops below 10.
6. **City guide title fix.** 14 over-limit titles corrected. Prompt tightened to 50-58 chars + truncation safety net.
7. **AggregateRating schema LIVE.** Real Google Reviews (google_rating + google_reviews_count) on ~15K /review/ pages. Stars in SERPs.
8. **766 CFPB Consumer Response Profile pages LIVE.** Prerendered at `/trends/[slug]/`. Positively framed (no complaint language). Links to /review/ and /research/. Export script in deploy.sh.

8. **Mini-quiz on /review/ pages.** "Is this lender right for you?" — 3 contextual questions, personalized result based on category/services/rating match.
9. **Trends index page.** `/trends/` lists all 766 companies alphabetically with resolution rates + alphabet nav.
10. **Comparison table on city guides.** Quick side-by-side table (rating, category, services) renders when 3+ lenders available.
11. **Detroit city guide.** Generated and live at `/credit-guide/detroit-mi/` — was ranking pos 3 without a page.
12. **Research→Trends linking.** Consumer complaints research page now links to 9 individual trend profiles.
13. **Footer link.** "Consumer Response Data" added to Quick Links.

**Current Worker:** `f584ef44` (latest deploy)

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

## AI Council Session 6 Decision (2026-05-16)

**Unanimous:** "Not a content problem — a CTR and trust-signal problem."

Approved next actions:
1. **AggregateRating schema** — stars in SERP (20-35% CTR lift expected) ← DOING NOW
2. **FAQ schema** on city guides + top pages
3. **Enhance top-10 pages** (Charlotte, LV, Detroit) with tables/FAQ/local data
4. **Mini-quiz on /review/ pages** ("Is this lender right for you?")
5. **Keep city guides at 10/day** (22x better per-page ROI than reviews)
6. **Link equity to /best/ pages** via inline linker ← DOING NOW
7. **Title/meta CTR optimization** for pos 15-30 pages

Full council transcript: `CreditDoc Project Improvement/2026-05-16-AI-COUNCIL-SESSION-6.md`

---

## Content Pipelines (all running, all self-feeding)

| Pipeline | Cron | Status |
|----------|------|--------|
| City guides | 04:00 UTC daily | 10/day, 31 live, target 250 by June 7 |
| Blog posts | 10:00 UTC daily | Auto-refills from CSV topics |
| Wellness guides | 11:00 UTC daily | Self-feeds from answer titles at <10 queue |
| Answer pages | 12:00 UTC daily | Running |
| Indexation | 08:00 UTC daily | Deduped, tier-priority, daily GSC push |
| Content audit | 09:00 UTC daily | Autofix titles/metas + email report |
| Site monitor | */5 minutes | 6 routes + content checks + Harvey alert |

---

## Sendy Email System

| Item | Value |
|------|-------|
| Quiz leads list | `rCzcu8brUim88T892Y85IqRQ` |
| Course list | `Yj7BPjltZ5YG9nUBw892y93g` (ID=2) |
| Autoresponder | ares_id=1, 8 emails, immediately→+21d |
| API key | `325gBl60j5lQ2vVs1RVN` |
| Login | `gian.eao@gmail.com` / `CrD_S3ndy_2026` |

---

## Current Counts

| Type | Count |
|------|-------|
| Lender profiles (total) | 18,971 |
| CFPB trend pages | 766 (+index) |
| Comparison pages | 185 |
| City guides | 32 |
| Money pages (/best/) | 13 |
| Course pages | 10 |
| Tools/quizzes | 4 |

---

## What NOT to do

- Don't add new page types until CTR improves
- Don't rewrite titles/metas on pages indexed <7 days
- Don't rebuild the inline linker (patch the TS)
- Don't pause any content pipeline without Jammi approval
- Don't conflate Vercel with CreditDoc (it's Cloudflare Workers)
