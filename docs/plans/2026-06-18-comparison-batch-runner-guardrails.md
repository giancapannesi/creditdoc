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
- The first autonomous campaign should run as `10 x 20`: ten sequential batches of 20 pages each.
- The loop must produce a full batch report and cumulative campaign report after each 20-page batch before starting the next batch.
- The runner must abort on stale DB/export mismatch.
- The runner must abort if changed slugs differ from selected slugs.
- The runner must write reports before and after every batch.
- Independent review is required for all anomalies plus a sample of normal rows.
- A separate final checker is required after batch implementation. The checker must not be the same AI/session that selected, generated, or applied the batch.
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

Each group should start at 20 rows. The first campaign target is ten 20-page batches, not one large 200-page rewrite. Increase beyond 20 rows per batch only after the 10-batch campaign proves the checkers are working cleanly.

## First Campaign Shape: 10 x 20

The initial scalable run should be a campaign with these limits:

- `campaign_id`: `comparison-pricing-safety-10x20-001`
- `batch_count`: 10
- `batch_size`: 20
- maximum campaign scope: 200 selected comparison pages
- execution style: sequential batches, never one bulk edit
- checkpoint after every 20-page batch

Each batch must complete this cycle before the next batch starts:

```text
20-page batch selected
  -> all deterministic checks pass
  -> content reviewer returns corrections/pass
  -> corrections applied
  -> deterministic checks pass again
  -> separate final checker returns pass
  -> batch report written
  -> cumulative campaign report updated
  -> commit/deploy checkpoint handled according to approval rules
  -> only then select/start next 20-page batch
```

The report after each batch must summarize the entire current campaign, not only the just-finished batch:

- campaign progress: batch `N` of `10`
- total pages selected so far
- total pages changed so far
- total pages skipped and reasons
- checker failures and corrections across all completed batches
- source-fact corrections found by reviewers
- pricing fields preserved
- missing-pricing cases converted to uncertainty language
- build/deploy/live verification status
- current repo status
- next batch group and selection rationale

If any batch fails final checker review, live verification, or repo cleanliness, the loop stops and writes a blocked campaign report instead of moving to the next batch.

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
  -> separate final checker review
  -> commit checkpoint
  -> deploy checkpoint
  -> live URL scan
  -> memory/report write
```

Token control:

- Do not send full pages to an LLM.
- Review packets should include only slug, current fields, proposed changed fields, allowed source facts, and checker findings.
- Send every anomaly to a review agent, plus 3-5 sampled non-anomaly rows per batch.
- Send the final checker a compact evidence bundle, not the full working context: manifest, git diff summary, source-fact packet, raw scan, rendered scan, build result, independent review result, and proposed commit message.
- Use deterministic scripts for repetitive scans and counts.

## Independent Final Checker Requirement

Every batch must have two separate review layers:

1. **Content reviewer**
   - Reviews anomalies plus sampled rows before commit.
   - Checks whether useful page value is preserved.
   - Checks unsupported prices, ratings, guarantees, accreditation, and negative claims.
   - May suggest copy corrections.

2. **Final checker**
   - Runs after corrections and after all deterministic checks pass.
   - Must be a different AI/session from the batch implementer and content reviewer where possible.
   - Must not edit files.
   - Must answer pass/fail against the evidence bundle.
   - Must explicitly check:
     - selected slugs equal changed slugs
     - only allowed fields changed
     - DB freshness gate passed before edits
     - no page was removed, redirected, or noindexed
     - source-supported pricing was preserved
     - missing pricing was not fabricated
     - rendered pages contain enrichment sections
     - build and sitemap checks passed
     - repo can be cleanly committed

The batch cannot be committed or deployed if the final checker returns `fail`, `needs correction`, or an incomplete review.

## Task 1: Create Batch Workpack Format

**Files:**
- Create: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_Runner_2026-06-18/README.md`
- Create: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_Runner_2026-06-18/batch_manifest.example.json`
- Create: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_Runner_2026-06-18/campaign_manifest.example.json`

**Step 1: Write the README**

Document:

- group names
- max batch size
- first campaign shape: `10 x 20`
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

Create the campaign manifest example:

```json
{
  "campaign_id": "comparison-pricing-safety-10x20-001",
  "batch_count": 10,
  "batch_size": 20,
  "max_total_rows": 200,
  "batch_ids": [],
  "requires_report_after_each_batch": true,
  "requires_cumulative_report_before_next_batch": true,
  "stop_on_final_checker_failure": true,
  "stop_on_live_check_failure": true,
  "stop_on_dirty_repo": true
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

## Task 10: Add Campaign Reporter And Loop Gate

**Files:**
- Create: `scripts/write_comparison_campaign_report.mjs`
- Create: `scripts/check_comparison_campaign_can_continue.mjs`

**Step 1: Implement campaign report writer**

Inputs:

- campaign manifest
- all completed batch manifests
- all completed batch reports
- checker results
- live reports
- git status snapshot

Output:

- `campaign_report.md`
- `campaign_report.json`

The report must cover the whole campaign to date after every batch, including:

- batch `N` of `10`
- all completed batch ids
- total changed pages
- total skipped pages
- all final checker verdicts
- all reviewer corrections
- pricing preserved count
- missing-pricing uncertainty count
- build/deploy/live status by batch
- whether the next batch may start

**Step 2: Implement continue gate**

`scripts/check_comparison_campaign_can_continue.mjs` must fail if:

- latest batch report is missing
- cumulative campaign report is missing
- final checker did not pass
- live verifier did not pass when deployment occurred
- repo is dirty unexpectedly
- campaign already reached 10 batches
- any blocker exists in cumulative report

**Step 3: Add npm scripts**

```json
"comparison:campaign:report": "node scripts/write_comparison_campaign_report.mjs",
"comparison:campaign:can-continue": "node scripts/check_comparison_campaign_can_continue.mjs"
```

**Step 4: Commit**

```bash
git add package.json scripts/write_comparison_campaign_report.mjs scripts/check_comparison_campaign_can_continue.mjs
git commit -m "feat: add comparison campaign reporting gate"
```

## Task 11: Add Final Checker Packet And Gate

**Files:**
- Create: `scripts/build_comparison_final_checker_packet.mjs`
- Create: `scripts/check_comparison_final_checker_result.mjs`

**Step 1: Build final checker packet**

The packet builder must collect only compact evidence:

- manifest
- changed slug list from scope gate
- changed field list from scope gate
- DB freshness report
- source fact packet
- raw claim safety report
- rendered HTML report
- build/postbuild command outcome
- content reviewer result
- `git diff --stat`
- `git diff -- src/content/comparisons.json` limited to changed records

Output:

- `final_checker_packet.json`
- `final_checker_packet.md`

The packet must include this instruction:

```text
You are the final checker, not the implementer. Do not edit files. Decide pass/fail only.
Fail the batch if selected slugs do not equal changed slugs, if fields outside the manifest changed, if source-supported prices were removed, if missing prices were fabricated, if pages were removed/redirected/noindexed, if rendered enrichment sections are missing, or if build/check evidence is absent.
```

**Step 2: Add final checker result schema**

The checker result must be saved as JSON:

```json
{
  "checker_agent_id": "",
  "batch_id": "",
  "verdict": "pass",
  "checked_items": {
    "selected_slugs_equal_changed_slugs": true,
    "only_allowed_fields_changed": true,
    "db_freshness_gate_passed": true,
    "no_route_index_or_delete_changes": true,
    "source_supported_prices_preserved": true,
    "missing_prices_not_fabricated": true,
    "rendered_enrichment_present": true,
    "build_and_sitemap_checks_passed": true
  },
  "blockers": [],
  "notes": ""
}
```

Only `verdict: "pass"` may proceed to commit.

**Step 3: Implement result checker**

`scripts/check_comparison_final_checker_result.mjs` must:

- parse the final checker JSON
- require `verdict === "pass"`
- require every `checked_items` value to be true
- require `checker_agent_id` to be present
- fail if the result came from the same recorded implementer agent/session when that metadata is available
- print all blockers on failure

**Step 4: Add npm scripts**

```json
"comparison:batch:final-checker-packet": "node scripts/build_comparison_final_checker_packet.mjs",
"comparison:batch:final-checker-result": "node scripts/check_comparison_final_checker_result.mjs"
```

**Step 5: Commit**

```bash
git add package.json scripts/build_comparison_final_checker_packet.mjs scripts/check_comparison_final_checker_result.mjs
git commit -m "feat: add final checker gate for comparison batches"
```

## Task 12: Add Memory And Resume Writer

**Files:**
- Create: `scripts/write_comparison_batch_memory.mjs`

**Step 1: Implement memory writer**

Inputs:

- manifest
- preflight report
- claim report
- rendered report
- independent review summary
- final checker result
- campaign report
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
- final checker verdict and checker agent/session id
- campaign progress and whether the next batch may start
- verification commands and outcomes
- deploy version
- next batch recommendation
- any aborted attempt or stale DB issue

**Step 3: Commit**

```bash
git add scripts/write_comparison_batch_memory.mjs
git commit -m "feat: write comparison batch memory notes"
```

## Task 13: Pilot The First 20-Page Batch In The 10 x 20 Campaign

**Files:**
- Create: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_Runner_2026-06-18/<batch-id>/manifest.json`
- Generated reports under that same batch folder.
- Modify only: `src/content/comparisons.json`

