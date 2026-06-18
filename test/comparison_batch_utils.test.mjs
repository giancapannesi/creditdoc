import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import {
  checkComparisonDbFreshness,
  compareComparisonBatchScope,
  extractComparisonSourceFacts,
  selectComparisonsForManifest,
  loadLendersForComparisons,
} from '../scripts/lib/comparison_batch_utils.mjs';

function tempDir() {
  return mkdtempSync(join(tmpdir(), 'creditdoc-comparison-batch-'));
}

function writeJson(path, value) {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
}

function createComparisonDb(dbPath, rows) {
  execFileSync('sqlite3', [
    dbPath,
    `CREATE TABLE comparisons (
      slug TEXT PRIMARY KEY,
      data JSON NOT NULL,
      checksum TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      updated_by TEXT NOT NULL DEFAULT 'test',
      exported_at TEXT
    );`,
  ]);
  for (const row of rows) {
    const values = [
      row.slug,
      JSON.stringify(row),
      'checksum',
      '2026-06-18T00:00:00Z',
      'test',
    ].map((value) => `'${String(value).replaceAll("'", "''")}'`);
    execFileSync('sqlite3', [
      dbPath,
      `INSERT INTO comparisons (slug, data, checksum, updated_at, updated_by) VALUES (${values.join(', ')});`,
    ]);
  }
}

test('DB freshness passes when SQLite comparison fields match exported JSON', () => {
  const dir = tempDir();
  const comparisonsPath = join(dir, 'comparisons.json');
  const dbPath = join(dir, 'creditdoc.db');
  const rows = [
    { slug: 'alpha-vs-beta', summary: 'A', winner_reason: 'B', seo_description: 'C', untouched: 'x' },
    { slug: 'gamma-vs-delta', summary: 'D', winner_reason: 'E', seo_description: 'F' },
  ];
  writeJson(comparisonsPath, rows);
  createComparisonDb(dbPath, rows);

  const result = checkComparisonDbFreshness({ comparisonsPath, dbPath });

  assert.equal(result.ok, true);
  assert.equal(result.jsonCount, 2);
  assert.equal(result.dbCount, 2);
  assert.deepEqual(result.mismatches, []);
});

test('DB freshness fails when a compared field differs', () => {
  const dir = tempDir();
  const comparisonsPath = join(dir, 'comparisons.json');
  const dbPath = join(dir, 'creditdoc.db');
  writeJson(comparisonsPath, [
    { slug: 'alpha-vs-beta', summary: 'JSON summary', winner_reason: 'B', seo_description: 'C' },
  ]);
  createComparisonDb(dbPath, [
    { slug: 'alpha-vs-beta', summary: 'DB summary', winner_reason: 'B', seo_description: 'C' },
  ]);

  const result = checkComparisonDbFreshness({ comparisonsPath, dbPath });

  assert.equal(result.ok, false);
  assert.equal(result.mismatches[0].slug, 'alpha-vs-beta');
  assert.equal(result.mismatches[0].reason, 'field_hash_mismatch');
});

test('DB freshness fails when lender identity differs even if editable text matches', () => {
  const dir = tempDir();
  const comparisonsPath = join(dir, 'comparisons.json');
  const dbPath = join(dir, 'creditdoc.db');
  writeJson(comparisonsPath, [
    { slug: 'alpha-vs-beta', lender_a: 'alpha', lender_b: 'beta', summary: 'same', winner_reason: 'same', seo_description: 'same' },
  ]);
  createComparisonDb(dbPath, [
    { slug: 'alpha-vs-beta', lender_a: 'wrong-alpha', lender_b: 'beta', summary: 'same', winner_reason: 'same', seo_description: 'same' },
  ]);

  const result = checkComparisonDbFreshness({ comparisonsPath, dbPath });

  assert.equal(result.ok, false);
  assert.equal(result.mismatches[0].slug, 'alpha-vs-beta');
  assert.equal(result.mismatches[0].reason, 'field_hash_mismatch');
});

test('batch scope passes only when selected slugs and allowed fields changed', () => {
  const baseRows = [
    { slug: 'alpha-vs-beta', summary: 'old', winner_reason: 'same', seo_description: 'same', seo_title: 'stable' },
    { slug: 'gamma-vs-delta', summary: 'unchanged', winner_reason: 'same', seo_description: 'same' },
  ];
  const currentRows = [
    { slug: 'alpha-vs-beta', summary: 'new', winner_reason: 'same', seo_description: 'same', seo_title: 'stable' },
    { slug: 'gamma-vs-delta', summary: 'unchanged', winner_reason: 'same', seo_description: 'same' },
  ];
  const result = compareComparisonBatchScope({
    baseRows,
    currentRows,
    manifest: {
      selected_slugs: ['alpha-vs-beta'],
      allowed_fields: ['summary', 'winner_reason', 'seo_description'],
    },
  });

  assert.equal(result.ok, true);
  assert.deepEqual(result.changedSlugs, ['alpha-vs-beta']);
  assert.deepEqual(result.changedFieldsBySlug['alpha-vs-beta'], ['summary']);
});

