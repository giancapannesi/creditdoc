# Comparison Page Enrichment Design

Date: 2026-06-18

## Purpose

CreditDoc comparison pages should become useful decision pages, not thin copies of the linked review pages and not cleanup-only pages. Each comparison page should help a visitor understand how to decide between provider X and provider Y, then route them to the deeper CreditDoc assets that support that decision.

The linked review pages remain the deep provider profiles. The comparison page should preserve sourced facts from both providers, explain the practical trade-offs, and point users to relevant tools, guides, courses, category hubs, local guides, and regulatory context.

## Product Principle

Do not strip useful comparison pages down to bland safety copy. Preserve and structure the page value:

- real listed pricing and setup-fee fields;
- real APR/rate examples where the source supports them;
- public review fields and BBB/profile context;
- refund, return, or cancellation-term notes;
- service-model differences;
- product mechanics;
- geographic or use-case distinctions;
- regulatory or complaint context where already sourced.

Remove or soften only unsupported conclusions: winner/value verdicts, guarantee certainty, fabricated savings, approval predictions, broad trust conclusions, and unsupported negative claims.

## Page Role

The comparison page answers:

> I am comparing X vs Y. What is actually different, what should I verify, and which CreditDoc tools or guides help me decide?

It should not try to repeat every field from each full review page.

## Reusable Page Sections

### 1. Quick Decision Map

Show two or more fit cards:

- "Compare X if..." using stored service, product, category, and feature fields.
- "Compare Y if..." using the same source discipline.
- "Main trade-off to verify" where the page has enough structured context.

For example, in a credit-repair comparison, the map might distinguish mortgage-readiness support from broader dispute management, rent reporting, identity-theft insurance, or three-bureau dispute work.

### 2. What Actually Differs

Use stored facts to summarize meaningful differences:

- service model;
- cost shape;
- refund or return terms;
- bureau coverage;
- speed or funding channel;
- platform/portal/mobile-app context;
- state/local availability when relevant.

This section should be factual and compact. It should not declare a provider "better" unless the criteria are explicit and sourced.

### 3. Cost And Terms To Verify

Keep real stored pricing and fees, but present them as verification points:

- monthly price;
- setup fee;
- minimum or maximum amount where relevant;
- APR/rate examples where relevant;
- refund/cancellation/return-term wording;
- warning that missing price is not "free."

### 4. Before You Contact Either Company

Add a short checklist tailored by category:

- verify current pricing and setup fees;
- ask what is included;
- ask about cancellation/refund terms;
- confirm bureau coverage;
- check complaint and regulator context;
- compare the full CreditDoc review pages.

### 5. CreditDoc Tools And Guides

Add a reusable resource section on comparison pages:

- Tools relevant to the category.
- Credit fundamentals course.
- Answer pages and blogs relevant to the category.
- Resources such as credit-report checklist or letter templates.
- Local city guides and state lending-law pages.
- Complaint-data context.

The section should use real internal URLs only. It should be category-aware and avoid dumping every link on every page.

## Initial Category Routing

Credit repair comparisons:

- `/tools/credit-repair-qualify-quiz/`
- `/tools/credit-score-simulator/`
- `/resources/credit-report-checklist/`
- `/courses/credit-fundamentals/`
- `/answers/how-to-remove-charge-offs/`
- `/answers/how-to-build-credit-score-fast/`
- `/categories/credit-repair/`

Personal loan and emergency-cash comparisons:

- `/tools/borrowing-power-quiz/`
- `/tools/loan-denial-reason-checker/`
- `/tools/credit-denial-action-checklist/`
- `/answers/personal-loan-interest-rates-explained/`
- `/answers/how-much-can-you-borrow-with-your-credit-score/`
- `/tools/state-consumer-credit-regulator-directory/`

Debt-relief comparisons:

- `/tools/debt-payoff-calculator/`
- `/resources/debt-credit-letter-templates/`
- `/answers/can-i-do-debt-consolidation-myself/`
- `/answers/debt-settlement-credit-report-diy-guide/`
- `/categories/debt-relief/`

Business-loan comparisons:

- `/tools/business-loan-readiness-quiz/`
- `/tools/bank-statement-cash-flow-calculator/`
- `/tools/mca-repayment-calculator/`
- `/answers/how-to-apply-for-a-business-loan/`
- `/answers/merchant-cash-advance-guide/`

Credit-building and fintech comparisons:

- `/tools/credit-score-simulator/`
- `/courses/credit-fundamentals/`
- `/answers/build-credit-with-no-credit-history/`
- `/answers/secured-credit-cards-questions-answered/`
- `/categories/build-credit/`

## Pilot

Use `ecreditadvisor-vs-the-credit-repairmen` as the pilot page because it shows the exact issue:

- it has useful real distinctions;
- the deeper reviews already exist;
- current comparison copy has old "wins/safer" framing;
- the right answer is to preserve useful facts and add decision structure.

## Success Criteria

- Comparison pages become richer and more useful, not thinner.
- The reusable template improves every comparison page without hand-editing all 336 records at once.
- Cleanup and enrichment happen together in future batches.
- Build, sitemap, and rendered-page checks pass.
- Page copy remains YMYL-safe: no fabricated prices, no unsupported guarantees, no approval predictions, no fake recommendations.