**Step 1: Create campaign manifest**

Create `comparison-pricing-safety-10x20-001` with ten 20-page batch slots.

**Step 2: Select one group**

Use `credit-repair-pricing-refunds-001` with max 20 rows.

**Step 3: Run preflight**

```bash
npm run comparison:batch:preflight -- --manifest <manifest.json>
```

Expected: DB freshness gate passes, fact packet written.

**Step 4: Apply content updates through DB path**

Use existing `CreditDocDB.add_comparison(..., updated_by='founder')`, preserving all fields not in scope.

**Step 5: Run full check mode**

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

**Step 6: Independent review**

Send review packet to a debug/review agent. Require:

- all blocker/anomaly rows reviewed
- 3-5 normal rows sampled
- explicit statement on whether content value is preserved
- exact corrections if facts are wrong

**Step 7: Patch reviewer corrections**

Apply only reviewer-supported corrections.

**Step 8: Re-run checks**

Run check mode again and require clean output.

**Step 9: Build final checker packet**

```bash
npm run comparison:batch:final-checker-packet -- --manifest <manifest.json>
```

Expected:

- `final_checker_packet.json` written
- `final_checker_packet.md` written

**Step 10: Separate final checker**

Send the final checker packet to a separate checker agent/session. This must not be the same agent/session that implemented the batch, and it should not be the same content reviewer where avoidable.

The checker must return the required JSON result. It must not edit files.

**Step 11: Verify final checker result**

```bash
npm run comparison:batch:final-checker-result -- --result <final-checker-result.json>
```

Expected: exits `0` only for a full `pass`.

**Step 12: Write full batch and campaign report**

```bash
npm run comparison:campaign:report -- --campaign <campaign-manifest.json> --latest-batch <manifest.json>
npm run comparison:campaign:can-continue -- --campaign <campaign-manifest.json>
```

Expected:

- batch report exists
- cumulative campaign report exists
- continue gate explicitly says whether batch 2 may start

**Step 13: Commit**

```bash
git add src/content/comparisons.json
git commit -m "fix: clean comparison pricing batch credit repair 001"
```

**Step 14: Deploy checkpoint**

Only after founder approval or standing approval for this exact phase:

```bash
/srv/BusinessOps/creditdoc/deploy.sh
```

**Step 15: Live verify**

```bash
node scripts/check_live_comparison_batch.mjs --manifest <manifest.json>
```

**Step 16: Update campaign report after live verify**

```bash
npm run comparison:campaign:report -- --campaign <campaign-manifest.json> --latest-batch <manifest.json>
npm run comparison:campaign:can-continue -- --campaign <campaign-manifest.json>
```

The loop may only move to the next 20-page batch if the continue gate passes.

**Step 17: Write memory**

```bash
node scripts/write_comparison_batch_memory.mjs --manifest <manifest.json> --commit <hash> --deploy-version <version>
```

## Task 14: Loop Through Remaining 9 Batches

For batches 2 through 10:

- repeat Task 13 with the next 20-page manifest
- write both batch and cumulative campaign reports before selecting the next batch
- stop immediately on any failed deterministic check, content review blocker, final checker failure, live check failure, or dirty repo
- do not increase batch size during the 10-batch campaign

After batch 10:

- write a final campaign report
- summarize all changed pages, skipped pages, reviewer corrections, final checker verdicts, deployment versions, and remaining inventory
- recommend whether future campaigns should stay at 20 pages, move to 30 pages, or split by lower-risk group

## Task 15: Increase Batch Size Only With Evidence

After one full clean 10 x 20 campaign:

- consider 30-page batches for the same group type
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
- Separate final checker returned a full pass after corrections and deterministic checks.
- Batch report and cumulative campaign report were written before moving on.
- Campaign continue gate passed before selecting the next batch.
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
