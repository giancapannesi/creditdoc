# CreditDoc Retention And Monetization Blueprint

Source: PDF from Gian Capannesi, received through LongLeader AgentMail on 2026-06-13.

Local source files:

- `/srv/BusinessOps/data/creditdoc_strategic_plan_from_gian_20260613.pdf`
- `/srv/BusinessOps/data/creditdoc_strategic_plan_from_gian_20260613.txt`

## Objective

Move CreditDoc from anonymous, one-session tool usage toward a stateful user
system that can retain users, prescribe next actions, and later monetize through
Engine by MoneyLion or similar offer infrastructure.

The plan should not begin with financial-offer integration. The first milestone
is a reliable CreditDoc account, dashboard, saved action plan, and next-best
action loop.

## Current Repo Reality

CreditDoc currently has:

- Public free tools and calculators under `/tools/`.
- A tools hub at `/tools/`.
- A Supabase-backed intake endpoint at `/api/origination-intake`.
- Existing storage patterns for `lead_captures` and `user_quiz_responses`.
- Tool intake currently configured for:
  - `credit-repair-qualify-quiz`
  - `business-loan-readiness-quiz`
- No visible app-level login, signup, account, or dashboard route in the repo.
- No committed first-party auth client dependency in `package.json`.

## Product Direction

The PDF proposes five linked product moves:

1. Gated output: show partial tool results publicly, then require account
   creation to save and unlock the full personalized CreditDoc Action Plan.
2. CreditDoc Health Score: a proprietary 0-1000 score aggregating quiz,
   course, tool, and eventually connected-account signals.
3. Dashboard: the user's home base, with Health Score first and a clear action
   path below it.
4. Next Best Action engine: route users from their latest result to the next
   useful tool, course, checklist, state page, or provider research path.
5. Monetization later: only map to Engine by MoneyLion after enough profile
   data is collected naturally and the dashboard loop works.

## Implementation Sequence

### Phase 0 - Safety And Data Design

Goal: define the retention model without changing live user behavior.

Tasks:

- Document the user journey from anonymous page visit to saved action plan.
- Define the minimum account data model.
- Define Health Score inputs and ranges.
- Define Next Best Action rules.
- Confirm privacy/disclosure copy for storing tool results.
- Decide whether Supabase Auth or a separate auth provider will own accounts.

Deliverables:

- `docs/plans/2026-06-15-creditdoc-retention-monetization-blueprint.md`
- SQL migration draft for user action plan tables.
- Tool-to-NBA mapping table.

### Phase 1 - Extend Existing Intake Without Gating

Goal: collect structured completions from every meaningful tool while keeping
the public site stable.

Tasks:

- Extend `/api/origination-intake` to cover:
  - `borrowing-power-quiz`
  - `loan-denial-reason-checker`
  - `debt-payoff-calculator`
  - `credit-score-simulator`
  - `mca-repayment-calculator`
  - `bank-statement-cash-flow-calculator`
- Keep sensitive data out of payloads.
- Store only normalized ranges, categorical answers, calculated summaries, and
  recommended routes.
- Add a `save_plan_intent` or similar field so the same endpoint can support
  later account creation.

Risk:

- Low to medium. This touches tool scripts and an API route but does not require
  authentication or a dashboard.

### Phase 2 - Action Plan Preview And Soft Gate

Goal: introduce the retention concept without breaking free-tool trust.

Tasks:

- At the end of selected quizzes, show:
  - partial result summary
  - visible next step
  - "Save my CreditDoc Action Plan" CTA
- Do not remove all public value immediately. Use a soft gate first.
- Add a no-password email capture path if full auth is not ready.
- Store an action-plan record linked by `session_id` and email.

Risk:

- Medium. This changes conversion behavior and needs careful copy.

### Phase 3 - Dashboard And Health Score

Goal: provide a reason to return.

Tasks:

- Add `/dashboard/` route.
- Add `/account/` or `/login/` route after auth choice is finalized.
- Create a first-pass CreditDoc Health Score:
  - score range: 0-1000
  - bands: Needs Review, Building, Improving, Ready To Compare
  - inputs: credit range, debt pressure, report accuracy, documentation
    readiness, business cash-flow pressure, course/checklist completions
- Dashboard first screen:
  - Health Score
  - latest Action Plan
  - one Next Best Action
  - saved tools/checklists

Risk:

- High. Requires auth/session design, user data rules, and live QA.

### Phase 4 - Next Best Action Engine

Goal: connect the whole site into a multi-session journey.

Initial rule examples:

- Credit report errors -> Credit Report Checklist -> Dispute guide -> Credit
  repair provider research.
- High debt pressure -> Debt Payoff Calculator -> DTI guide -> loan denial
  checker.
- Business revenue ready + documents ready -> Business loan research.
- Business cash-flow pressure high -> MCA calculator -> cash-flow calculator ->
  caution content.
- State/local risk -> state lending-law page -> regulator directory -> checklist.

Risk:

- Medium. Logic is straightforward, but bad recommendations can damage trust.

### Phase 5 - Retention Alerts

Goal: use existing indexed content as personalized reactivation triggers.

Tasks:

- Map user state, business type, and problem area to relevant pages.
- Send email alerts only where there is clear user consent.
- Avoid legal-advice framing. Use "new CreditDoc research relevant to your
  saved profile" language.

Risk:

- Medium to high because email consent, compliance copy, and unsubscribe
  handling matter.

### Phase 6 - Engine By MoneyLion Readiness

Goal: prepare monetization only after the dashboard loop works.

Tasks:

- Get current official Engine by MoneyLion API requirements before building.
- Map CreditDoc fields to required offer fields.
- Identify required disclosures and consent checkpoints.
- Trigger offers contextually from score milestones, not as generic ads.

Risk:

- High. Requires current commercial/API terms, privacy review, and compliance
  review before implementation.

## Immediate Work We Can Do Safely

1. Finish this repo plan document.
2. Build the tool-to-NBA mapping file in code or data.
3. Extend `/api/origination-intake` to additional tools without changing their
   public UX.
4. Add soft "Save Action Plan" copy to one pilot tool only.
5. Draft the dashboard route behind noindex/internal links, without adding it to
   navigation until auth is ready.

## Work To Avoid For Now

- Do not hard-gate every tool result immediately.
- Do not remove "free/no signup" claims until the product flow actually changes.
- Do not integrate Engine by MoneyLion before official docs, field mapping,
  consent handling, and dashboard retention are in place.
- Do not collect SSNs, bank credentials, exact account numbers, or raw sensitive
  documents through tool forms.

## Recommended Pilot

Pilot on `business-loan-readiness-quiz` because it already posts structured
completion data to `/api/origination-intake` and already has an optional email
capture section.

Pilot behavior:

- Keep the on-page result visible enough to preserve trust.
- Add "Save your CreditDoc Action Plan" CTA after the result.
- Store the result under the existing `session_id`.
- Add a dashboard placeholder only after the save path works.

