# CreditDoc Data Quality Remediation — v2 (Authored by Opus 4.7)

> **For Claude 4.6:** Execute this plan task-by-task. Commit after each completed task. Do not batch. Use superpowers:executing-plans.

**Authored:** 2026-04-19 by Opus 4.7 (1M context)
**Supersedes:** `2026-04-19-data-quality-remediation.md` (v1, authored by 4.6)
**Reason for v2:** v1 covered the 5 issue classes from Jammi's external mobile audit. v2 adds **15 additional issues** discovered during a live 60-URL random-sample audit by 4.7. All 15 are template- or config-level (same risk class as v1's P0 work) and several are higher-severity than v1's findings.

**Goal:** Eliminate data-quality, schema-compliance, and SEO defects across 15,516 indexed review pages + 16,666 total pages, with prevention gates to block regression.

**Architecture:** Phased remediation. Phase 0 is template/config-only (safe, one deploy, no data touch). Phases 1-2 touch data (require approval per CLAUDE.md Rule 4). Phase 3-4 build prevention + monitoring infrastructure.

**Tech Stack:** Astro static (soon hybrid per architecture-overhaul plan), SQLite source-of-truth, Python enrichment/build scripts, Vercel hosting, JSON-LD schema.org.

---

## Scope Delta vs v1 (what 4.6 missed)

v1 phase breakdown was solid for the 5 external-audit issues. v2 adds, in order of severity:

| # | Issue | Severity | Why v1 missed it |
|---|---|---|---|
| N1 | Hardcoded `aggregateRating` with `Harvey Brooks` as sole author on 100% of reviews — violates Google Rich Results policy + FTC UDAAP | **CRITICAL** | External audit didn't inspect JSON-LD |
| N2 | 100% of canonicals point to apex `creditdoc.co` but apex is a 307 (temp, not 301) redirect to `www.` — canonical = redirect source | **CRITICAL** | External audit worked off rendered content only |
| N3 | Empty placeholders embedded in FAQPage JSON-LD (not just body copy) — Google ingests as structured data | **CRITICAL** | v1 treated Issue 2 as body-only |
| N4 | 5 hub pages are 404: `/categories/credit-unions/`, `/banks/`, `/debt-settlement/`, `/atms-cash-access/`, `/answers/` | **CRITICAL** | Not tested |
| N5 | Custom 404 returns empty response (size=0, no title, no nav) | **HIGH** | Not tested |
| H1 | All 16K+ pages share `og-default.png` — zero social-preview differentiation | **HIGH** | Not tested |
| H2 | Security headers missing: `x-content-type-options`, `x-frame-options`, CSP, `referrer-policy`, `permissions-policy` | **HIGH** | HTTP header audit not performed |
| H3 | Brand "logos" are 16x16 DuckDuckGo favicons — external dep + CLS risk + not authoritative | **HIGH** | Image audit not performed |
| H4 | Uncle Dan's Pawn Shop has 9 near-duplicate review pages (Dallas-area branches) — duplicate brand risk across chains | MEDIUM | Brand-chain deduplication not evaluated |
| H5 | `Niagara&#39;S Choice`, `&amp;` in H1s on state pages — HTML entity escape leaks | MEDIUM | Sample too small to catch |
| M1 | `/best/best-X/` redundant URL pattern across all 26 /best/ pages | LOW | URL ergonomics not evaluated |
| M2 | `/methodology/` describes 5-factor system but never discloses where scores come from (human vs LLM vs algorithmic) | MEDIUM | Methodology integrity not evaluated |
| M3 | `cache-control: max-age=0, must-revalidate` on every page — no browser cache | LOW | HTTP header audit not performed |
| M4 | Homepage shows `age: 70060s` (19.5 hrs stale) — ISR/revalidation not firing | MEDIUM | Cache behavior not evaluated |
| QUANT | Placeholder leaks that v1 treated as rare are directory-wide: Free Consultation 100%, Free to Use 85%, BBB: NR 78% of 60-URL sample | **CRITICAL** | Sample size too small to estimate prevalence |

---

## Phase 0 — Emergency Template & Config Fixes (Day 1, single deploy)

**Scope contract:** No data writes. No DB migrations. Template + config only. All 7 tasks land in one commit batch, one Vercel deploy. Rollback = revert the commit.

