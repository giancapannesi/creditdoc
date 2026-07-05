import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';

const AUDIT_TEXT = process.argv[2] || '/tmp/creditdoc-se-ranking-audit.txt';
const OUT_MANIFEST = 'data/seranking_static_snapshot_urls_2026-07-05.json';
const SITE = 'https://www.creditdoc.co';

function urlToPublicFile(rawUrl) {
  const url = new URL(rawUrl);
  if (url.origin !== SITE) return null;
  if (url.search) return null;
  const path = url.pathname;
  if (!path.startsWith('/review/') && !path.startsWith('/credit-guide/') && !path.startsWith('/categories/')) {
    return null;
  }
  if (!path.endsWith('/')) return null;
  return join('public', path, 'index.html');
}

function extractFlaggedUrls(text) {
  const matches = [];
  let collecting = false;
  for (const line of text.split('\n')) {
    if (line.includes('5XX HTTP Status Codes') || line.includes('5XX pages in XML sitemap')) {
      collecting = true;
      continue;
    }
    if (
      collecting &&
      (
        line.includes('Blocked by noindex') ||
        line.includes('Noindex pages in XML sitemap') ||
        line.includes('Blocked by nofollow') ||
        line.includes('Blocked by robots.txt')
      )
    ) {
      collecting = false;
    }
    if (!collecting) continue;
    const urls = line.match(/https:\/\/www\.creditdoc\.co\/[^\s)]+/g) || [];
    matches.push(...urls);
  }
  const urls = [];
  const seen = new Set();
  for (const raw of matches) {
    const clean = raw.replace(/[),.]+$/, '');
    const file = urlToPublicFile(clean);
    if (!file || seen.has(clean)) continue;
    seen.add(clean);
    urls.push(clean);
  }
  return urls.sort();
}

async function fetchHtml(url) {
  const res = await fetch(url, {
    headers: {
      'user-agent': 'CreditDocStaticSnapshot/2026-07-05 (+https://www.creditdoc.co)',
      accept: 'text/html,application/xhtml+xml',
    },
  });
  const html = await res.text();
  if (!res.ok) {
    throw new Error(`${url} returned ${res.status}`);
  }
  if (!/<html[\s>]/i.test(html) || !/<\/html>/i.test(html)) {
    throw new Error(`${url} did not return a complete HTML document`);
  }
  return `<!-- Static snapshot generated from ${url} for SE Ranking 5XX remediation. -->\n${html}`;
}

const text = await readFile(AUDIT_TEXT, 'utf8');
const urls = extractFlaggedUrls(text);
if (urls.length === 0) {
  throw new Error(`No SE Ranking 5XX URLs found in ${AUDIT_TEXT}`);
}

const manifest = {
  generated_at: new Date().toISOString(),
  source: AUDIT_TEXT,
  count: urls.length,
  urls,
};

for (const url of urls) {
  const file = urlToPublicFile(url);
  if (!file) continue;
  const html = await fetchHtml(url);
  await mkdir(dirname(file), { recursive: true });
  await writeFile(file, html);
  console.log(`${url} -> ${file}`);
}

await mkdir(dirname(OUT_MANIFEST), { recursive: true });
await writeFile(`${OUT_MANIFEST}`, `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`Wrote ${urls.length} static snapshots and ${OUT_MANIFEST}`);
