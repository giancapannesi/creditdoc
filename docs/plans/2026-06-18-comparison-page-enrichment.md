# Comparison Page Enrichment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn CreditDoc comparison pages into richer decision pages that preserve sourced provider facts, add category-aware decision support, and route users to relevant CreditDoc tools, guides, courses, blogs, answers, resources, local pages, and regulatory context.

**Architecture:** Add reusable comparison enrichment helpers and template sections to `src/pages/compare/[slug].astro`, keeping provider reviews as the deep-detail pages. The comparison page will derive decision cards and resource links from existing lender/category fields and static route maps, with no direct lender JSON edits and no bulk content rewrites.

**Tech Stack:** Astro SSR/static build, TypeScript in Astro frontmatter, existing `Lender` data shape from `src/utils/data`, existing internal routes under `/tools/`, `/answers/`, `/resources/`, `/courses/`, `/blog/`, `/categories/`, `/city/`, and `/research/`.

---

## Constraints

- Do not bulk rewrite comparison records.
- Do not remove sourced value from existing pages.
- Do not edit `src/content/lenders/*.json` as live source of truth.
- Do not fabricate prices, savings, ratings, guarantees, or recommendation claims.
- Use category-aware internal links only where the routes exist.
- Keep cards compact and useful on mobile.
- Preserve build performance and avoid client-side dependencies.

## Task 1: Add Category-Aware Resource Link Model

**Files:**
- Modify: `src/pages/compare/[slug].astro`

**Step 1: Add route-map helpers in the frontmatter**

Add a typed helper near the existing `categoryLabels` block:

```ts
type ComparisonResourceLink = {
  label: string;
  href: string;
  detail: string;
  group: 'tool' | 'guide' | 'course' | 'resource' | 'local' | 'data';
};

const sharedComparisonLinks: ComparisonResourceLink[] = [
  { label: 'Credit fundamentals course', href: '/courses/credit-fundamentals/', detail: 'Review core credit concepts before comparing paid services.', group: 'course' },
  { label: 'Local credit guides', href: '/city/', detail: 'Compare local providers, state context, and city-level credit resources.', group: 'local' },
  { label: 'Complaint data context', href: '/research/consumer-complaints/', detail: 'Use public complaint context as one research signal.', group: 'data' },
];

const categoryResourceLinks: Record<string, ComparisonResourceLink[]> = {
  'credit-repair': [
    { label: 'Credit repair qualify quiz', href: '/tools/credit-repair-qualify-quiz/', detail: 'Check whether dispute help, DIY review, or credit building may fit.', group: 'tool' },
    { label: 'Credit score simulator', href: '/tools/credit-score-simulator/', detail: 'Model common score-pressure scenarios before paying for help.', group: 'tool' },
    { label: 'Credit report checklist', href: '/resources/credit-report-checklist/', detail: 'Review report sections before hiring a repair company.', group: 'resource' },
    { label: 'Charge-off guide', href: '/answers/how-to-remove-charge-offs/', detail: 'Understand charge-off research before comparing repair providers.', group: 'guide' },
    { label: 'Build credit faster', href: '/answers/how-to-build-credit-score-fast/', detail: 'Compare dispute work with credit-building actions.', group: 'guide' },
  ],
  'personal-loans': [
    { label: 'Borrowing power quiz', href: '/tools/borrowing-power-quiz/', detail: 'Estimate broad borrowing capacity before comparing lenders.', group: 'tool' },
    { label: 'Loan denial checker', href: '/tools/loan-denial-reason-checker/', detail: 'Map denial reasons to next research steps.', group: 'tool' },
    { label: 'APR guide', href: '/answers/personal-loan-interest-rates-explained/', detail: 'Understand interest-rate and APR terms before applying.', group: 'guide' },
  ],
  'emergency-cash': [
    { label: 'Borrowing power quiz', href: '/tools/borrowing-power-quiz/', detail: 'Check broad repayment fit before using high-cost cash products.', group: 'tool' },
    { label: 'Credit denial checklist', href: '/tools/credit-denial-action-checklist/', detail: 'Review safer next steps after a credit denial.', group: 'tool' },
    { label: 'State regulator directory', href: '/tools/state-consumer-credit-regulator-directory/', detail: 'Find state lending-law starting points and official resources.', group: 'data' },
  ],
  'debt-relief': [
    { label: 'Debt payoff calculator', href: '/tools/debt-payoff-calculator/', detail: 'Compare payoff paths before contacting debt-relief providers.', group: 'tool' },
    { label: 'Debt letter templates', href: '/resources/debt-credit-letter-templates/', detail: 'Use templates and checklists for debt validation and settlement research.', group: 'resource' },
    { label: 'DIY debt consolidation', href: '/answers/can-i-do-debt-consolidation-myself/', detail: 'Compare provider help with self-managed options.', group: 'guide' },
  ],
  'business-loans': [
    { label: 'Business readiness quiz', href: '/tools/business-loan-readiness-quiz/', detail: 'Check documents, revenue, business age, and route fit.', group: 'tool' },
    { label: 'Cash-flow calculator', href: '/tools/bank-statement-cash-flow-calculator/', detail: 'Estimate cash-flow pressure before comparing funding products.', group: 'tool' },
    { label: 'MCA repayment calculator', href: '/tools/mca-repayment-calculator/', detail: 'Compare payback amount and revenue share before accepting fast funding.', group: 'tool' },
  ],
  'build-credit': [
    { label: 'Credit score simulator', href: '/tools/credit-score-simulator/', detail: 'Model score-pressure scenarios before choosing credit-building products.', group: 'tool' },
    { label: 'Build credit with no history', href: '/answers/build-credit-with-no-credit-history/', detail: 'Compare product choices with basic credit-building steps.', group: 'guide' },
    { label: 'Secured card questions', href: '/answers/secured-credit-cards-questions-answered/', detail: 'Understand secured-card trade-offs before comparing products.', group: 'guide' },
  ],
  fintech: [
    { label: 'Credit score simulator', href: '/tools/credit-score-simulator/', detail: 'Model credit-building scenarios before choosing fintech tools.', group: 'tool' },
    { label: 'Credit fundamentals course', href: '/courses/credit-fundamentals/', detail: 'Review core credit concepts before comparing apps or subscriptions.', group: 'course' },
  ],
};
```

