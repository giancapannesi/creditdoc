import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const DIST = join(ROOT, 'dist');
const REPORT_DIR = join(ROOT, 'reports', 'seo-debug');
const TODAY = new Date().toISOString().slice(0, 10);
const REPORT_PATH = join(REPORT_DIR, `public_sanitization_contract_${TODAY}.json`);

// Sources that emit public HTML/JSON. Updated 2026-07-18 after Astro→Python renderer migration:
// Jinja2 templates and hand-rolled Worker replace all src/pages/*.astro + src/middleware.ts.
const PUBLIC_SOURCE_GLOBS = [
  'renderer/templates/review.html.j2',
  'renderer/templates/answer.html.j2',
  'renderer/templates/best.html.j2',
  'renderer/templates/blog.html.j2',
  'renderer/templates/wellness.html.j2',
  'renderer/templates/category.html.j2',
  'renderer/templates/city.html.j2',
  'renderer/templates/brand.html.j2',
  'renderer/templates/state.html.j2',
  'renderer/templates/browse.html.j2',
  'renderer/templates/trends.html.j2',
  'renderer/templates/compare.html.j2',
  'renderer/templates/state_lending_laws.html.j2',
  'renderer/templates/credit_guide_hub.html.j2',
  'renderer/templates/credit_guide_category.html.j2',
  'worker/index.ts',
  'worker/handlers/search.ts',
  'worker/handlers/go.ts',
  'worker/handlers/geo.ts',
  'worker/handlers/email-signup.ts',
  'worker/handlers/origination-intake.ts',
  'worker/handlers/revalidate.ts',
  'src/lib/cache.ts',
];

const BANNED_PUBLIC_PATTERNS = [
  { id: 'x-cdm-debug-header', pattern: /\bx-cdm-[a-z0-9-]+\b/i },
  { id: 'ssr-pilot-copy', pattern: /\bSSR pilot\b/i },
  { id: 'architecture-copy', pattern: /\bArchitecture:\b/i },
  { id: 'internal-batch-copy', pattern: /\bBatch\s+\d+\s+priority\s+#\d+/i },
  { id: 'gsc-signal-copy', pattern: /\bCurrent GSC signal\b/i },
  { id: 'city-enhancement-data-marker', pattern: /\bdata-city-enhancement-batch\b/i },
  { id: 'machine-generated-copy', pattern: /\b(machine generated|AI generated|auto generated|automatically generated)\b/i },
];

const PRIORITY_STATIC_PREFIXES = [
  '/answers/',
  '/blog/',
  '/tools/',
  '/financial-wellness/',
  '/courses/',
  '/best/',
  '/city/',
  '/browse/',
  '/state/',
  '/research/',
  '/resources/',
];

const PRIORITY_EXAMPLES = [
  '/',
  '/tools/mca-repayment-calculator/',
  '/tools/sba-loan-calculator/',
  '/tools/business-line-of-credit-calculator/',
  '/tools/commercial-loan-calculator/',
  '/tools/credit-score-simulator/',
  '/best/best-sba-loans/',
  '/best/best-business-lines-of-credit/',
  '/best/best-small-business-loans/',
  '/answers/does-a-sba-loan-affect-your-credit/',
  '/financial-wellness/',
  '/courses/credit-fundamentals/',
  '/state/california/',
  '/research/consumer-complaints/',
  '/resources/loan-approval-readiness-toolkit/',
];

function readText(path) {
  return readFileSync(path, 'utf8');
}

function routeToDistFile(route) {
  const clean = route.replace(/^https:\/\/www\.creditdoc\.co/i, '').split('?')[0];
  if (clean === '/' || clean === '') return join(DIST, 'index.html');
  return join(DIST, clean.replace(/^\/+/, ''), 'index.html');
}

function distRouteExists(route) {
  return existsSync(routeToDistFile(route));
}

function parseCsvRows(text) {
  const rows = [];
  let row = [];
  let value = '';
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (quoted && ch === '"' && next === '"') {
      value += '"';
      i += 1;
    } else if (ch === '"') {
      quoted = !quoted;
    } else if (!quoted && ch === ',') {
      row.push(value);
      value = '';
    } else if (!quoted && (ch === '\n' || ch === '\r')) {
      if (ch === '\r' && next === '\n') i += 1;
      row.push(value);
      if (row.some((cell) => cell.length > 0)) rows.push(row);
      row = [];
      value = '';
    } else {
      value += ch;
    }
  }
  if (value || row.length) {
    row.push(value);
    if (row.some((cell) => cell.length > 0)) rows.push(row);
  }
  return rows;
}