**Why bundled:** Each fix is <30 lines, independently verifiable, zero data risk, and deploying them together minimizes the number of stale-cache regressions.

### Task 0.1 — Flip canonical host to www

**Files:**
- Modify: `astro.config.mjs`

**Change:**
```js
// Before
site: 'https://creditdoc.co',
// After
site: 'https://www.creditdoc.co',
```

**Verify (after deploy):**
```bash
curl -sL https://www.creditdoc.co/review/shell/ | grep -oP 'rel="canonical"[^>]+' | head -1
# Expected: rel="canonical" href="https://www.creditdoc.co/review/shell/"
```

**Acceptance:** 100/100 sampled pages return `canonical → www.creditdoc.co/...`. Zero pages canonical-to-apex.

**Commit:** `fix(seo): canonical to www host, not apex`

---

### Task 0.2 — Apex redirect 307→301 + security headers

**Files:**
- Modify: `vercel.json`

**Change:** Add `headers` block + explicit apex redirect (Vercel defaults to 307 for host redirects; must be declared explicitly to make it 301).

```json
{
  "redirects": [
    {"source": "/:path*", "has": [{"type": "host", "value": "creditdoc.co"}], "destination": "https://www.creditdoc.co/:path*", "permanent": true},
    ...existing redirects...
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {"key": "X-Content-Type-Options", "value": "nosniff"},
        {"key": "X-Frame-Options", "value": "SAMEORIGIN"},
        {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
        {"key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()"}
      ]
    }
  ]
}
```

**Verify:**
```bash
curl -sI https://creditdoc.co/ | grep -E '^(HTTP|location):'
# Expected: HTTP/2 301  /  location: https://www.creditdoc.co/
curl -sI https://www.creditdoc.co/ | grep -iE '(x-content-type|x-frame|referrer-policy|permissions)'
# Expected: all four headers present
```

**Acceptance:** Apex redirect is 301, all 4 security headers present on every response.

**Commit:** `fix(infra): apex→www 301, add security headers`

---

### Task 0.3 — Suppress empty FAQ template fields + body placeholders

**Files:**
- Modify: `src/pages/review/[slug].astro:155-175` (FAQ generation)
- Modify: `src/components/TrustBadge.astro` (if it renders BBB: NR)
- Grep first: `grep -rn "headquartered in\|They hold a\|hold a " src/`

**Change (FAQ generation):**
```js
// BEFORE (line ~159):
const faqs = [
  {
    question: `Is ${lender.name} legitimate?`,
    answer: `Yes. ${lender.name} is a registered company headquartered in ${lender.company_info.headquarters}${...}. They hold a ${lender.company_info.bbb_rating} rating with the Better Business Bureau${...}.`,
  },
  ...
];

// AFTER:
const hq = lender.company_info?.headquarters?.trim();
const year = lender.company_info?.founded_year;
const bbb = lender.company_info?.bbb_rating?.trim();
const bbbAcc = lender.company_info?.bbb_accredited;

const legitParts = [`Yes. ${lender.name} is a registered company`];
if (hq) legitParts.push(`headquartered in ${hq}`);
if (year) legitParts.push(`founded in ${year}`);
let legitAnswer = legitParts.join(', ') + '.';
if (bbb && bbb !== 'NR' && bbb !== 'N/A') {
  legitAnswer += ` They hold a ${bbb} rating with the Better Business Bureau${bbbAcc ? ' and are BBB-accredited' : ''}.`;
}

const faqs = [
  { question: `Is ${lender.name} legitimate?`, answer: legitAnswer },
  ...
].filter(faq => faq.answer && !/ in , |hold a  /.test(faq.answer));
```

**Apply same pattern anywhere body copy shows these fields.** Grep the codebase for every use of `headquarters`, `bbb_rating`, `founded_year` without nullish checks.

**Verify:**
```bash
npm run build 2>&1 | tail -5
# Then sample:
for slug in shell abnb niagaras-choice legacy-community chevron; do
  grep -c 'headquartered in , \|hold a  rating\|>BBB:\s*NR' dist/review/$slug/index.html
done
# Expected: 0 for all
```

**Acceptance:** 0 occurrences of `headquartered in , `, `hold a  rating`, `BBB: NR` (as a badge), or `founded in ,` in any rendered HTML across a 60-page random sample.

