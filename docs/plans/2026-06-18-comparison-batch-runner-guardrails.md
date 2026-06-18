# CreditDoc Comparison Batch Runner Guardrails Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a controlled batching system for CreditDoc comparison cleanup/enrichment so 20-30 page groups can run with deterministic guardrails, low token usage, independent review gates, and no broad damaging rewrites.

**Architecture:** Add a script-led batch runner around the existing comparison DB/export workflow. The runner selects a bounded group, checks DB freshness, extracts allowed facts from current source fields, prepares neutral patches, runs raw/rendered/live checkers, writes machine-readable reports, and pauses for commit/deploy only when every gate passes.

**Tech Stack:** Node scripts for JSON/rendered checks, existing Python `tools/creditdoc_db.py` DB path, Astro build output, existing `src/content/comparisons.json`, existing inventory workpacks under `/srv/BusinessOps/CreditDoc Project Improvement/`, Git worktrees, Cloudflare deploy script.

---

## Non-Negotiable Guardrails

- No blind bulk rewrites.
- No page removal, redirect, or noindex changes in this runner.
- No direct lender JSON edits.
- No fabricated prices, guarantees, savings claims, ratings, accreditation, or negative trust claims.
- Pricing may be shown only when present in current CreditDoc source fields.
- Missing pricing must become uncertainty language, not a fake price and not "free".
- Each batch must have a maximum size, initially 20-30 pages.
- The runner must abort on stale DB/export mismatch.
- The runner must abort if changed slugs differ from selected slugs.
- The runner must write reports before and after every batch.
- Independent review is required for all anomalies plus a sample of normal rows.
- Commit and deploy remain explicit checkpoint actions, not hidden in the long-running loop.

## Batch Groups

Use pattern batches instead of arbitrary next-10 batches:

1. `credit-repair-pricing-refunds`
   - Focus: monthly/setup fees, first-work fees, refund terms, BBB/accreditation wording.
2. `nonprofit-dmp-fees`
   - Focus: DMP monthly/setup fee language, state-dependent fee caveats, nonprofit/counseling certifications.
3. `bureau-monitoring-fintech`
   - Focus: bureau identity, subscription pricing, monitoring vs repair distinction, referral-model caveats.
4. `emergency-cash-apr`
   - Focus: APR, fee, payday/installment language, state-law context, no "safe" or "best" claims.
5. `secured-card-credit-builder`
   - Focus: deposits, admin fees, loan mechanics, credit reporting, graduation/review caveats.

Each group should start at 20 rows. Increase only after two consecutive clean batches with no reviewer corrections that affect source facts.

## Checker Loop Design

The unattended loop should run deterministic checks and stop at checkpoints:

```text
select batch
  -> DB freshness gate
  -> source fact extraction
  -> draft patch generation
  -> changed-scope gate
  -> raw JSON safety scan
  -> build
  -> rendered HTML scan
  -> independent review packet generation
  -> wait for review result
  -> commit checkpoint
  -> deploy checkpoint
  -> live URL scan
  -> memory/report write
```

Token control:

- Do not send full pages to an LLM.
- Review packets should include only slug, current fields, proposed changed fields, allowed source facts, and checker findings.
- Send every anomaly to a review agent, plus 3-5 sampled non-anomaly rows per batch.
- Use deterministic scripts for repetitive scans and counts.

## Task 1: Create Batch Workpack Format

**Files:**
- Create: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_Runner_2026-06-18/README.md`
- Create: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_Runner_2026-06-18/batch_manifest.example.json`

**Step 1: Write the README**

Document:

- group names
- max batch size
- allowed field edits: `summary`, `winner_reason`, `seo_description`
- forbidden edits: routes, indexability, lender JSON, redirects, page deletion
- required reports
- checkpoint rules

**Step 2: Create manifest example**

```json
{
  "batch_id": "credit-repair-pricing-refunds-001",
  "group": "credit-repair-pricing-refunds",
  "max_rows": 20,
  "source_inventory": "/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Pricing_Safety_Phase_1_2026-06-17/comparison_risk_inventory_2026-06-17.csv",
  "selected_slugs": [],
  "allowed_fields": ["summary", "winner_reason", "seo_description"],
  "forbidden_actions": ["delete", "redirect", "noindex", "lender_json_edit"],
  "requires_independent_review": true
}
```

