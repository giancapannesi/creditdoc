# CreditDoc Next Best Action Map

Purpose: first-pass routing map for the dashboard/NBA engine described in the
CreditDoc retention blueprint.

This is not user-facing logic yet. It is a controlled planning artifact for
turning existing tools, checklists, courses, state pages, and research assets
into a stateful journey.

## Routing Principles

- Recommend one primary next action, not a list of everything.
- Prefer free CreditDoc tools, checklists, and education before provider
  comparisons.
- Avoid legal, underwriting, or approval language.
- Do not recommend financial offers until the dashboard and consent model exist.
- Never collect SSNs, bank credentials, exact account numbers, or raw document
  uploads through tool forms.

## Tool Result Routes

| Source | Signal | Primary Next Action | Secondary Action |
| --- | --- | --- | --- |
| Credit Repair Qualify Quiz | `repair_research` | `/best/best-credit-repair-companies/` | `/resources/credit-report-checklist/` |
| Credit Repair Qualify Quiz | `build_first` | `/tools/credit-score-simulator/` | `/financial-wellness/credit-score-basics/` |
| Credit Repair Qualify Quiz | `review_first` | `/resources/credit-report-checklist/` | `/financial-wellness/dispute-credit-report-errors/` |
| Business Loan Readiness Quiz | `bank_sba_ready` | `/best/best-sba-loans/` | `/answers/how-to-apply-for-a-business-loan/` |
| Business Loan Readiness Quiz | `alternative_lender_fit` | `/best/best-small-business-loans/` | `/tools/bank-statement-cash-flow-calculator/` |
| Business Loan Readiness Quiz | `startup_build_path` | `/best/best-startup-business-loans/` | `/answers/how-to-apply-for-a-business-loan/` |
| Business Loan Readiness Quiz | `cash_flow_caution` | `/tools/mca-repayment-calculator/` | `/tools/bank-statement-cash-flow-calculator/` |
| Business Loan Readiness Quiz | `repair_docs_first` | `/tools/loan-denial-reason-checker/` | `/resources/credit-report-checklist/` |
| Loan Denial Reason Checker | Credit/report issue | `/resources/credit-report-checklist/` | `/tools/credit-denial-action-checklist/` |
| Loan Denial Reason Checker | DTI/debt pressure | `/tools/debt-payoff-calculator/` | `/answers/debt-to-income-ratio-explained/` |
| Loan Denial Reason Checker | Business document issue | `/tools/business-loan-readiness-quiz/` | `/tools/bank-statement-cash-flow-calculator/` |
| Credit Denial Action Checklist | User completed checklist | `/tools/loan-denial-reason-checker/` | `/resources/credit-report-checklist/` |
| Debt Payoff Calculator | High interest savings from avalanche | `/financial-wellness/debt-payoff-strategies/` | `/answers/can-i-do-debt-consolidation-myself/` |
| Debt Payoff Calculator | Payment overload | `/answers/debt-to-income-ratio-explained/` | `/tools/loan-denial-reason-checker/` |
| Credit Score Simulator | Utilization improvement | `/financial-wellness/credit-utilization/` | `/resources/credit-report-checklist/` |
| Credit Score Simulator | Missed-payment risk | `/financial-wellness/credit-score-basics/` | `/tools/debt-payoff-calculator/` |
| MCA Repayment Calculator | High repayment pressure | `/tools/bank-statement-cash-flow-calculator/` | `/answers/merchant-cash-advance-guide/` |
| Bank Statement Cash Flow Calculator | Weak cash-flow readiness | `/tools/mca-repayment-calculator/` | `/tools/business-loan-readiness-quiz/` |
| State Consumer Credit Regulator Directory | State selected | `/state/<slug>/lending-laws/` | `/tools/credit-denial-action-checklist/` |

## Health Score Inputs

First-pass score should be explainable and conservative.

| Input | Direction | Notes |
| --- | --- | --- |
| Credit range | Higher score range improves readiness | Store range only, not exact score unless user provides it later with consent. |
| Report accuracy confidence | Known errors reduce readiness | Route errors to checklist/dispute education. |
| Debt/payment pressure | Higher pressure reduces readiness | Route to debt payoff and DTI content. |
| Business documentation readiness | Ready docs improve business funding readiness | Applies only to business funding flows. |
| Cash-flow pressure | Higher pressure reduces business funding readiness | Route to MCA/cash-flow caution content. |
| Course/checklist completion | Completion improves progression | Do not over-weight passive page views. |
| State/local context saved | Improves personalization, not financial readiness | Used for alert targeting. |

## Dashboard First Screen

Recommended order:

1. CreditDoc Health Score with a plain-English band.
2. One sentence explaining why the score changed.
3. One Next Best Action CTA.
4. Saved Action Plan summary.
5. Recently used tools/checklists.
6. State/local research card if the user has a saved state.

## Open Decisions

- Auth provider: Supabase Auth versus another provider.
- Whether the first dashboard is email-link based or password based.
- Whether Health Score should start hidden behind account creation or visible as
  a temporary session score before save.
- Whether state/regulatory alerts need separate explicit consent from general
  product updates.