test('batch scope fails on an unselected slug and disallowed field', () => {
  const baseRows = [
    { slug: 'alpha-vs-beta', summary: 'old', seo_title: 'old title' },
    { slug: 'gamma-vs-delta', summary: 'old' },
  ];
  const currentRows = [
    { slug: 'alpha-vs-beta', summary: 'new', seo_title: 'new title' },
    { slug: 'gamma-vs-delta', summary: 'new' },
  ];
  const result = compareComparisonBatchScope({
    baseRows,
    currentRows,
    manifest: {
      selected_slugs: ['alpha-vs-beta'],
      allowed_fields: ['summary'],
    },
  });

  assert.equal(result.ok, false);
  assert.match(result.blockers.join('\n'), /unselected changed slug: gamma-vs-delta/);
  assert.match(result.blockers.join('\n'), /disallowed field changed: alpha-vs-beta seo_title/);
});

test('source fact extractor preserves pricing and uncertainty flags from lender data', () => {
  const facts = extractComparisonSourceFacts({
    comparison: { slug: 'alpha-vs-beta', lender_a: 'alpha', lender_b: 'beta' },
    lendersBySlug: {
      alpha: {
        slug: 'alpha',
        name: 'Alpha Credit',
        category: 'credit-repair',
        pricing: { monthly_price: 79, setup_fee: 19, tiers: [{ name: 'Flat', price: 419 }] },
        bbb_rating: 'A+',
        bbb_accredited: true,
        google_rating: 4.8,
        google_reviews_count: 120,
        services: ['Disputes'],
        pros: ['Good portal'],
        cons: ['Limited states'],
      },
      beta: {
        slug: 'beta',
        name: 'Beta Credit',
        category: 'credit-repair',
        bbb_rating: 'A+',
        bbb_accredited: false,
      },
    },
  });

  assert.equal(facts.slug, 'alpha-vs-beta');
  assert.equal(facts.lender_a.pricing.monthly_price, 79);
  assert.equal(facts.flags.has_pricing_a, true);
  assert.equal(facts.flags.pricing_missing_b, true);
  assert.equal(facts.flags.bbb_accreditation_supported_a, true);
  assert.equal(facts.flags.bbb_accreditation_supported_b, false);
});

test('source fact extractor reads BBB facts from company_info', () => {
  const facts = extractComparisonSourceFacts({
    comparison: { slug: 'alpha-vs-beta', lender_a: 'alpha', lender_b: 'beta' },
    lendersBySlug: {
      alpha: {
        slug: 'alpha',
        name: 'Alpha Credit',
        company_info: { bbb_rating: 'A+', bbb_accredited: true },
      },
      beta: {
        slug: 'beta',
        name: 'Beta Credit',
        company_info: { bbb_rating: 'B', bbb_accredited: false },
      },
    },
  });

  assert.equal(facts.lender_a.bbb_rating, 'A+');
  assert.equal(facts.lender_a.bbb_accredited, true);
  assert.equal(facts.flags.bbb_accreditation_supported_a, true);
  assert.equal(facts.lender_b.bbb_rating, 'B');
  assert.equal(facts.flags.bbb_accreditation_supported_b, false);
});

test('lender loader records missing lender source files as blockers', () => {
  const dir = tempDir();
  mkdirSync(join(dir, 'lenders'), { recursive: true });
  writeJson(join(dir, 'lenders', 'alpha.json'), { slug: 'alpha', name: 'Alpha Credit' });

  const result = loadLendersForComparisons({
    comparisons: [{ slug: 'alpha-vs-missing', lender_a: 'alpha', lender_b: 'missing' }],
    lendersDir: join(dir, 'lenders'),
  });

  assert.equal(result.lendersBySlug.alpha.name, 'Alpha Credit');
  assert.deepEqual(result.missingLenderSlugs, ['missing']);
  assert.deepEqual(result.blockers, ['missing lender source file: missing']);
});

test('manifest selection records selected comparison slugs missing from content', () => {
  const result = selectComparisonsForManifest({
    allComparisons: [{ slug: 'alpha-vs-beta', lender_a: 'alpha', lender_b: 'beta' }],
    selectedSlugs: ['alpha-vs-beta', 'missing-vs-beta'],
  });

  assert.deepEqual(result.comparisons.map((row) => row.slug), ['alpha-vs-beta']);
  assert.deepEqual(result.missingComparisonSlugs, ['missing-vs-beta']);
  assert.deepEqual(result.blockers, ['selected comparison not found: missing-vs-beta']);
});
