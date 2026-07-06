#!/usr/bin/env node
// Guard the commercial /best/ pages from broad safety rewrites that erase
// exact search-intent wording such as "Best SBA Loans".

import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const DIST = join(ROOT, 'dist');
const LISTICLES = join(ROOT, 'src', 'content', 'listicles.json');

function decodeHtml(value) {
  return String(value || '')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ')
    .trim();
}

function stripTags(value) {
  return decodeHtml(String(value || '').replace(/<[^>]+>/g, ' '));
}

function titleText(html) {
  return decodeHtml(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1] || '');
}

function h1Text(html) {
  return stripTags(html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)?.[1] || '');
}

function metaDescription(html) {
  return decodeHtml(html.match(/<meta\s+name=["']description["']\s+content=["']([^"']*)["'][^>]*>/i)?.[1] || '');
}

function jsonLdItems(html) {
  const items = [];
  for (const script of html.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)) {
    const parsed = JSON.parse(decodeHtml(script[1]));
    if (Array.isArray(parsed)) items.push(...parsed);
    else if (Array.isArray(parsed?.['@graph'])) items.push(...parsed['@graph']);
    else items.push(parsed);
  }
  return items;
}

function addIssue(issues, code, message, detail) {
  issues.push({ code, message, ...detail });
}

const listicles = JSON.parse(readFileSync(LISTICLES, 'utf8'));
const issues = [];
let checked = 0;

for (const listicle of listicles) {
  const sourceTitle = listicle.seo_title || listicle.title || '';
  const sourceH1 = listicle.title || '';
  const expectsBestTitle = /\bbest\b/i.test(sourceTitle);
  const expectsBestH1 = /\bbest\b/i.test(sourceH1);

  if (!expectsBestTitle && !expectsBestH1) continue;

  const file = join(DIST, 'best', listicle.slug, 'index.html');
  if (!existsSync(file)) {
    addIssue(issues, 'missing_best_artifact', 'Best listicle is missing a rendered HTML artifact.', { slug: listicle.slug });
    continue;
  }

  checked += 1;
  const html = readFileSync(file, 'utf8');
  const renderedTitle = titleText(html);
  const renderedH1 = h1Text(html);
  const renderedDescription = metaDescription(html);
  const article = jsonLdItems(html).find((item) => item?.['@type'] === 'Article');
  const headline = decodeHtml(article?.headline || '');

  if (expectsBestTitle && !/\bbest\b/i.test(renderedTitle)) {
    addIssue(issues, 'best_title_lost_intent', 'Rendered SEO title lost the source "Best" wording.', {
      slug: listicle.slug,
      sourceTitle,
      renderedTitle,
    });
  }
  if (expectsBestH1 && !/\bbest\b/i.test(renderedH1)) {
    addIssue(issues, 'best_h1_lost_intent', 'Rendered H1 lost the source "Best" wording.', {
      slug: listicle.slug,
      sourceH1,
      renderedH1,
    });
  }
  if (expectsBestH1 && !/\bbest\b/i.test(headline)) {
    addIssue(issues, 'best_article_headline_lost_intent', 'Article schema headline lost the source "Best" wording.', {
      slug: listicle.slug,
      sourceH1,
      headline,
    });
  }
  if (expectsBestTitle && !/\bbest\b/i.test(renderedDescription)) {
    addIssue(issues, 'best_meta_description_lost_intent', 'Rendered meta description lost the source "Best" wording.', {
      slug: listicle.slug,
      sourceTitle,
      renderedDescription,
    });
  }
  for (const [field, value] of [
    ['title', renderedTitle],
    ['h1', renderedH1],
    ['description', renderedDescription],
    ['articleHeadline', headline],
  ]) {
    if (/^compare\b/i.test(value) && /\bbest\b/i.test(sourceTitle || sourceH1)) {
      addIssue(issues, 'best_rendered_as_compare', 'Best listicle rendered its SEO identity as Compare.', {
        slug: listicle.slug,
        field,
        value,
      });
    }
  }
}

if (issues.length) {
  console.error(`[best-serp-contract] FAILED — checked=${checked}, issues=${issues.length}`);
  for (const issue of issues.slice(0, 20)) {
    console.error(`[best-serp-contract] ${issue.code} ${issue.slug || ''} ${issue.message}`);
  }
  process.exit(1);
}

console.log(`[best-serp-contract] OK — ${checked} /best/ listicle page(s) preserve source "Best" title intent.`);