**Commit:** `fix(template): suppress empty company_info placeholders in FAQ + body`

---

### Task 0.4 — Entity-type-aware trust badges

**Files:**
- Modify: `src/components/TrustBadge.astro` (or wherever "Free Consultation" / "Free to Use" render — grep first)
- Modify: `src/utils/data.ts` — add `ENTITY_TYPE_BADGE_MATRIX`

**Grep first:**
```bash
grep -rn "Free Consultation\|Free to Use" src/
```

**Change:** Drive badge rendering from an entity-type matrix, not blanket rendering:
```ts
// src/utils/data.ts — new export
export const ENTITY_TYPE_BADGE_MATRIX: Record<string, {freeConsult: boolean; freeToUse: boolean}> = {
  'credit-repair':       {freeConsult: true,  freeToUse: false},
  'debt-relief':         {freeConsult: true,  freeToUse: false},
  'debt-settlement':     {freeConsult: true,  freeToUse: false},
  'credit-counseling':   {freeConsult: true,  freeToUse: false},
  'personal-loans':      {freeConsult: false, freeToUse: false},
  'business-loans':      {freeConsult: false, freeToUse: false},
  'credit-cards':        {freeConsult: false, freeToUse: false},
  'banks':               {freeConsult: false, freeToUse: false},
  'credit-unions':       {freeConsult: false, freeToUse: false},
  'pawn-shops':          {freeConsult: false, freeToUse: false},
  'check-cashing':       {freeConsult: false, freeToUse: false},
  'atms':                {freeConsult: false, freeToUse: false},
  'payday-alternatives': {freeConsult: false, freeToUse: false},
  'insurance':           {freeConsult: true,  freeToUse: false},
  'credit-monitoring':   {freeConsult: false, freeToUse: true},
  'identity-theft':      {freeConsult: false, freeToUse: true},
};

export function getBadges(category: string) {
  return ENTITY_TYPE_BADGE_MATRIX[category] || {freeConsult: false, freeToUse: false};
}
```

**Change in template:** Wrap badge render in `{getBadges(lender.category).freeConsult && <Badge ...>}`.

**Verify:**
```bash
# Check pawn/check/ATM pages DO NOT have Free Consultation
for slug in crystal-pawn-shop dollar-smart-check-cashing; do
  grep -c 'Free Consultation' dist/review/$slug/index.html
done
# Expected: 0

# Check credit-repair pages DO still have it
for slug in credit-saint lexington-law; do
  grep -c 'Free Consultation' dist/review/$slug/index.html
done
# Expected: ≥1
```

**Acceptance:** 60-page random sample shows badges only on matching entity types. Zero pawn/check-cashing/ATM pages with "Free Consultation". Zero fee-charging pages with "Free to Use".

**Commit:** `fix(template): badge matrix by entity type`

---

### Task 0.5 — Rating attribution: CreditDoc as organization, not Harvey as reviewer

**Files:**
- Modify: `src/pages/review/[slug].astro` (around line 220-260, the aggregateRating + review block)

**Problem:** Template currently emits schema saying "Harvey Brooks wrote one customer review with rating X" on every one of 15K+ pages. That's not what's happening. The rating is an **algorithmic CreditDoc score** derived from the 5-factor methodology. Labelling it as a single-person customer review is (a) dishonest in schema.org semantics, (b) against Google Rich Results policy, and (c) misrepresents what the score actually is. No lender ratings change in value. We're only fixing the *label* Google sees.

**Design decision (approved by Jammi 2026-04-19):**
- The rating value stays exactly as it is (no score changes to any lender)
- Schema.org output: a `Review` object with `author: {"@type": "Organization", "name": "CreditDoc"}` (NOT a Person)
- `reviewBody` points at `/methodology/` so the formula is discoverable
- Remove the `AggregateRating` block entirely — aggregation implies multiple customer reviews, which isn't what the score is
- No `reviewCount: 1` fallback, no Harvey Brooks in `review.author`

