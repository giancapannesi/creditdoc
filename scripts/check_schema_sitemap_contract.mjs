#!/usr/bin/env node
// Post-build contract for the two SEO surfaces most likely to regress quietly:
// generated XML sitemaps and rendered JSON-LD schema.

import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const DIST = join(ROOT, 'dist');
const REPORT = join(ROOT, 'reports', 'schema-sitemap-contract.json');
const SITE = 'https://www.creditdoc.co';
const SITE_ORIGIN = new URL(SITE).origin;

const REQUIRED_STATIC_FAMILY_SCHEMA = new Map([
  ['answers', ['Article', 'BreadcrumbList']],
  ['best', ['Article', 'BreadcrumbList', 'ItemList']],
  ['blog', ['Article', 'BreadcrumbList']],
  ['courses', ['BreadcrumbList']],
  ['financial-wellness', ['Article', 'BreadcrumbList']],
  ['tools', ['BreadcrumbList']],
]);

const REQUIRED_STATIC_FAMILIES = new Set([
  'answers',
  'best',
  'blog',
  'courses',
  'financial-wellness',
  'tools',
]);

const FORBIDDEN_SITEMAP_PATTERNS = [
  /\/api\//,
  /\/go\//,
  /\/linkedin-oauth-callback\/?$/,
  /\/search\/?$/,
  /\/specials\/?$/,
  /\/print\/?$/,
];

const SITEMAP_FAMILY_BUDGETS = new Map([
  // These are not ranking targets; keep generous caps to catch accidental
  // explosions, not normal production growth.
  ['review', 20000],
  ['credit-guide', 8000],
  ['trends', 1500],
  ['compare', 1000],
  ['browse', 1000],
  ['city', 1000],
]);

const PAGE_LEVEL_SCHEMA_TYPES = new Set([
  'Article',
  'BlogPosting',
  'CollectionPage',
  'Course',
  'FAQPage',
  'ProfilePage',
  'Review',
  'WebApplication',
  'WebPage',
]);

function schemaTypeList(item) {
  const type = item?.['@type'];
  if (Array.isArray(type)) return type.map(String);
  if (type) return [String(type)];
  return [];
}

function isPageLevelSchema(item) {
  return schemaTypeList(item).some((type) => PAGE_LEVEL_SCHEMA_TYPES.has(type));
}

function sameUrl(left, right) {
  try {
    return new URL(left).href === new URL(right).href;
  } catch {
    return left === right;
  }
}

function walk(dir, predicate, out = []) {
  if (!existsSync(dir)) return out;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) walk(full, predicate, out);
    else if (predicate(full)) out.push(full);
  }
  return out;
}

function decodeXml(value) {
  return String(value || '')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>');
}