**Step 2: Add a de-duplicating selector**

```ts
function comparisonResourceLinks(categories: string[]): ComparisonResourceLink[] {
  const links = [
    ...categories.flatMap(category => categoryResourceLinks[category] || []),
    ...sharedComparisonLinks,
  ];
  const seen = new Set<string>();
  return links.filter(link => {
    if (seen.has(link.href)) return false;
    seen.add(link.href);
    return true;
  }).slice(0, 8);
}

const resourceLinks = comparisonResourceLinks(comparedCategories);
```

**Step 3: Verify route existence**

Run:

```bash
cd /srv/BusinessOps/creditdoc
for p in \
  src/pages/tools/credit-repair-qualify-quiz.astro \
  src/pages/tools/credit-score-simulator.astro \
  src/pages/resources/credit-report-checklist/index.astro \
  src/pages/courses/credit-fundamentals/index.astro \
  src/pages/answers/[slug].astro \
  src/pages/city/index.astro \
  src/pages/research/consumer-complaints.astro; do test -e "$p" && echo "OK $p" || echo "MISSING $p"; done
```

Expected: all listed direct files exist except answer slugs route through `src/pages/answers/[slug].astro`.

**Step 4: Commit**

```bash
git add src/pages/compare/[slug].astro
git commit -m "feat: add comparison resource link model"
```

## Task 2: Add Quick Decision Map

**Files:**
- Modify: `src/pages/compare/[slug].astro`

**Step 1: Add fit-signal helpers**

Use existing fields only:

```ts
function topServiceSignals(lender: Lender): string[] {
  return [
    ...(lender.services || []),
    ...(lender.pros || []),
  ]
    .filter(Boolean)
    .slice(0, 4)
    .map(item => softenComparisonText(String(item)).replace(/[.\s]+$/g, ''));
}

function decisionMapLine(lender: Lender): string {
  const signals = topServiceSignals(lender);
  if (signals.length === 0) {
    return `Compare ${lender.name} if its full profile, listed category, and current provider terms match your research need.`;
  }
  return `Compare ${lender.name} if these stored profile signals match your need: ${signals.slice(0, 3).join('; ')}.`;
}
```

**Step 2: Add section after Summary**

Add a full-width section titled `Quick Decision Map` with two equal cards:

```astro
<section class="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
  <h2 class="text-lg font-bold text-text mb-4">Quick Decision Map</h2>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    {[lenderA, lenderB].map((lender) => (
      <div class="rounded-lg border border-border bg-bg-alt p-4">
        <h3 class="text-sm font-semibold text-text">Compare {lender.name} if...</h3>
        <p class="mt-2 text-sm text-muted leading-relaxed">{decisionMapLine(lender)}</p>
        <a href={`/review/${lender.slug}/`} class="mt-3 inline-flex text-sm font-medium text-primary hover:underline">
          Read the full {lender.name} review
        </a>
      </div>
    ))}
  </div>
</section>
```

**Step 3: Run build**

Run:

```bash
npm run build
```

Expected: build completes with existing robots/sitemap checks passing.

**Step 4: Commit**

```bash
git add src/pages/compare/[slug].astro
git commit -m "feat: add comparison decision map"
```

## Task 3: Add CreditDoc Tools And Guides Section