**Step 3: Commit**

```bash
git -C /srv/BusinessOps/creditdoc status --short
```

Do not commit these workpack files from the CreditDoc repo if they sit outside the repo. Record them in memory instead.

## Task 2: Add DB Freshness Gate

**Files:**
- Create: `scripts/check_comparison_db_freshness.mjs`

**Step 1: Implement checker**

The script must:

- read `src/content/comparisons.json`
- query local SQLite `data/creditdoc.db` table `comparisons`
- compare row count
- compare per-slug hash of `summary`, `winner_reason`, and `seo_description`
- print a report to stdout
- exit `0` only when local DB and committed JSON match for comparison rows
- exit non-zero with a clear stale-DB warning when mismatched

**Step 2: Add npm script**

Modify `package.json`:

```json
"check:comparison-db-freshness": "node scripts/check_comparison_db_freshness.mjs"
```

**Step 3: Verify**

Run:

```bash
npm run check:comparison-db-freshness
```

Expected:

- `OK comparison DB matches src/content/comparisons.json`
- or a hard fail that explains the mismatch and blocks the batch.

**Step 4: Commit**

```bash
git add package.json scripts/check_comparison_db_freshness.mjs
git commit -m "feat: add comparison db freshness check"
```

## Task 3: Add Batch Scope Gate

**Files:**
- Create: `scripts/check_comparison_batch_scope.mjs`

**Step 1: Implement checker**

Inputs:

```bash
node scripts/check_comparison_batch_scope.mjs --base HEAD --manifest <manifest.json>
```

The script must:

- diff `src/content/comparisons.json` against the base ref
- list changed comparison slugs
- verify changed slugs exactly match `selected_slugs`
- verify only allowed fields changed
- fail if any rows were added or removed
- fail if any changed page is outside the manifest

**Step 2: Add npm script**

```json
"check:comparison-batch-scope": "node scripts/check_comparison_batch_scope.mjs"
```

**Step 3: Verify with a known clean tree**

Run:

```bash
npm run check:comparison-batch-scope -- --base HEAD --manifest /path/to/manifest.json
```

Expected on a clean tree: `OK no comparison changes` or an explicit message that no batch changes are present.

**Step 4: Commit**

```bash
git add package.json scripts/check_comparison_batch_scope.mjs
git commit -m "feat: add comparison batch scope guard"
```

## Task 4: Add Source Fact Extractor

**Files:**
- Create: `scripts/extract_comparison_source_facts.mjs`

**Step 1: Implement extractor**

For each selected slug, output a compact JSON packet:

```json
{
  "slug": "example-vs-example",
  "lender_a": {
    "name": "",
    "category": "",
    "pricing": {},
    "bbb_rating": "",
    "bbb_accredited": null,
    "google_rating": null,
    "google_reviews": null,
    "services": [],
    "pros": [],
    "cons": []
  },
  "lender_b": {}
}
```

The extractor must use current CreditDoc source fields only. It must not scrape the web or infer missing facts.

**Step 2: Add fact uncertainty labels**

Emit flags:

- `has_pricing_a`
- `has_pricing_b`
- `pricing_missing_a`
- `pricing_missing_b`
- `bbb_accreditation_supported_a`
- `bbb_accreditation_supported_b`

**Step 3: Verify on slice 5 slugs**

Run against the 10 slice-5 slugs and confirm the packet includes the corrected facts for The Credit People and National Credit Fixers.

**Step 4: Commit**

```bash
git add scripts/extract_comparison_source_facts.mjs
git commit -m "feat: extract comparison source facts"
```

## Task 5: Add Raw Claim Safety Scanner

**Files:**
- Create: `scripts/check_comparison_claim_safety.mjs`

**Step 1: Implement scanner**

Scan selected `summary`, `winner_reason`, and `seo_description` fields for risky patterns:

- `best`
- `winner`
- `guaranteed`
- `guarantee`
- `superior`
- `better value`
- `clear pick`
- `safer choice`
- `lowest`
- `no BBB rating`
- `red flag`
- `saves`
- unpaired dollar amounts not present in extracted source facts
- APR/rate claims not present in extracted source facts
- accreditation claims where `bbb_accredited` is not true