**Change:**
```js
// BEFORE (approx line 230):
financialService.aggregateRating = {
  '@type': 'AggregateRating',
  ratingValue: clampedRating.toFixed(1),
  bestRating: '5', worstRating: '1',
  reviewCount: ((lender.google_reviews_count || 0) > 0 ? lender.google_reviews_count.toString() : '1'),
};
// plus existing `review` sub-object with author: Harvey

// AFTER:
// No AggregateRating emission (we don't aggregate many reviews).
// Emit a single org-authored Review representing our algorithmic score.
if (lender.rating > 0 && lender.rating <= 5) {
  financialService.review = {
    '@type': 'Review',
    author: {
      '@type': 'Organization',
      'name': 'CreditDoc',
      'url': 'https://www.creditdoc.co/'
    },
    reviewRating: {
      '@type': 'Rating',
      ratingValue: clampedRating.toFixed(1),
      bestRating: '5',
      worstRating: '1'
    },
    reviewBody: `CreditDoc Rating derived from our 5-factor methodology. See https://www.creditdoc.co/methodology/ for scoring details.`,
    datePublished: lender.last_reviewed_at || lender.last_updated || new Date().toISOString().slice(0,10)
  };
}
// If we later add real external customer reviews (Google Places, BBB, Trustpilot),
// re-add AggregateRating at that point using their counts only.
// If we only have an editorial opinion, render the rating VISUALLY via <RatingStars />
// but do NOT emit schema.org review markup.
```

**Same for the `review` sub-object** — remove `review: {author: Harvey, reviewBody: ...}` from emitted schema unless there's a verified external review object. Our editorial position can still appear in page body copy; it just cannot be schema'd as a customer review.

**Verify:**
```bash
# Sample 20 review pages — expected: aggregateRating present ONLY if externalReviewCount > 0
python3 scripts/audit_rating_schema.py --sample 60
# Expected: zero pages with reviewCount: "1" and author: Harvey Brooks
```

**Acceptance:** Schema `aggregateRating` only emits when external review count > 0. Zero pages emit a schema.org Review with Harvey Brooks as author.

**Commit:** `fix(schema): remove self-authored aggregateRating, require external reviews`

---

### Task 0.6 — Per-entity OG image fallback

**Files:**
- Modify: `src/layouts/BaseLayout.astro:19` (`ogImg` computation)
- Modify: `src/pages/review/[slug].astro` to pass `ogImage={...}`
- Create: `public/og-templates/review-default.svg` (per-category fallback)

**Change:** Reviews should pass a logo URL (or a per-category OG). BaseLayout keeps the generic fallback only as last resort.

```astro
<!-- src/pages/review/[slug].astro — BaseLayout call -->
<BaseLayout
  title={...}
  description={...}
  canonical={...}
  ogImage={lender.logo_url || `https://www.creditdoc.co/og-templates/${lender.category}.svg` || 'https://www.creditdoc.co/og-default.png'}
  jsonLd={...}
>
```

**Per-category OG templates** (Phase 0 ships with 4 placeholder SVGs for top categories; rest fall through to og-default): credit-repair, credit-cards, personal-loans, business-loans. Generate via existing `tools/image_generator.py` or hand-author SVGs.

**Verify:**
```bash
# Expect ≥1 unique og:image per entity type across 60 pages
python3 -c "
import urllib.request, re
from collections import Counter
ogs = []
for slug in 'shell abnb chevron crystal-pawn-shop credit-saint lexington-law'.split():
    h = urllib.request.urlopen(f'https://www.creditdoc.co/review/{slug}/').read().decode()
    m = re.search(r'og:image[^>]+content=\"([^\"]+)\"', h)
    if m: ogs.append(m.group(1))