**Files:**
- Modify: `src/pages/compare/[slug].astro`

**Step 1: Add section before FAQ**

```astro
{resourceLinks.length > 0 && (
  <section class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
    <div class="glass-card p-5">
      <h2 class="text-lg font-bold text-text mb-2">CreditDoc Tools and Guides for This Comparison</h2>
      <p class="text-sm text-muted leading-relaxed">
        If you need a calculator, checklist, course, or deeper guide before contacting either company, start with these CreditDoc resources.
      </p>
      <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {resourceLinks.map(link => (
          <a href={link.href} class="rounded-lg border border-border bg-bg-alt p-3 hover:border-primary transition-colors">
            <span class="text-xs font-semibold uppercase text-muted">{link.group}</span>
            <span class="mt-1 block text-sm font-semibold text-primary">{link.label}</span>
            <span class="mt-1 block text-xs text-muted leading-relaxed">{link.detail}</span>
          </a>
        ))}
      </div>
    </div>
  </section>
)}
```

**Step 2: Check pilot rendered output**

Run:

```bash
npm run build
test -f dist/compare/ecreditadvisor-vs-the-credit-repairmen/index.html
rg "CreditDoc Tools and Guides for This Comparison|Credit repair qualify quiz|Credit fundamentals course" dist/compare/ecreditadvisor-vs-the-credit-repairmen/index.html
```

Expected: the rendered pilot page includes the new section and credit-repair links.

**Step 3: Commit**

```bash
git add src/pages/compare/[slug].astro
git commit -m "feat: link tools and guides from comparisons"
```

## Task 4: Add Before-Contact Checklist

**Files:**
- Modify: `src/pages/compare/[slug].astro`

**Step 1: Add category-aware checklist helper**

```ts
function beforeContactChecklist(categories: string[]): string[] {
  const base = [
    'Verify current pricing, setup fees, and cancellation terms directly with the company.',
    'Read both full CreditDoc review pages before using external signup links.',
    'Check whether listed refund, return, or satisfaction terms have conditions.',
  ];
  if (categories.includes('credit-repair')) {
    return [
      ...base,
      'Ask which bureaus are included and how dispute updates are delivered.',
      'Confirm whether the service is dispute-focused, coaching-focused, mortgage-readiness focused, or credit-building focused.',
    ];
  }
  if (categories.includes('emergency-cash') || categories.includes('personal-loans')) {
    return [
      ...base,
      'Confirm APR, fees, repayment schedule, and state-specific availability before applying.',
      'Check whether prequalification uses a soft or hard credit inquiry.',
    ];
  }
  if (categories.includes('debt-relief')) {
    return [
      ...base,
      'Ask whether the program requires missed payments or dedicated-account deposits.',
      'Compare fee timing, tax risk, and credit-report impact before enrolling.',
    ];
  }
  return base;
}

const contactChecklist = beforeContactChecklist(comparedCategories);
```

**Step 2: Add section after What/How to Compare**

Add a compact checklist section:

```astro
<section class="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
  <div class="rounded-lg border border-border bg-bg-alt p-5">
    <h2 class="text-lg font-bold text-text mb-3">Before You Contact Either Company</h2>
    <ul class="grid grid-cols-1 md:grid-cols-2 gap-2">
      {contactChecklist.map(item => (
        <li class="text-sm text-muted leading-relaxed flex gap-2">
          <span class="mt-1 h-1.5 w-1.5 rounded-full bg-primary shrink-0"></span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  </div>
</section>
```

**Step 3: Run focused scan**

Run:

```bash
npm run build
node - <<'NODE'
const fs = require('fs');
const html = fs.readFileSync('dist/compare/ecreditadvisor-vs-the-credit-repairmen/index.html','utf8');
for (const text of ['Before You Contact Either Company','Ask which bureaus are included','CreditDoc Tools and Guides']) {
  if (!html.includes(text)) throw new Error(`missing ${text}`);
}
console.log('pilot enrichment present');
NODE
```

Expected: `pilot enrichment present`.

**Step 4: Commit**

```bash
git add src/pages/compare/[slug].astro
git commit -m "feat: add comparison verification checklist"
```

## Task 5: Clean And Enrich Pilot Copy

**Files:**
- Modify through DB/export path: `src/content/comparisons.json`

**Step 1: Inspect current pilot source**

Run:

```bash
cd /srv/BusinessOps/creditdoc
python3 - <<'PY'
import json
rows=json.load(open('src/content/comparisons.json'))
for row in rows:
    if row['slug']=='ecreditadvisor-vs-the-credit-repairmen':
        print(json.dumps(row, indent=2))
PY
```

Expected: current old winner/safety copy is visible.

**Step 2: Update only this comparison through `CreditDocDB.add_comparison`**

Use the existing DB helper. Preserve the row fields and set:

- summary: neutral decision copy preserving mortgage-readiness vs broader repair/tracking/rent-reporting differences.
- winner_reason: explain why the stored comparison note highlights eCreditAdvisor for mortgage-readiness, while The Credit Repairmen remains relevant for broader repair and feature context.
- seo_description: factual comparison description.

Do not edit lender JSON.

**Step 3: Export comparisons**

Run the same export helper used in Phase 1 slices:

```bash
cd /srv/BusinessOps/creditdoc
python3 - <<'PY'
from tools.creditdoc_db import CreditDocDB
db = CreditDocDB()
db.export_content_file('comparisons', 'comparisons.json')
PY
```

Expected: `src/content/comparisons.json` updates only the pilot record.

**Step 4: Verify copy safety**

Run:

```bash
node - <<'NODE'
const fs = require('fs');
const row = JSON.parse(fs.readFileSync('src/content/comparisons.json','utf8')).find(r => r.slug === 'ecreditadvisor-vs-the-credit-repairmen');
const text = [row.summary,row.winner_reason,row.seo_description].join('\\n');
const patterns = [/money-back guarantee/i,/\\bwins\\b/i,/superior value/i,/better value/i,/clear winner/i,/safer choice/i,/more reliable choice/i,/red flag/i,/significantly cheaper/i,/unconditional/i];
const hits = patterns.filter(re => re.test(text)).map(String);
if (hits.length) throw new Error(`unsafe hits: ${hits.join(', ')}`);
console.log('pilot copy scan OK');
NODE
```

Expected: `pilot copy scan OK`.

**Step 5: Build and render-check**

Run:

```bash
npm run build
rg "Quick Decision Map|CreditDoc Tools and Guides for This Comparison|Before You Contact Either Company" dist/compare/ecreditadvisor-vs-the-credit-repairmen/index.html
```

Expected: all three section headings are present.

**Step 6: Commit**

```bash
git add src/pages/compare/[slug].astro src/content/comparisons.json
git commit -m "feat: enrich pilot comparison page"
```

## Task 6: Update Workpack And Memory

**Files:**
- Modify: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Pricing_Safety_Phase_1_2026-06-17/PHASE_1_COMPARISON_PRICING_WORKPACK.md`
- Modify: `CREDITDOC_NOW.md`
- Modify: `CREDITDOC_NEXT.md`
- Add memory file outside repo as needed.

**Step 1: Document direction shift**

Record that Phase 1 has changed from cleanup-only to cleanup-plus-enrichment.

**Step 2: Build final verification**

Run:

```bash
npm run build
git diff --check
git status --short --untracked-files=all
```

Expected: build passes, no whitespace errors, only expected docs or final files are dirty before commit.

**Step 3: Commit repo docs**

```bash
git add CREDITDOC_NOW.md CREDITDOC_NEXT.md docs/plans/2026-06-18-comparison-page-enrichment-design.md docs/plans/2026-06-18-comparison-page-enrichment.md
git commit -m "docs: plan comparison page enrichment"
```

## Task 7: Deploy After Review Approval

**Files:**
- No file changes.

**Step 1: Confirm release scope**

Release scope should include only:

- comparison template enrichment;
- pilot comparison copy cleanup/enrichment;
- docs.

**Step 2: Deploy through documented script**

Run:

```bash
cd /srv/BusinessOps/creditdoc
source /srv/BusinessOps/.env
unset CLOUDFLARE_API_TOKEN
export CLOUDFLARE_API_KEY="$CLOUDFLARE_GLOBAL_API_KEY"
./deploy.sh
```

Expected: deploy script completes, cache purge succeeds, smoke routes return 200.

**Step 3: Live-check pilot**

Run:

```bash
node - <<'NODE'
const https = require('https');
const url = 'https://www.creditdoc.co/compare/ecreditadvisor-vs-the-credit-repairmen/';
https.get(url, res => {
  let body = '';
  res.setEncoding('utf8');
  res.on('data', c => body += c);
  res.on('end', () => {
    const required = ['Quick Decision Map','CreditDoc Tools and Guides for This Comparison','Before You Contact Either Company'];
    const missing = required.filter(x => !body.includes(x));
    console.log(`status=${res.statusCode}`);
    if (res.statusCode !== 200 || missing.length) {
      console.error(`missing=${missing.join(',')}`);
      process.exit(1);
    }
    console.log('pilot live enrichment OK');
  });
}).on('error', err => { console.error(err); process.exit(1); });
NODE
```

Expected: `status=200` and `pilot live enrichment OK`.

## Rollout Notes

After the pilot is approved live, future Phase 1 batches should use this rule:

- clean unsafe copy and enrich comparison value together;
- keep batch size small;
- preserve useful facts;
- do not bulk rewrite all comparison records.