**Step 2: Make severity levels**

- `blocker`: unsupported price/rate/accreditation, forbidden route/index/delete changes
- `review`: softer words such as `best` or `winner` that might be title text but should be reviewed
- `info`: source-supported price/rating found

**Step 3: Verify**

Run:

```bash
node scripts/check_comparison_claim_safety.mjs --manifest <manifest.json> --facts <facts.json>
```

Expected: exits non-zero on blockers; writes JSON report.

**Step 4: Commit**

```bash
git add scripts/check_comparison_claim_safety.mjs
git commit -m "feat: add comparison claim safety scanner"
```

## Task 6: Add Rendered HTML Scanner

**Files:**
- Create: `scripts/check_rendered_comparison_batch.mjs`

**Step 1: Implement scanner**

After `npm run build`, for each selected slug:

- confirm `dist/compare/<slug>/index.html` exists
- confirm rendered HTML contains:
  - `Quick Decision Map`
  - `CreditDoc Tools and Guides for This Comparison`
  - `Before You Contact Either Company`
- scan rendered HTML for the same risky claim patterns
- fail on blockers

**Step 2: Verify**

Run against the last deployed 10 slugs after a build.

**Step 3: Commit**

```bash
git add scripts/check_rendered_comparison_batch.mjs
git commit -m "feat: check rendered comparison batches"
```

## Task 7: Add Review Packet Generator

**Files:**
- Create: `scripts/build_comparison_review_packet.mjs`

**Step 1: Generate small LLM packets**

For a selected batch, write:

- `review_packet.json`
- `review_packet.md`

Each row should include:

- slug
- group
- changed fields before/after
- extracted allowed facts
- scanner findings
- exact question for reviewer:
  - "Does this preserve useful page value?"
  - "Are any prices, ratings, guarantees, or accreditation claims unsupported?"
  - "Is the language too restrictive or likely to reduce user value?"

**Step 2: Token cap**

Hard cap each row packet to compact fields only. Do not include full rendered HTML.

**Step 3: Commit**

```bash
git add scripts/build_comparison_review_packet.mjs
git commit -m "feat: generate comparison review packets"
```

## Task 8: Add Batch Runner Orchestrator

**Files:**
- Create: `scripts/run_comparison_batch_guarded.mjs`

**Step 1: Implement non-mutating preflight mode**

Run:

```bash
node scripts/run_comparison_batch_guarded.mjs --manifest <manifest.json> --mode preflight
```

It must run:

- DB freshness gate
- source fact extraction
- scope preview
- write preflight report

No content edits.

**Step 2: Implement check mode**

Run:

```bash
node scripts/run_comparison_batch_guarded.mjs --manifest <manifest.json> --mode check
```

It must run:

- scope gate
- raw claim scanner
- `npm run build`
- rendered scanner
- review packet generator

No commit or deploy.

**Step 3: Implement loop-safe status output**

Write a JSON status file:

```json
{
  "batch_id": "",
  "phase": "preflight|check|review|commit_ready|deploy_ready|live_verified",
  "ok": true,
  "blockers": [],
  "reports": []
}
```

**Step 4: Add npm scripts**

```json
"comparison:batch:preflight": "node scripts/run_comparison_batch_guarded.mjs --mode preflight",
"comparison:batch:check": "node scripts/run_comparison_batch_guarded.mjs --mode check"
```

**Step 5: Commit**

```bash
git add package.json scripts/run_comparison_batch_guarded.mjs
git commit -m "feat: add guarded comparison batch runner"
```

## Task 9: Add Live URL Verifier

**Files:**
- Create: `scripts/check_live_comparison_batch.mjs`

**Step 1: Implement verifier**

After deploy, for each selected slug:

- fetch `https://www.creditdoc.co/compare/<slug>/`
- require HTTP 200
- require enrichment section strings
- fail on risky rendered snippets
- write `live_check_report.json`

**Step 2: Verify**

Run against slice 5 slugs:

```bash
node scripts/check_live_comparison_batch.mjs --manifest <manifest.json>
```