print('unique og:images:', len(set(ogs)), 'of', len(ogs))
"
# Expected: unique count > 1
```

**Acceptance:** At least 2 distinct og:image URLs across a 6-slug sample from different categories.

**Commit:** `feat(social): per-entity OG image fallback`

---

### Task 0.7 — Harvey Brooks bio page + editorial attribution tier

**Files:**
- Create: `src/pages/about/harvey-brooks.astro`
- Create: `src/pages/about/editorial-standards.astro`
- Modify: `src/pages/review/[slug].astro` — conditional attribution

**Change:** FA-protected profiles get "Editorially reviewed by [Harvey Brooks](/about/harvey-brooks/)". Auto-generated profiles get "Data sourced from NCUA/FDIC/HUD, last updated {date}".

```astro
<!-- in review template -->
{lender.is_protected ? (
  <p class="text-sm text-muted">Editorially reviewed by <a href="/about/harvey-brooks/">Harvey Brooks</a> · Last updated {lender.last_reviewed_at}</p>
) : (
  <p class="text-sm text-muted">Data sourced from {lender.data_source_label || 'public regulatory filings'} · Last synced {lender.last_synced_at}</p>
)}
```

**Bio page contents** (Jammi to provide final copy — placeholder scaffold only):
- Harvey's credentials in consumer finance
- Photo + LinkedIn (if Jammi approves)
- Review process description
- Scope of review (which entity classes are editorially reviewed vs. data-sourced)
- Methodology link

**Acceptance:** `/about/harvey-brooks/` returns 200 with bio content. FA profiles link to it. Non-FA profiles show "Data sourced from..." tag, not Harvey's name.

**Commit:** `feat(eeat): Harvey Brooks bio + tiered attribution`

---

### Phase 0 Deployment Gate

**Before pushing:**
1. Run `npm run build` — must complete without errors
2. Run `python3 tools/validate_build_data.py` — must pass
3. Manual sample: `dist/review/shell/index.html` — inspect canonical, og:image, FAQ, schema, attribution
4. Jammi approval required on screenshots

**After Vercel deploy:**
1. Run live audit: `python3 scripts/live_quality_audit.py --sample 60` (script built in Phase 3, see Task 3.1 — for Phase 0, run ad-hoc checks from "Verify" sections above)
2. Confirm all 7 acceptance criteria in a single Telegram summary to Jammi

---

## Phase 1 — Dead Hubs, 404 Page, Finance Relevance Classifier (Day 2-3)

### Task 1.1 — Build 5 dead hub pages

**Files:**
- Create: `src/pages/categories/credit-unions.astro`
- Create: `src/pages/categories/banks.astro`
- Create: `src/pages/categories/debt-settlement.astro`
- Create: `src/pages/categories/atms-cash-access.astro`
- Create: `src/pages/answers/index.astro`

**Pattern:** Copy existing `src/pages/categories/credit-repair.astro` structure. Query DB for matching entity types. Link to top /best/ pages. Include category-specific FAQ and 2-3 paragraphs of hub copy.

**DB queries per hub:**
| Hub | Query |
|---|---|
| credit-unions | `WHERE json_extract(data,'$.entity_type')='credit-union' OR category IN ('credit-unions','banks-credit-unions')` |
| banks | `WHERE json_extract(data,'$.entity_type')='bank' AND no_index=0` |
| debt-settlement | `WHERE category='debt-settlement'` |
| atms-cash-access | `WHERE category IN ('atms','cash-access')` |
| /answers/ | `SELECT * FROM cluster_answers WHERE status='published' ORDER BY published_at DESC` |

**Acceptance:** Each of the 5 URLs returns 200, has title/H1/canonical/meta-description, includes ≥20 entity cards (or answer cards) from DB, has internal links to ≥3 money pages.

**Commits:** One commit per hub page.

---

### Task 1.2 — Custom 404 page

**Files:**
- Rewrite: `src/pages/404.astro`

**Contract:** Branded 404 with search bar, category grid, top 5 /best/ links, contact link.

**Verify:**
```bash
curl -s https://www.creditdoc.co/nonexistent-xyz/ | wc -c
# Expected: ≥5000 bytes (current is 0)
```

**Acceptance:** 404 page returns HTML >5KB, has navigation, search, and CTAs.

**Commit:** `feat(404): branded 404 with search and category nav`

---

### Task 1.3 — Finance-relevance classifier + sweep

**Files:**
- Create: `tools/finance_relevance_classifier.py`
- Modify: `tools/creditdoc_autonomous_engine.py` — wire gate before publish
- Create: Report CSV for review (NEVER auto-delete — per CLAUDE.md Rule 4)

**Contract:**
- Reads every `processing_status='ready_for_index'` row
- Calls Claude Haiku (cheap) with prompt: "Is {name}, described as '{description_short}', a US financial-services provider? Answer YES or NO with one sentence."
- Caches result in `data/finance_relevance_cache.json` keyed by slug
- Outputs CSV: `reports/finance_relevance_flagged_YYYY-MM-DD.csv` with columns: slug, current_category, classifier_verdict, reason, suggested_action (noindex / reclassify / remove)
- **DOES NOT WRITE TO DB.** Only outputs CSV. Jammi reviews, approves, then runs the apply step.

**Apply step** (separate command, requires explicit flag):
```bash
python3 tools/finance_relevance_classifier.py --apply reports/finance_relevance_flagged_2026-04-19.csv --min-confidence 0.9
# Sets no_index=1 in DB for all rows approved in CSV
```

**Acceptance:** CSV produced for Jammi review. Zero auto-deletes. Zero auto-noindexes without explicit `--apply` step.

**Commit:** `feat(quality): finance-relevance classifier (detect-only)`

---

### Task 1.4 — Slug-collision detector

**Files:**
- Create: `tools/slug_collision_detector.py`

**Contract:**
- For every pair of slugs (s1, s2), compute fuzzy name similarity
- Flag any pair where: name_similarity(s1.name, s2.name) > 0.80 AND slug_similarity(s1.slug, s2.slug) < 0.60
- Also flag: any slug that is a prefix of another slug (e.g., `money-line` prefix of `money-line-san-diego`)
- Output: `reports/slug_collisions_YYYY-MM-DD.csv`

**Why broader than v1's 114 number:** v1 probably used categorical filters. Fuzzy similarity will surface the `Money Line` vs `Money One FCU` class, which is the actual root cause.

**Acceptance:** Report CSV delivered. Zero auto-actions.

**Commit:** `feat(quality): slug collision detector (detect-only)`

---

## Phase 2 — Data Fixes (Day 3-7, requires approval per fix batch)

### Task 2.1 — Quarantine mismatched-body review pages
**Source:** Task 1.4 output (approved subset).
**Action:** For each approved row: set `processing_status='quarantine_mismatch'`, `no_index=1`, wipe `description_long` to force re-enrichment.
**Scale:** Unknown until 1.4 runs. Estimate 50-300.
**Commit per batch of ≤50.**

### Task 2.2 — Backfill empty city/state
**Source:** DB rows where `company_info.headquarters IS NULL OR =''`. Prior work (`cu_ncua_resolver.py`) handles CUs. Extend to banks via FDIC API, to pawn/check-cashing via Google Places.
**Action:** Update DB only. Template Phase 0 fix already suppresses empty-field text, so this is cosmetic recovery, not urgent.

### Task 2.3 — Chain-brand deduplication decision
**Source:** Task 1.4 output + DB query for brands with ≥3 locations.
**Action:** For each chain, Jammi decides: (a) one hero review + N location stubs linking to it, or (b) keep all, ensure differentiated content.
**Scale:** ~50 chain brands estimated (Uncle Dan's is one example).

### Task 2.4 — Entity-type backfill
**Source:** Current DB rows where `category` is set but `entity_type` is null.
**Action:** Derive entity_type from category + keyword scan of description. Apply in bulk after Jammi spot-checks a sample.
**Scale:** ~2,693 (per v1 estimate — verify).

---

## Phase 3 — Prevention Gate Infrastructure (Day 8-10)

### Task 3.1 — `pre_publish_gate.py` (expanded from v1)

**File:** `tools/pre_publish_gate.py`

**Checks (all must pass for a row to move to published):**

1. **Fuzzy match:** entity name in body matches entity name in slug (Jaro-Winkler >0.85)
2. **No empty placeholders:** body HTML has no `headquartered in , ,`, `hold a  rating`, `founded in ,`, `>BBB:\s*NR<`, `>BBB:\s*</`
3. **Entity type set:** `entity_type` field populated AND in allowed taxonomy
4. **Finance relevance:** Task 1.3 classifier = YES
5. **Required schema fields populated:** address (city+state at minimum) OR address clause suppressed in template
6. **Author-tier consistent:** if `is_protected=1`, attribution = Harvey Brooks; else = data-sourced
7. **Canonical → www:** generated canonical URL starts with `https://www.creditdoc.co/`
8. **OG image not default:** OG image URL != `og-default.png` OR entity is in a known-low-value category (wellness glossary etc.)
9. **aggregateRating sanity:** if schema emits aggregateRating, external review count > 0
10. **FAQ JSON-LD clean:** no empty placeholder strings inside any `Answer.text`
11. **Noindex coherence:** if `no_index=1` in DB, response `<meta robots>` includes noindex
12. **Logo present or suppressed:** if logo is DDG favicon, ensure `width`/`height` attrs present and `loading=lazy`

