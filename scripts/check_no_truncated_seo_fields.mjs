#!/usr/bin/env node

import { readdirSync, readFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const CONTENT_DIR = join(ROOT, 'src', 'content');
const TITLE_FIELDS = new Set(['title', 'seo_title', 'meta_title', 'h1']);
const TRAILING_ELLIPSIS = /(\.\.\.|…)$/;
const issues = [];

function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath);
    } else if (entry.isFile() && entry.name.endsWith('.json')) {
      scanJson(fullPath);
    }
  }
}

function scanJson(filePath) {
  let data;
  try {
    data = JSON.parse(readFileSync(filePath, 'utf8'));
  } catch (error) {
    issues.push({
      filePath,
      path: '$',
      field: 'json',
      value: error.message,
    });
    return;
  }

  function visit(value, jsonPath) {
    if (Array.isArray(value)) {
      value.forEach((item, index) => visit(item, `${jsonPath}[${index}]`));
      return;
    }
    if (!value || typeof value !== 'object') return;

    for (const [key, child] of Object.entries(value)) {
      const childPath = `${jsonPath}.${key}`;
      if (typeof child === 'string' && TITLE_FIELDS.has(key) && TRAILING_ELLIPSIS.test(child.trim())) {
        issues.push({ filePath, path: childPath, field: key, value: child });
      } else {
        visit(child, childPath);
      }
    }
  }

  visit(data, '$');
}

walk(CONTENT_DIR);

if (issues.length) {
  console.error(`[no-truncated-seo-fields] FAILED — ${issues.length} title-like field(s) end in an ellipsis.`);
  for (const issue of issues.slice(0, 40)) {
    console.error(
      `[no-truncated-seo-fields] ${relative(ROOT, issue.filePath)} ${issue.path}: ${JSON.stringify(issue.value)}`,
    );
  }
  if (issues.length > 40) {
    console.error(`[no-truncated-seo-fields] ...and ${issues.length - 40} more.`);
  }
  process.exit(1);
}

console.log('[no-truncated-seo-fields] OK — no title-like SEO fields end in an ellipsis.');
