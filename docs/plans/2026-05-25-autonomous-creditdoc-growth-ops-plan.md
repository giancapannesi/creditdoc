# Autonomous CreditDoc Growth Ops Plan

Date: 2026-05-25  
Owner: Jammi  
Operator: Codex  
Site: `https://www.creditdoc.co`

## Objective

Activate a daily CreditDoc operating loop that improves SEO, page quality, indexability, and pipeline reliability without requiring Jammi to approve every small action.

The system should work like a responsible operating partner:

- use real GSC, database, live-site, and git data;
- improve only pages that are safe to improve;
- keep risky YMYL/profile decisions in hold status;
- deploy only verified low-risk site improvements;
- stop automatically when the repo, live site, database, or automation state is unclear.

## Current Strategy Context

CreditDoc is using the directory/review/page network as the SEO foothold toward an embedded finance and lead-routing business. The business goal is not content volume by itself. The goal is to earn qualified organic traffic, route users into finance/help journeys, and eventually support loan/card/credit-repair origination and lead distribution.

Daily work should therefore prioritize:

1. Pages Google is already surfacing.
2. Review pages with impressions and weak CTR.
3. Raw/weak pages that could harm trust if indexed.
4. Internal linking between review pages, answers, city guides, best/compare pages, tools, course, and financial wellness.
5. Automation reliability so answers, blogs, wellness, comparisons, and city guides keep publishing.

## Non-Negotiable Rules

- Database is the source of truth for lender/profile content.
- Do not edit `src/content/lenders/*.json` as the live source.
- Do not invent Google ratings, pricing, services, licenses, complaint data, or review claims.
- Visible star ratings must use verifiable stored Google rating data with review count.
- Do not index raw, weak, quarantined, or manual-review pages just because they get impressions.
- Every touched URL must end with live status checks.
- Do not deploy from a dirty or unclear worktree.
- Do not restart `creditdoc-engine.service` or the autonomous enrichment loop without Jammi approval.
- Do not buy traffic as part of this process.

## Autonomy Levels

### Green: Codex Can Do Automatically

These actions can run without Jammi approval if all preflight checks pass:

- Pull latest GSC data and create daily workpack.
- Check live URL status for surfaced/touched pages.
- Detect 404s, noindex mismatches, sitemap/robots conflicts, broken internal links, and automation failures.
- Restore generated lender JSON drift when it is metadata/export-only and archive evidence first.
- Improve metadata in the database for already-safe pages using real lender/category/location data.
- Add or improve internal links when they are factual and relevant.
- Add monitoring reports and docs.
- Run builds and smoke checks.
- Deploy low-risk template/guard fixes that pass build and live checks.

### Yellow: Codex Can Prepare But Not Finalize

These can be queued for Jammi review or grouped into a weekly decision packet:

- Indexing decisions for previously held/manual pages.
- Redirect/archive decisions for questionable provider pages.
- Provider profile claims where source evidence is thin or third-party-only.
- New monetization widgets, affiliate CTAs, or lead forms on YMYL pages.
- Any change that materially changes consumer advice wording.

### Red: Requires Jammi Approval

Do not do these without Jammi:

- Restart autonomous enrichment engine.
- Re-enable service loops that can spend AI tokens or edit large profile sets.
- Bulk index hundreds of pages.
- Delete large datasets without archive.
- Change business strategy or vertical priority.
- Add paid traffic.
- Publish live social posts.

## Daily Operating Loop

### 1. Preflight Safety Gate

Run before any SEO/content/page work:

- `git status --short` in `/srv/BusinessOps/creditdoc`.
- Check dirty `src/content/lenders` count.
- Check `creditdoc-engine.service`:
  - active must be `inactive`;
  - enabled must be `disabled`;
  - unit restart must be `Restart=no`;
  - `/srv/BusinessOps/tools/.creditdoc-engine-enabled` must be absent.
- Check recent deployment/build status.
- Check key live routes:
  - `/`
  - `/review/lexington-law/`
  - `/answers/`
  - `/sitemap-index.xml`
  - `/robots.txt`

If lender JSON drift exists:

1. Classify it.
2. If metadata/export-only, archive evidence and restore.
3. If content-bearing, stop and write a decision note.

### 2. Pipeline Health Check

Check the daily production systems:

- Answer pages: latest published row, answer count, `/answers/` live status.
- Blog automation: latest publish, log errors, queue state.
- Wellness/comparison automation: latest publish, log errors.
- City guide automation: latest generated/published rows, route status.
- GSC/indexing jobs: latest pull and failures.
- Site monitor: recent 404/500 reports.
- Email/reporting jobs: any alert failures.

Output:

- `GREEN`, `YELLOW`, or `RED` status.
- exact failed job/log if anything is broken.
- no guesswork.

### 3. GSC-Led Page Selection

Use the latest GSC pull only. Segment pages into:

- new pages appearing for the first time;
- impressions up, clicks zero;
- average position 1-20 but weak CTR;
- review pages appearing;
- answer pages appearing;
- city/category pages appearing;
- pages with clicks that should be protected from over-editing.