Expected: all 10 return `200`.

**Step 3: Commit**

```bash
git add scripts/check_live_comparison_batch.mjs
git commit -m "feat: verify live comparison batches"
```

## Task 10: Add Memory And Resume Writer

**Files:**
- Create: `scripts/write_comparison_batch_memory.mjs`

**Step 1: Implement memory writer**

Inputs:

- manifest
- preflight report
- claim report
- rendered report
- independent review summary
- commit hash
- deploy version
- live report

Output:

- `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_comparison_batch_<batch_id>_<date>.md`

**Step 2: Include required resume facts**

The memory note must include:

- selected slugs
- exact changed fields
- fact-source corrections
- reviewer corrections
- verification commands and outcomes
- deploy version
- next batch recommendation
- any aborted attempt or stale DB issue

**Step 3: Commit**

```bash
git add scripts/write_comparison_batch_memory.mjs
git commit -m "feat: write comparison batch memory notes"
```

## Task 11: Pilot One 20-Page Batch

**Files:**
- Create: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_Runner_2026-06-18/<batch-id>/manifest.json`
- Generated reports under that same batch folder.
- Modify only: `src/content/comparisons.json`

**Step 1: Select one group**

Use `credit-repair-pricing-refunds-001` with max 20 rows.

**Step 2: Run preflight**

```bash
npm run comparison:batch:preflight -- --manifest <manifest.json>
```

Expected: DB freshness gate passes, fact packet written.

**Step 3: Apply content updates through DB path**

Use existing `CreditDocDB.add_comparison(..., updated_by='founder')`, preserving all fields not in scope.

**Step 4: Run full check mode**

```bash
npm run comparison:batch:check -- --manifest <manifest.json>
```

Expected:

- scope exactly matches selected slugs
- only allowed fields changed
- raw scan passes
- build passes
- rendered scan passes
- review packet written

**Step 5: Independent review**

Send review packet to a debug/review agent. Require:

- all blocker/anomaly rows reviewed
- 3-5 normal rows sampled
- explicit statement on whether content value is preserved
- exact corrections if facts are wrong

**Step 6: Patch reviewer corrections**

Apply only reviewer-supported corrections.

**Step 7: Re-run checks**

Run check mode again and require clean output.

**Step 8: Commit**

```bash
git add src/content/comparisons.json
git commit -m "fix: clean comparison pricing batch credit repair 001"
```

**Step 9: Deploy checkpoint**

Only after founder approval or standing approval for this exact phase:

```bash
/srv/BusinessOps/creditdoc/deploy.sh
```

**Step 10: Live verify**

```bash
node scripts/check_live_comparison_batch.mjs --manifest <manifest.json>
```

**Step 11: Write memory**

```bash
node scripts/write_comparison_batch_memory.mjs --manifest <manifest.json> --commit <hash> --deploy-version <version>
```

## Task 12: Increase Batch Size Only With Evidence

After two clean 20-page batches:

- increase to 30 pages for the same group type
- keep independent review on anomalies plus sampled rows
- do not jump to hundreds

After two clean 30-page batches:

- consider 50-page batches only for low-risk groups such as bureau/monitoring pages
- keep emergency cash/APR and refund/pricing pages capped lower unless scanner precision is proven.

## Final Verification Checklist

Before claiming any batch is complete:

- `git status --short` is clean except intended files before commit, then clean after commit.
- `npm run check:comparison-db-freshness` passed before edits.
- `npm run comparison:batch:check -- --manifest <manifest.json>` passed after edits.
- `npm run build` passed.
- Independent review completed and corrections applied.
- `git diff --check` passed.
- Deployed with `/srv/BusinessOps/creditdoc/deploy.sh` only when approved.
- Live verifier passed after deploy.
- Memory note written.

## Anti-Patterns To Avoid

- Do not let a script rewrite all 340 comparison records.
- Do not rely on an LLM to decide whether a price exists.
- Do not treat a BBB letter grade as accreditation.
- Do not convert missing pricing into "free".
- Do not hide value by deleting useful services, review counts, or stored profile facts.
- Do not commit generated reports into the app repo unless they belong under tracked docs.
- Do not deploy from a dirty tree.

