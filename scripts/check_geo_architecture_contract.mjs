#!/usr/bin/env node
// Guard the local SEO architecture:
// /city/ is the hub, /browse/ is the city-category money route, and
// /credit-guide/{city}/{category}/ must not be used as a priority internal
// destination because those pages are noindex/follow.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');

const priorityFiles = [
  'src/pages/credit-guide/[slug]/index.astro',
  'src/pages/credit-guide/[slug]/[category].astro',
  'src/pages/categories/[category].astro',
];

const prohibitedPatterns = [
  /href=\{`\/credit-guide\/\$\{slug\}\/\$\{[^}]+\}\/?`\}/,
  /href=\{`\/credit-guide\/\$\{g\.slug\}\/\$\{category\}\/?`\}/,
  /href:\s*`\/credit-guide\/\$\{city\.slug\}\/\$\{categorySlug\}\/?`/,
];

const failures = [];

for (const relativePath of priorityFiles) {
  const source = readFileSync(join(ROOT, relativePath), 'utf8');
  for (const pattern of prohibitedPatterns) {
    if (pattern.test(source)) {
      failures.push(`${relativePath}: priority internal link points to noindex credit-guide category route (${pattern})`);
    }
  }
}

if (failures.length > 0) {
  console.error('[geo-architecture-contract] FAILED');
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}

console.log(`[geo-architecture-contract] OK — ${priorityFiles.length} priority source file(s) checked.`);