**Input:** slug → fetches rendered HTML from `dist/` (post-build)
**Output:** Pass/Fail per check + aggregated verdict
**Exit codes:** 0=pass, 1=fail (block publish)

**Wire into:** `creditdoc_build.py` runs this BEFORE `git_commit_changes()`. If any row fails, exclude from export and alert.

### Task 3.2 — `rendered_html_scanner.py`

**File:** `tools/rendered_html_scanner.py`

**Contract:** Scans built HTML in `dist/**/*.html` for 20 known regex patterns (the ones in check #2 above, plus new ones as discovered). Outputs count per pattern per URL.

**Use modes:**
- Pre-push: runs against changed files only, blocks if any fail
- Nightly: runs against all files, emails report

### Task 3.3 — Wire gates into enrichment engine

**Files:**
- Modify: `tools/creditdoc_autonomous_engine.py` — require `pre_publish_gate.py` pass before `processing_status='ready_for_index'`
- Modify: `tools/creditdoc_build.py` — add `--gate-check` step before commit

---

## Phase 4 — Re-enrichment & Daily Monitoring (Day 10-21)

### Task 4.1 — Re-enrich quarantined rows
Cron already runs at 14:00 UTC (`creditdoc_autonomous_engine.py`). Phase 2 rows feed into this queue naturally. Monitor: 100/day throughput.

### Task 4.2 — Daily mismatch + placeholder scanner
Add cron at 15:00 UTC: runs Task 1.4 (slug collision) + Task 3.2 (HTML scanner) against production. Alerts to Telegram if new issues detected post-launch.

### Task 4.3 — Weekly external regression audit
See separate doc: `CreditDoc Project Improvement/2026-04-19-monitoring-architecture.md`.

---

## Sequencing & Dependencies

```
Phase 0 (Day 1)    ─► single deploy, all 7 tasks
 │
Phase 1 (Day 2-3)  ─► 1.1 hubs (parallel with 1.2 404) ─► 1.3 classifier ─► 1.4 detector
 │
Phase 2 (Day 3-7)  ─► 2.1 quarantine (needs 1.4) ─► 2.2 backfill (parallel) ─► 2.3 dedupe (needs 1.4)
 │                                                 ─► 2.4 entity-type backfill (parallel)
Phase 3 (Day 8-10) ─► 3.1 gate (needs Phase 0,1 data structures) ─► 3.2 scanner ─► 3.3 wire-in
 │
Phase 4 (Day 10-21)─► 4.1 re-enrich (continuous) + 4.2 daily cron + 4.3 weekly external audit
```

---

## Rollback

- **Phase 0**: git revert, redeploy. Cache TTL resolves in <1 hour.
- **Phase 1**: new pages are additive — delete to remove. Classifier is detect-only, no data change.
- **Phase 2**: DB audit log (from `creditdoc_db.py`) captures every change; revert by querying `audit_log` for that batch's rows and restoring prior `data` JSON.
- **Phase 3**: gates are in-band — removing the `--gate-check` flag from build script restores prior behavior.

---

## Success Metrics (check at Day 21)

| Metric | Baseline (Apr 19) | Target (May 10) |
|---|---|---|
| Placeholder leaks (`headquartered in , ,`) | 20% of reviews | <1% |
| `BBB: NR` as trust badge | 78% | 0% |
| `Free Consultation` on non-consulting entities | 100% of pawn/check/ATM | 0% |
| Self-authored aggregateRating schema | 100% of reviews | 0% |
| Canonicals pointing to apex | 100% | 0% |
| Hub category 404s | 5 | 0 |
| Per-entity OG images (distinct across 60 pages) | 1 | ≥6 (by category) |
| Vercel deploy time | 372s | <60s (with Phase 0 fixes + architecture overhaul) |
| Non-financial entities in index | Unknown; v1 est. 114 | 0 (all quarantined) |
| GSC "Unparsable structured data" errors | Unknown — baseline Day 1 | Trending down |

---

## Out of Scope (for this plan — separate planning required)

- Architecture overhaul (Astro static → hybrid+ISR) — plan already exists at `2026-04-18-architecture-overhaul.md`
- Real customer review collection (to make aggregateRating genuinely multi-source)
- DDG-favicon → hosted logo migration (captured in memory, needs separate planning — likely scraping each lender's site for a logo, hosting on our CDN)
- Methodology page expansion with transparency on score computation
