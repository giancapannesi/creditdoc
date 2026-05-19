# CreditDoc — Quiz Pages & Lead Funnels

**Status:** NOT STARTED — template exists, rollout planned but not executed
**Full plan:** `CreditDoc Project Improvement/2026-04-20_MASTER_SEO_EXECUTION_PLAN.md` (Phase 2.2)
**Depends on:** Part 1 delivering 30+ ranked phrases first (per plan gating rule)

---

## What This Is

Interactive quiz pages that capture visitors and feed them into the affiliate/recommendation funnel. The conversion path from the Master SEO Plan:

```
Question → /answers/X/ page → quiz CTA → /qualify/Z/ quiz → email captured → drip sequence → affiliate click → $
```

---

## What Already Exists

- **Template:** `src/pages/tools/borrowing-power-quiz.astro` (908 lines, LIVE at /tools/borrowing-power-quiz/)
- **Method:** Duplicate template per category, swap 5 questions + `categoryRecommendations` + result page CTA to matching `/best/*`
- **Email capture:** Added after Q3 in each quiz flow

---

## The 10 Quizzes (from Master SEO Plan Phase 2.2)

Rollout: one per week, Month 4-5 of the plan.

| Week | Quiz | URL |
|------|------|-----|
| 17 | Credit Repair Qualify Quiz | `/qualify/credit-repair/` |
| 18 | Credit Building Quiz | `/qualify/credit-building/` |
| 19 | Debt Relief Savings Quiz | `/qualify/debt-relief/` |
| 20 | Personal Loans Prequalify | `/qualify/personal-loans/` |
| 21 | Business Loans Prequalify | `/qualify/business-loans/` |
| 22 | Credit Cards Qualify | `/qualify/credit-cards/` |
| 23 | Auto Loan Rate Check | `/qualify/auto-loans/` |
| 24 | Mortgage Refi Check | `/qualify/mortgage/` |
| 25 | Student Loan Refi Check | `/qualify/student-loans/` |
| 26 | Checking/Savings Match | `/qualify/banking/` |

---

## Integration Points

- Every new quiz added to `/answers/*` pages in its cluster as **sidebar CTA + post-article CTA**
- Internal link from every relevant `/review/*` page to the quiz
- Each quiz result page links to matching `/best/*` money page

---

## Phase 2.3 — Email Drip Sequences (follows quiz launch)

For each of 10 quizzes: **5-email sequence over 14 days**. Last email sends affiliate recommendation matched to quiz answers.

**Infrastructure:** Supabase + AgentMail (Harvey). Built after quizzes prove conversion.
**Daily action:** 09:00 UTC cron sends drip emails for leads entering day N of their sequence.

---

## KPIs (from Master SEO Plan)

| Metric | Month 4 | Month 5 | Month 6 |
|--------|---------|---------|---------|
| Quiz pages live | 3 | 7 | 10 |
| Quiz completions/mo | 20 | 100 | 300 |
| Emails captured (cumulative) | 40 | 200 | 600 |
| Affiliate clicks/mo | 20 | 60 | 150 |

---

## Gating Rule

From the plan: "Part 2 only works if Part 1 delivered 30+ ranked phrases. If not, Part 2 pauses and we diagnose Part 1."

Quiz capture layer must be fully shipped (10 quizzes + drip sequences) before Part 3 (compounding authority) begins.

---

## Measurement

- Quiz conversion rate per pillar (% completions / page views)
- Email captures per quiz
- Email → affiliate click rate
- Drip sequence open rates (target: 30%, industry avg: 20%)
- Revenue per pillar attributed to quiz funnel

---

## Open Questions for Jammi

1. Are we at 30+ ranked phrases yet (Part 1 gate)?
2. Start with credit repair quiz (highest affiliate value) or borrowing power (template already live)?
3. Email capture: Supabase table + AgentMail drip, or external ESP?
4. Compliance review needed before launch?
