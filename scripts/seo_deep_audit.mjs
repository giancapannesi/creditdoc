import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const distRoot = path.join(root, 'dist');
const reportDir = path.join(root, 'reports');
const reportPath = path.join(reportDir, 'seo-deep-audit.json');
const siteOrigin = 'https://www.creditdoc.co';
const workerPagesRoot = path.join(distRoot, '_worker.js', 'pages');

function walk(dir, predicate, files = []) {
  if (!fs.existsSync(dir)) return files;

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath, predicate, files);
    } else if (predicate(fullPath)) {
      files.push(fullPath);
    }
  }

  return files;
}

function read(filePath) {
  return fs.readFileSync(filePath, 'utf8');
}

function stripTags(html) {
  return html
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function stripScriptsAndStyles(html) {
  return html
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ');
}

function textOfFirst(html, pattern) {
  const match = html.match(pattern);
  return match ? decodeHtml(match[1].trim()) : '';
}

function decodeHtml(value) {
  return value
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>');
}

function attrs(tag) {
  const result = {};
  for (const match of tag.matchAll(/([:\w-]+)\s*=\s*(["'])([\s\S]*?)\2/g)) {
    result[match[1].toLowerCase()] = decodeHtml(match[3]);
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

function hasHttpRefresh(html) {
  return /<meta\b[^>]*http-equiv=["']refresh["'][^>]*>/i.test(html);
}

function pageUrlForFile(filePath) {
  let relative = path.relative(distRoot, filePath).replaceAll(path.sep, '/');
  if (relative === 'index.html') return `${siteOrigin}/`;
  if (relative.endsWith('/index.html')) relative = relative.slice(0, -'index.html'.length);
  else relative = relative.replace(/\.html$/, '');
  return `${siteOrigin}/${relative}`;
}

function fileForInternalHref(href) {
  if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return null;

  let url;
  try {
    url = href.startsWith('http') ? new URL(href) : new URL(href, siteOrigin);
  } catch {
    return null;
  }

  if (url.origin !== siteOrigin) return null;
  let pathname = decodeURIComponent(url.pathname);
  if (pathname.endsWith('/')) pathname += 'index.html';
  else if (!path.extname(pathname)) pathname += '/index.html';
  return path.join(distRoot, pathname.replace(/^\/+/, ''));
}

function routeRegexForWorkerPage(filePath) {
  let route = path.relative(workerPagesRoot, filePath).replaceAll(path.sep, '/');
  route = route.replace(/\.astro\.mjs$/, '');
  route = route.replace(/\.xml\.mjs$/, '.xml');
  route = route.replace(/index$/, '');
  const segments = route.split('/').filter(Boolean);
  const pattern = segments
    .map((segment) => {
      if (/^_[a-z0-9]+_$/i.test(segment)) return '[^/]+';
      return segment.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    })
    .join('/');
  const suffix = route.endsWith('.xml') ? '' : '/?';
  return new RegExp(`^/${pattern}${suffix}$`);
}

function getWorkerRouteMatchers() {
  return walk(workerPagesRoot, (filePath) => filePath.endsWith('.mjs')).map(routeRegexForWorkerPage);
}

function addIssue(issues, severity, code, url, message, detail = {}) {
  issues.push({ severity, code, url, message, ...detail });
}

function getSitemapUrls() {
  const urls = new Set();
  for (const sitemap of walk(distRoot, (filePath) => /sitemap.*\.xml$/.test(path.basename(filePath)))) {
    const xml = read(sitemap);
    for (const match of xml.matchAll(/<loc>([\s\S]*?)<\/loc>/gi)) {
      urls.add(decodeHtml(match[1].trim()));
    }
  }
  return urls;
}

const htmlFiles = walk(distRoot, (filePath) => filePath.endsWith('.html'));
const sitemapUrls = getSitemapUrls();
const workerRouteMatchers = getWorkerRouteMatchers();
const issues = [];
const titleMap = new Map();
const descMap = new Map();
const canonicalMap = new Map();
const pageSummaries = [];

for (const filePath of htmlFiles) {
  const html = read(filePath);
  const url = pageUrlForFile(filePath);
  const title = textOfFirst(html, /<title[^>]*>([\s\S]*?)<\/title>/i);
  const description = firstTagAttrs(html, 'meta', (tagAttrs) => tagAttrs.name === 'description').content || '';
  const canonical = firstTagAttrs(html, 'link', (tagAttrs) => tagAttrs.rel === 'canonical').href || '';
  const robots = firstTagAttrs(html, 'meta', (tagAttrs) => tagAttrs.name === 'robots').content || '';
  const h1Count = (html.match(/<h1\b/gi) || []).length;
  const wordCount = stripTags(html).split(/\s+/).filter(Boolean).length;
  const isNoindex = /noindex/i.test(robots);
  const isRedirect = hasHttpRefresh(html) || /^Redirecting to:/i.test(title);
  const ogTitle = Boolean(firstTagAttrs(html, 'meta', (tagAttrs) => tagAttrs.property === 'og:title' && tagAttrs.content).content);
  const ogDescription = Boolean(firstTagAttrs(html, 'meta', (tagAttrs) => tagAttrs.property === 'og:description' && tagAttrs.content).content);

  pageSummaries.push({ url, title, description, canonical, robots, h1Count, wordCount, isRedirect });

  if (isRedirect) continue;

  if (!title) addIssue(issues, 'error', 'missing_title', url, 'Missing <title>.');
  else {
    if (title.length < 25) addIssue(issues, 'warning', 'short_title', url, `Title is short (${title.length} chars).`, { title });
    if (title.length > 65) addIssue(issues, 'warning', 'long_title', url, `Title is long (${title.length} chars).`, { title });
    titleMap.set(title, [...(titleMap.get(title) || []), url]);
  }

  if (!description) addIssue(issues, 'error', 'missing_meta_description', url, 'Missing meta description.');
  else {
    if (description.length < 70) addIssue(issues, 'warning', 'short_meta_description', url, `Meta description is short (${description.length} chars).`, { description });
    if (description.length > 170) addIssue(issues, 'warning', 'long_meta_description', url, `Meta description is long (${description.length} chars).`, { description });
    descMap.set(description, [...(descMap.get(description) || []), url]);
  }

  if (!canonical) addIssue(issues, 'error', 'missing_canonical', url, 'Missing canonical URL.');
  else {
    canonicalMap.set(canonical, [...(canonicalMap.get(canonical) || []), url]);
    if (!canonical.startsWith(siteOrigin)) addIssue(issues, 'error', 'external_or_relative_canonical', url, 'Canonical is not on the configured site origin.', { canonical });
  }

  if (h1Count !== 1) addIssue(issues, h1Count === 0 ? 'error' : 'warning', 'h1_count', url, `Expected exactly one H1, found ${h1Count}.`);
  if (!isNoindex && wordCount < 250) addIssue(issues, 'warning', 'thin_rendered_text', url, `Low rendered word count (${wordCount}).`);
  if (!ogTitle) addIssue(issues, 'warning', 'missing_og_title', url, 'Missing og:title.');
  if (!ogDescription) addIssue(issues, 'warning', 'missing_og_description', url, 'Missing og:description.');

  for (const script of html.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)) {
    try {
      JSON.parse(decodeHtml(script[1].trim()));
    } catch (error) {
      addIssue(issues, 'error', 'invalid_json_ld', url, 'Invalid JSON-LD block.', { error: error.message });
    }
  }

  const linkHtml = stripScriptsAndStyles(html);
  for (const match of linkHtml.matchAll(/<a\b[^>]*href=["']([^"']+)["'][^>]*>/gi)) {
    const href = decodeHtml(match[1]);
    const targetFile = fileForInternalHref(href);
    const targetUrl = (() => {
      try {
        return href.startsWith('http') ? new URL(href) : new URL(href, siteOrigin);
      } catch {
        return null;
      }
    })();
    const pathname = targetUrl?.origin === siteOrigin ? targetUrl.pathname : '';
    const isServerRoute = workerRouteMatchers.some((pattern) => pattern.test(pathname.endsWith('/') ? pathname : `${pathname}/`));
    const isSitemapUrl = targetUrl ? sitemapUrls.has(targetUrl.href) || sitemapUrls.has(`${targetUrl.origin}${targetUrl.pathname.endsWith('/') ? targetUrl.pathname : `${targetUrl.pathname}/`}`) : false;
    if (targetFile && !fs.existsSync(targetFile) && !isServerRoute && !isSitemapUrl) {
      addIssue(issues, 'error', 'broken_internal_link', url, `Internal link target is missing: ${href}`, { href });
    }
  }
}

for (const [title, urls] of titleMap) {
  if (urls.length > 1 && title) addIssue(issues, 'warning', 'duplicate_title', urls[0], `Duplicate title appears on ${urls.length} pages.`, { title, urls: urls.slice(0, 20) });
}
for (const [description, urls] of descMap) {
  if (urls.length > 1 && description) addIssue(issues, 'warning', 'duplicate_meta_description', urls[0], `Duplicate meta description appears on ${urls.length} pages.`, { description, urls: urls.slice(0, 20) });
}
for (const [canonical, urls] of canonicalMap) {
  if (urls.length > 1 && canonical) addIssue(issues, 'warning', 'duplicate_canonical_target', urls[0], `Canonical target is used by ${urls.length} rendered pages.`, { canonical, urls: urls.slice(0, 20) });
}

for (const summary of pageSummaries) {
  if (/noindex/i.test(summary.robots || '') && sitemapUrls.has(summary.url)) {
    addIssue(issues, 'error', 'noindex_in_sitemap', summary.url, 'Noindex page appears in sitemap.', { canonical: summary.canonical });
  }
}

const grouped = issues.reduce((acc, issue) => {
  const key = `${issue.severity}:${issue.code}`;
  acc[key] = (acc[key] || 0) + 1;
  return acc;
}, {});
const report = {
  generatedAt: new Date().toISOString(),
  checked: {
    htmlPages: htmlFiles.length,
    sitemapUrls: sitemapUrls.size,
  },
  counts: {
    errors: issues.filter((issue) => issue.severity === 'error').length,
    warnings: issues.filter((issue) => issue.severity === 'warning').length,
    byCode: Object.fromEntries(Object.entries(grouped).sort()),
  },
  topIssues: issues.slice(0, 500),
};

fs.mkdirSync(reportDir, { recursive: true });
fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);

console.log(`[seo-deep-audit] checked ${htmlFiles.length} rendered HTML page(s), ${sitemapUrls.size} sitemap URL(s).`);
console.log(`[seo-deep-audit] errors=${report.counts.errors}, warnings=${report.counts.warnings}`);
for (const [code, count] of Object.entries(report.counts.byCode)) {
  console.log(`[seo-deep-audit] ${code} ${count}`);
}
console.log(`[seo-deep-audit] report: ${path.relative(root, reportPath)}`);