function stripTags(html) {
  return html
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function attrs(tag) {
  const result = {};
  for (const match of tag.matchAll(/([:\w-]+)\s*=\s*(["'])([\s\S]*?)\2/g)) {
    result[match[1].toLowerCase()] = decodeXml(match[3]);
  }
  return result;
}

function firstTagAttrs(html, tagName, predicate) {
  const tagPattern = new RegExp(`<${tagName}\\b[^>]*>`, 'gi');
  for (const match of html.matchAll(tagPattern)) {
    const tagAttrs = attrs(match[0]);
    if (predicate(tagAttrs)) return tagAttrs;
  }
  return {};
}

function htmlFileToUrl(file) {
  let rel = relative(DIST, file).replaceAll(sep, '/');
  if (rel === 'index.html') return `${SITE}/`;
  if (rel.endsWith('/index.html')) rel = rel.slice(0, -'index.html'.length);
  else rel = rel.replace(/\.html$/, '');
  return `${SITE}/${rel}`;
}

function urlFamily(url) {
  const first = new URL(url).pathname.split('/').filter(Boolean)[0];
  return first || 'home';
}

function artifactCandidates(url) {
  const pathname = new URL(url).pathname;
  const clean = pathname.replace(/^\/+/, '');
  if (!clean) return [join(DIST, 'index.html')];
  if (clean.endsWith('/')) return [join(DIST, clean, 'index.html')];
  return [join(DIST, clean), join(DIST, clean, 'index.html')];
}

function hasArtifact(url) {
  return artifactCandidates(url).some((file) => existsSync(file));
}

function addIssue(issues, severity, code, message, detail = {}) {
  issues.push({ severity, code, message, ...detail });
}

function readSitemaps(issues) {
  const sitemapFiles = readdirSync(DIST).filter((name) => /^sitemap.*\.xml$/.test(name));
  const pageUrls = [];
  const sitemapIndexUrls = [];

  if (!sitemapFiles.includes('sitemap-index.xml')) {
    addIssue(issues, 'error', 'missing_sitemap_index', 'dist/sitemap-index.xml is missing.');
  }

  for (const file of sitemapFiles) {
    const xml = readFileSync(join(DIST, file), 'utf8');
    const locs = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => decodeXml(match[1].trim()));
    if (file === 'sitemap-index.xml') sitemapIndexUrls.push(...locs);
    else {
      if (locs.length > 50000) {
        addIssue(issues, 'error', 'sitemap_too_large', `${file} exceeds Google's 50,000 URL limit.`, { file, count: locs.length });
      }
      const bytes = statSync(join(DIST, file)).size;
      if (bytes > 50 * 1024 * 1024) {
        addIssue(issues, 'error', 'sitemap_file_too_large', `${file} exceeds Google's 50MB uncompressed limit.`, { file, bytes });
      }
      pageUrls.push(...locs);
    }
  }

  return { sitemapFiles, sitemapIndexUrls, pageUrls };
}

function validateSitemap(issues) {
  const { sitemapFiles, sitemapIndexUrls, pageUrls } = readSitemaps(issues);
  const urlCounts = new Map();
  const familyCounts = {};

  for (const url of pageUrls) {
    urlCounts.set(url, (urlCounts.get(url) || 0) + 1);

    let parsed;
    try {
      parsed = new URL(url);
    } catch {
      addIssue(issues, 'error', 'invalid_sitemap_url', 'Sitemap contains an invalid URL.', { url });
      continue;
    }

    if (parsed.origin !== SITE_ORIGIN) {
      addIssue(issues, 'error', 'wrong_sitemap_origin', 'Sitemap URL is not on the CreditDoc origin.', { url });
    }
    if (parsed.search || parsed.hash) {
      addIssue(issues, 'error', 'sitemap_url_has_query_or_hash', 'Sitemap URL contains a query string or hash.', { url });
    }
    if (!parsed.pathname.endsWith('/')) {
      addIssue(issues, 'warning', 'sitemap_url_not_trailing_slash', 'Sitemap URL does not use trailing slash canonical form.', { url });
    }
    if (FORBIDDEN_SITEMAP_PATTERNS.some((pattern) => pattern.test(parsed.pathname))) {
      addIssue(issues, 'error', 'forbidden_sitemap_url', 'Sitemap includes a forbidden utility, redirect, noindex, or print URL.', { url });
    }

    const family = urlFamily(url);
    familyCounts[family] = (familyCounts[family] || 0) + 1;
    if (REQUIRED_STATIC_FAMILIES.has(family) && !hasArtifact(url)) {
      addIssue(issues, 'error', 'static_family_url_missing_artifact', 'Important static SEO family URL has no built HTML artifact.', { url, family });
    }
  }

  for (const [url, count] of urlCounts) {
    if (count > 1) {
      addIssue(issues, 'error', 'duplicate_sitemap_url', 'Sitemap contains a duplicate URL.', { url, count });
    }
  }

  for (const url of sitemapIndexUrls) {
    const name = new URL(url).pathname.split('/').pop();
    if (!name || !sitemapFiles.includes(name)) {
      addIssue(issues, 'error', 'sitemap_index_points_to_missing_file', 'Sitemap index points to a missing generated sitemap file.', { url });
    }
  }

  for (const [family, maxCount] of SITEMAP_FAMILY_BUDGETS) {
    if ((familyCounts[family] || 0) > maxCount) {
      addIssue(issues, 'error', 'sitemap_family_budget_exceeded', 'Sitemap family exceeded its crawl-budget guardrail.', {
        family,
        count: familyCounts[family],
        maxCount,
      });
    }
  }

  return { sitemapFiles, sitemapIndexUrls, pageUrls, familyCounts };
}

function normalizeJsonLdItem(item) {
  if (!item || typeof item !== 'object') return [];
  if (Array.isArray(item)) return item.flatMap(normalizeJsonLdItem);
  if (Array.isArray(item['@graph'])) return item['@graph'].flatMap(normalizeJsonLdItem);
  return [item];
}

function schemaTypes(items) {
  const types = new Set();
  for (const item of items) {
    const type = item?.['@type'];
    if (Array.isArray(type)) type.forEach((value) => types.add(String(value)));
    else if (type) types.add(String(type));
  }
  return types;
}

function validateSchema(issues) {
  const htmlFiles = walk(DIST, (file) => file.endsWith('.html'));
  const familySchemaCounts = {};

  for (const file of htmlFiles) {
    const html = readFileSync(file, 'utf8');
    const url = htmlFileToUrl(file);
    const family = urlFamily(url);
    const canonical = firstTagAttrs(html, 'link', (tagAttrs) => tagAttrs.rel === 'canonical').href || '';
    const title = (html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1] || '').trim();
    const description = firstTagAttrs(html, 'meta', (tagAttrs) => tagAttrs.name === 'description').content || '';
    const wordCount = stripTags(html).split(/\s+/).filter(Boolean).length;
    const isLeaf = !new URL(url).pathname.match(/^\/(?:answers|best|blog|courses|financial-wellness|tools)\/?$/);
    const requiredTypes = isLeaf ? REQUIRED_STATIC_FAMILY_SCHEMA.get(family) : null;
    const jsonLdItems = [];

    for (const script of html.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)) {
      try {
        const parsed = JSON.parse(decodeXml(script[1].trim()));
        jsonLdItems.push(...normalizeJsonLdItem(parsed));
      } catch (error) {
        addIssue(issues, 'error', 'invalid_json_ld', 'Rendered page contains invalid JSON-LD.', { url, error: error.message });
      }
    }

    const types = schemaTypes(jsonLdItems);
    familySchemaCounts[family] = familySchemaCounts[family] || {};
    for (const type of types) familySchemaCounts[family][type] = (familySchemaCounts[family][type] || 0) + 1;

    for (const item of jsonLdItems) {
      if (!item['@context']) {
        addIssue(issues, 'error', 'json_ld_missing_context', 'JSON-LD item is missing @context.', { url, type: item['@type'] || null });
      }
      if (!item['@type']) {
        addIssue(issues, 'error', 'json_ld_missing_type', 'JSON-LD item is missing @type.', { url });
      }
      if (isPageLevelSchema(item) && item.url && String(item.url).startsWith(SITE) && canonical && !sameUrl(item.url, canonical)) {
        addIssue(issues, 'warning', 'schema_url_mismatches_canonical', 'JSON-LD url differs from canonical.', { url, schemaUrl: item.url, canonical });
      }
    }

    if (requiredTypes) {
      if (!jsonLdItems.length) {
        addIssue(issues, 'error', 'missing_json_ld', 'Important static SEO page has no JSON-LD.', { url, family });
      }
      for (const type of requiredTypes) {
        if (!types.has(type)) {
          addIssue(issues, 'error', 'missing_required_schema_type', 'Important static SEO page is missing required schema type.', { url, family, type });
        }
      }
      if (!canonical || canonical !== url) {
        addIssue(issues, 'error', 'static_family_bad_canonical', 'Important static SEO page canonical does not match the rendered URL.', { url, canonical });
      }
      if (!title || !description || wordCount < 250) {
        addIssue(issues, 'error', 'static_family_weak_rendered_page', 'Important static SEO page is missing title/meta or has very low rendered text.', {
          url,
          titleLength: title.length,
          descriptionLength: description.length,
          wordCount,
        });
      }
    }
  }

  return { htmlPages: htmlFiles.length, familySchemaCounts };
}

function main() {
  if (!existsSync(DIST)) {
    throw new Error('dist/ does not exist. Run npm run build first.');
  }

  const issues = [];
  const sitemap = validateSitemap(issues);
  const schema = validateSchema(issues);
  const counts = issues.reduce((acc, issue) => {
    const key = `${issue.severity}:${issue.code}`;
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
  const report = {
    generatedAt: new Date().toISOString(),
    checked: {
      sitemapFiles: sitemap.sitemapFiles.length,
      sitemapIndexUrls: sitemap.sitemapIndexUrls.length,
      sitemapPageUrls: sitemap.pageUrls.length,
      htmlPages: schema.htmlPages,
    },
    sitemapFamilyCounts: Object.fromEntries(Object.entries(sitemap.familyCounts).sort((a, b) => b[1] - a[1])),
    familySchemaCounts: schema.familySchemaCounts,
    counts: {
      errors: issues.filter((issue) => issue.severity === 'error').length,
      warnings: issues.filter((issue) => issue.severity === 'warning').length,
      byCode: counts,
    },
    topIssues: issues.slice(0, 100),
  };

  mkdirSync(join(ROOT, 'reports'), { recursive: true });
  writeFileSync(REPORT, `${JSON.stringify(report, null, 2)}\n`);

  if (report.counts.errors > 0) {
    console.error(`[schema-sitemap-contract] FAILED — errors=${report.counts.errors}, warnings=${report.counts.warnings}`);
    for (const issue of report.topIssues.slice(0, 20)) {
      console.error(`[schema-sitemap-contract] ${issue.severity}:${issue.code} ${issue.url || ''} ${issue.message}`);
    }
    console.error(`[schema-sitemap-contract] report: ${REPORT}`);
    process.exit(1);
  }

  console.log(`[schema-sitemap-contract] OK — sitemap URLs=${sitemap.pageUrls.length}, HTML pages=${schema.htmlPages}, warnings=${report.counts.warnings}`);
  console.log(`[schema-sitemap-contract] report: ${REPORT}`);
}

main();