Daily limit:

- 5-15 URLs for analysis.
- 3-5 low-risk improvements maximum.
- No huge batch rewrites.

### 4. Page Quality Upgrade

For each selected page:

- verify live status;
- verify canonical;
- verify noindex/index intent;
- check title/meta from real data;
- check internal links to relevant:
  - answers;
  - compare/best pages;
  - financial wellness;
  - tools/quiz;
  - course/resources;
  - city/state pages;
- check visible claims for unsupported ratings, pricing, or service statements.

Allowed automatic improvements:

- better factual title/meta;
- relevant internal links;
- clearer cautious language;
- schema alignment only if visible content supports it;
- template improvements that improve all pages safely.

### 5. Build And Deploy Rule

Deploy only if:

- git diff is understood;
- no unrelated generated lender JSON drift remains;
- `npm run build` passes;
- robots/sitemap checks pass;
- touched live URLs can be checked after deploy.

Deploy path:

- use `/srv/BusinessOps/creditdoc/deploy.sh`;
- do not use bare `wrangler deploy`.

After deploy:

- check every touched URL;
- check homepage;
- check sitemap/robots;
- check no accidental noindex on intended indexable pages.

### 6. Daily Report

Save a daily workpack under:

`/srv/BusinessOps/CreditDoc Project Improvement/Daily_Autonomous_Growth_Ops/YYYY-MM-DD/`

Each report must include:

- git preflight result;
- automation health result;
- latest GSC pull used;
- URLs analyzed;
- actions taken;
- pages touched;
- deploy yes/no and Worker version if yes;
- live URL check results;
- open decisions for Jammi;
- next-day queue.

The report should be short enough to read in five minutes.

## Weekly Review Loop

Once per week:

- summarize GSC deltas;
- list pages gaining impressions;
- list pages losing impressions/clicks;
- list pages upgraded that week;
- list 404/noindex/quality issues found;
- prepare Jammi-only decisions:
  - pages to index;
  - pages to archive;
  - pages to redirect;
  - vertical focus adjustment;
  - lead-routing readiness.

## Implementation Phases

### Phase 1: Manual Codex Daily Loop

Start immediately.

Codex runs the daily checklist manually, saves the workpack, makes low-risk improvements, and deploys only if verification passes.

No new automation code required.

### Phase 2: Semi-Automated Daily Reporter

Create a script that only observes and reports:

- git status;
- engine status;
- latest GSC pull;
- pipeline health;
- live status for priority URLs;
- lender JSON drift classification.

It must not edit or deploy.

Suggested output:

`/srv/BusinessOps/CreditDoc Project Improvement/Daily_Autonomous_Growth_Ops/YYYY-MM-DD/daily_health.md`

### Phase 3: Assisted Workpack Generator

Create a script that builds the daily SEO workpack from real data:

- latest GSC page/query rows;
- DB page status;
- live status checks;
- existing title/meta;
- recommended safe action.

It should produce CSV/Markdown only. Codex still chooses and executes.

### Phase 4: Controlled Auto-Fixes

Only after two weeks of stable daily reports:

- allow automatic metadata updates for `ready_for_index` pages only;
- allow automatic internal-link suggestions to be staged as patches;
- require build and live checks;
- require no dirty generated JSON.

### Phase 5: Limited Auto-Deploy

Only after Phase 4 is stable:

- auto-deploy guard-only/template-only fixes;
- never auto-deploy database indexability flips;
- never auto-deploy large profile rewrites;
- never auto-deploy if any touched page fails live checks.

## Stop Conditions

Daily process must stop and report if:

- live homepage returns non-200;
- sitemap/robots conflict appears;
- git has unexplained dirty files;
- lender JSON drift is content-bearing;
- `creditdoc-engine.service` is active;
- build fails;
- deploy fails;
- any touched URL is 404/500 after deploy;
- GSC/database query returns inconsistent or missing data;
- automation starts spending AI/model tokens unexpectedly.

## First-Day Activation Checklist

1. Create `Daily_Autonomous_Growth_Ops` folder.
2. Run preflight safety gate.
3. Restore/archive any generated JSON drift if metadata-only.
4. Pull latest GSC workpack.
5. Select first daily queue of 5-15 URLs.
6. Execute only 3-5 low-risk improvements.
7. Build.
8. Deploy only if necessary.
9. Live-check touched URLs.
10. Save report and next-day queue.

## Success Metrics

Short term:

- zero unexplained dirty repo state;
- zero broken touched pages;
- daily automations running or clearly reported when paused;
- GSC surfaced pages triaged within 24 hours;
- no invented claims or unsupported ratings.

Medium term:

- CTR improvement on review/city/answer pages;
- more answer/city/question pages appearing in GSC;
- fewer weak pages indexed;
- stronger internal paths into tools, course, financial wellness, best/compare pages.

Business outcome:

- organic traffic grows into qualified finance intent;
- CreditDoc becomes ready for credit repair, loan, card, and embedded-finance lead-routing tests once traffic and compliance gates are met.
