# CreditDoc GSC-Led SEO Settle And Upgrade Plan

> **For Claude/Codex:** REQUIRED SKILL: Use `creditdoc-seo-growth` before executing this plan. Use `verification-before-completion` before claiming a batch is complete.

**Goal:** Keep improving CreditDoc pages as Google discovers them, without constantly disturbing the site before SEO signals have time to settle.

**Architecture:** Google Search Console decides the work queue. CreditDoc upgrades pages in controlled batches, deploys once per batch, checks every touched live URL, then waits for measurable GSC movement before changing those same pages again.

**Tech Stack:** CreditDoc Astro/Cloudflare Worker, Supabase/runtime database, local SQLite mirror, GSC exports/workpacks, existing DB update tools, `npm run build`, `./deploy.sh`.

---

## Operating Principle

CreditDoc should not be edited randomly just because a page exists.

The right loop is:

1. Let Google discover pages.
2. Pull real GSC data.
3. Identify pages with impressions, rankings, or near-click potential.
4. Improve a small batch.
5. Deploy once.
6. Check every touched live URL.
7. Leave that batch alone long enough for Google to measure it.

This prevents SEO noise, protects live pages, and makes it possible to know what actually worked.

## Cadence

Run this workflow weekly, unless there is a live-site defect.

- **Monday:** Pull and inspect latest GSC data.
- **Tuesday:** Build the next candidate batch from real GSC pages/queries.
- **Wednesday/Thursday:** Upgrade only the approved batch.
- **After deploy:** Check every touched page live.
- **Next 7 days:** Do not re-edit the same pages unless there is a factual error, 404, noindex mistake, schema issue, legal/compliance issue, or Jammi explicitly directs it.
- **21-28 days:** Judge SEO movement for the batch.

## Batch Size

Default batch size:

- Review pages: 10-25 pages.
- City/category pages: 5-15 pages.
- Best/compare/answer pages: 3-10 pages.
- Template/code changes: one release scope only, then broader smoke tests.

Do not mix too many page types in one batch unless the change is a small shared template improvement.

## Page Selection Rules

Use real GSC data only. Do not guess.

Prioritize:

1. Pages with impressions and average position 8-30.
2. Pages with impressions, zero clicks, and weak title/meta fit.
3. Pages Google is discovering but where content quality is weak.
4. Pages with commercial intent and clear user need.
5. Pages that can be improved with internal links to answers, financial wellness, course, quiz, best pages, or relevant city/category pages.

Deprioritize:

- Pages with no GSC signal unless they are strategic seed pages.
- Raw, blank, low-confidence, or non-financial pages.
- Pages indexed for less than 7 days unless there is a defect.
- Pages needing factual research we cannot verify.

## Mandatory Safety Rules

- Database is the source of truth for live lender/profile facts.
- Do not edit `src/content/lenders/*.json` directly for live page changes.
- Do not invent Google ratings, reviews, prices, services, licensing, regulatory status, or customer outcomes.
- Public star ratings and AggregateRating schema must use stored Google rating plus stored Google review count only.
- No unverified pricing.
- No unsupported negative claims.
- No page gets moved from hold/manual/noindex to indexable without evidence and review.
- Every project section that touches pages must end by checking touched live URLs.

## Weekly Workflow

### Task 1: Pull The Latest GSC Workpack

**Files / data:**

- Read latest GSC exports/workpacks under `/srv/BusinessOps/CreditDoc Project Improvement/`.
- Check local GSC tables if needed: `gsc_page_history`, `gsc_query_history`, `gsc_weekly_pulls`.
- Record the date window and pull ID in the batch notes.

**Output:**

- A candidate CSV with URL, page type, clicks, impressions, CTR, average position, top queries, and current action recommendation.

### Task 2: Segment Candidates

Segment pages into:

- `upgrade_now`: enough GSC signal and page is safe to improve.
- `monitor_only`: already improved recently or too new.
- `manual_review`: content/facts/index status need human review.
- `technical_fix`: 404, wrong canonical, noindex mistake, robots/sitemap mismatch, broken page, schema mismatch.
- `do_not_touch`: no clear benefit or unsafe facts.

**Output:**

- Save batch CSV under `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_GSC_Led_Upgrade_<date>/`.

### Task 3: Create A Small Batch Plan

For each selected page, specify the exact improvement:

- Title/meta rewrite from real query intent.
- Add or improve internal links.
- Add relevant FAQ only if visible content supports it.
- Strengthen services/location/consumer context from DB facts.
- Add course/financial wellness/quiz link where genuinely useful.
- Hold/noindex if the page is being discovered but quality is not safe.

**Rule:** Do not batch pages simply because they share a category. Batch pages because GSC shows opportunity.

### Task 4: Execute The Batch

Use existing CreditDoc DB/update tools where facts or metadata live in the database.

Use Astro/template edits only when a reusable pattern improves many pages without changing unverified facts.

Keep changes scoped to the batch.

### Task 5: Verify Before Deploy

Run:

```bash
cd /srv/BusinessOps/creditdoc
npm run build
```

Expected:

- Robots contract passes.
- SSR sitemap parity passes.
- Astro build passes.
- Sitemap/robots conflict check passes.

Do not deploy if build fails.

### Task 6: Deploy Once

Deploy only after the release scope is understood.

Run:

```bash
cd /srv/BusinessOps/creditdoc
source /srv/BusinessOps/.env
unset CLOUDFLARE_API_TOKEN
export CLOUDFLARE_API_KEY="$CLOUDFLARE_GLOBAL_API_KEY"
./deploy.sh
```

Record the Cloudflare Worker Version ID in the batch notes.

### Task 7: Live Page Status Checks

After deploy, check every touched URL when practical.

For each touched page, record:

- HTTP status.
- Final URL after redirects.
- Title.
- Canonical.
- `noindex` state.
- Whether old/bad content is gone.
- Whether key internal links render.
- Whether AggregateRating schema appears only when Google rating + review count is visible.

If the batch is too large, run a full scripted HTTP status check for all touched URLs and spot-check rendered HTML on representative pages.

No batch is complete until this is done.

### Task 8: Measurement Window

Do not rework the same batch immediately.

Measurement checkpoints:

- First check: next GSC pull.
- Early signal: 7-14 days.
- Real judgement: 21-28 days.

Track:

- Impressions.
- Clicks.
- CTR.
- Average position.
- Query changes.
- Indexed/not indexed status.
- Any new 404/noindex/canonical issue.

## Success Metrics

Short-term:

- Zero touched-page 404s.
- Zero accidental noindex/index mistakes.
- Zero unsupported rating/pricing claims.
- More pages receiving impressions.
- CTR improving on pages already ranking.

Medium-term:

- More review pages moving from positions 20-40 into 8-20.
- More review/city/answer pages generating first clicks.
- Clear winners by query type and page type.

Long-term:

- Repeatable page-improvement system driven by Google discovery.
- Less random editing.
- Stronger internal link graph around commercial review pages, answers, financial wellness, courses, quizzes, and city/category pages.

## Stop Conditions

Pause page upgrades if:

- A deploy creates 404s or broken SSR routes.
- GSC shows a new widespread indexing/robots/canonical issue.
- A batch introduces unsupported factual claims.
- The worktree is too dirty to isolate release scope.
- Jammi asks to freeze changes.

When paused, only fix live defects and measurement tooling until the site is stable.