function loadPriorityCityRoutes(limit = 40) {
  const csvPath = join(ROOT, 'reports', 'local-seo', 'local_pages_with_gsc_impressions_2026-07-12.csv');
  if (!existsSync(csvPath)) return [];
  const rows = parseCsvRows(readText(csvPath));
  const header = rows.shift() || [];
  const urlIndex = header.indexOf('url');
  const familyIndex = header.indexOf('route_family');
  if (urlIndex === -1 || familyIndex === -1) return [];
  return rows
    .filter((row) => row[familyIndex] === 'city' || row[familyIndex] === 'browse_service_city')
    .slice(0, limit)
    .map((row) => row[urlIndex].replace(/^https:\/\/www\.creditdoc\.co/i, ''));
}

function scanText(id, filePath, text) {
  const issues = [];
  for (const banned of BANNED_PUBLIC_PATTERNS) {
    const match = text.match(banned.pattern);
    if (match) {
      issues.push({
        id: banned.id,
        file: relative(ROOT, filePath),
        match: match[0],
      });
    }
  }
  return issues;
}

function scanPublicSources() {
  const issues = [];
  for (const rel of PUBLIC_SOURCE_GLOBS) {
    const file = join(ROOT, rel);
    if (!existsSync(file)) continue;
    issues.push(...scanText('source', file, readText(file)));
  }
  return issues;
}

function scanDistRoutes(routes) {
  const issues = [];
  const checked = [];
  const missing = [];
  for (const route of routes) {
    const file = routeToDistFile(route);
    if (!existsSync(file)) {
      missing.push({ route, expected: relative(ROOT, file) });
      continue;
    }
    const html = readText(file);
    checked.push(route);
    issues.push(...scanText('dist', file, html).map((issue) => ({ ...issue, route })));
    if (!/<html\b/i.test(html) || !/<title>[^<]{10,}<\/title>/i.test(html) || !/<meta name="description" content="[^"]{40,}"/i.test(html)) {
      issues.push({
        id: 'static-html-basic-seo',
        file: relative(ROOT, file),
        route,
        match: 'missing html/title/meta description contract',
      });
    }
  }
  return { issues, checked, missing };
}

function main() {
  const routes = Array.from(new Set([...PRIORITY_EXAMPLES, ...loadPriorityCityRoutes(40)]))
    .filter((route) => route === '/' || PRIORITY_STATIC_PREFIXES.some((prefix) => route.startsWith(prefix)))
    .filter(distRouteExists);
  const sourceIssues = scanPublicSources();
  const dist = scanDistRoutes(routes);
  const result = {
    generated_at: new Date().toISOString(),
    status: sourceIssues.length || dist.issues.length || dist.missing.length ? 'FAIL' : 'PASS',
    checked_route_count: dist.checked.length,
    checked_routes: dist.checked,
    source_issue_count: sourceIssues.length,
    dist_issue_count: dist.issues.length,
    missing_count: dist.missing.length,
    source_issues: sourceIssues,
    dist_issues: dist.issues,
    missing: dist.missing,
    sanitation_priority_order: [
      'Top 40 /city/ and /browse/ pages with GSC impressions',
      'Tools, best money pages, answers, wellness, courses',
      'State, research, and resource pages',
      'Review/category/runtime pages after static-priority pages are clean',
    ],
  };

  mkdirSync(REPORT_DIR, { recursive: true });
  writeFileSync(REPORT_PATH, `${JSON.stringify(result, null, 2)}\n`);

  if (result.status !== 'PASS') {
    console.error(`[public-sanitization-contract] FAILED — report: ${relative(ROOT, REPORT_PATH)}`);
    for (const issue of [...sourceIssues, ...dist.issues].slice(0, 30)) {
      console.error(`[public-sanitization-contract] ${issue.id}: ${issue.file}${issue.route ? ` (${issue.route})` : ''} -> ${JSON.stringify(issue.match)}`);
    }
    if (dist.missing.length) {
      console.error(`[public-sanitization-contract] Missing static HTML routes: ${dist.missing.slice(0, 10).map((m) => m.route).join(', ')}`);
    }
    process.exit(1);
  }

  console.log(`[public-sanitization-contract] OK — ${dist.checked.length} priority static pages checked; report: ${relative(ROOT, REPORT_PATH)}`);
}

main();
