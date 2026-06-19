import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import {
  checkComparisonClaimSafety,
  checkComparisonDbFreshness,
  compareComparisonBatchScope,
  extractComparisonSourceFacts,
  checkRenderedComparisonBatch,
  buildComparisonReviewPacket,
  buildComparisonPreflightReport,
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

test('review packet includes compact before/after field diffs, facts, findings, and reviewer questions', () => {
  const packet = buildComparisonReviewPacket({
    manifest: {
      batch_id: 'credit-repair-pricing-refunds-001',
      group: 'credit-repair-pricing-refunds',
      selected_slugs: ['alpha-vs-beta'],
      allowed_fields: ['summary', 'winner_reason', 'seo_description'],
    },
    baseRows: [
      {
        slug: 'alpha-vs-beta',
        lender_a: 'alpha',
        lender_b: 'beta',
        summary: 'Old summary',
        winner_reason: 'Old reason',
        seo_description: 'Old meta',
        body: 'This full body must not enter the packet.',
      },
    ],
    currentRows: [
      {
        slug: 'alpha-vs-beta',
        lender_a: 'alpha',
        lender_b: 'beta',
        summary: 'New summary',
        winner_reason: 'Old reason',
        seo_description: 'New meta',
        body: 'This full body must not enter the packet.',
      },
    ],
    factsPayload: {
      comparisons: [{
        slug: 'alpha-vs-beta',
        lender_a: { name: 'Alpha', pricing: { monthly_price: 79 }, pros: ['Portal'] },
        lender_b: { name: 'Beta', pricing: {}, cons: ['No listed price'] },
        flags: { has_pricing_a: true, pricing_missing_b: true },
      }],
    },
    claimReport: {
      blockers: [{ slug: 'alpha-vs-beta', type: 'unsupported_money_amount', field: 'summary' }],
      reviews: [{ slug: 'alpha-vs-beta', type: 'soft_claim', field: 'summary' }],
      info: [{ slug: 'alpha-vs-beta', type: 'source_supported_price', field: 'summary' }],
    },
    renderedReport: {
      blockers: [],
      reviews: [{ slug: 'alpha-vs-beta', type: 'rendered_soft_claim' }],
      info: [],
    },
  });

  assert.equal(packet.batch_id, 'credit-repair-pricing-refunds-001');
  assert.equal(packet.rows.length, 1);
  assert.deepEqual(packet.rows[0].changed_fields, ['seo_description', 'summary']);
  assert.deepEqual(packet.rows[0].before_after.summary, { before: 'Old summary', after: 'New summary' });
  assert.equal(packet.rows[0].before_after.body, undefined);
  assert.equal(packet.rows[0].allowed_facts.lender_a.name, 'Alpha');
  assert.equal(packet.rows[0].scanner_findings.blockers.length, 1);
  assert.equal(packet.rows[0].scanner_findings.reviews.length, 2);
  assert.match(packet.rows[0].reviewer_questions.join('\n'), /preserve useful page value/);
  assert.match(packet.rows[0].reviewer_questions.join('\n'), /unsupported/);
  assert.match(packet.rows[0].reviewer_questions.join('\n'), /too restrictive/);
});

test('review packet truncates long scanner snippets', () => {
  const packet = buildComparisonReviewPacket({
    manifest: {
      batch_id: 'credit-repair-pricing-refunds-001',
      selected_slugs: ['alpha-vs-beta'],
      allowed_fields: ['summary'],
    },
    baseRows: [{ slug: 'alpha-vs-beta', summary: 'Old' }],
    currentRows: [{ slug: 'alpha-vs-beta', summary: 'New' }],
    claimReport: {
      blockers: [{
        slug: 'alpha-vs-beta',
        type: 'rendered_text_probe',
        snippet: 'x'.repeat(700),
      }],
    },
  });

  const text = packet.rows[0].scanner_findings.blockers[0].text;
  assert.equal(text.length, 283);
  assert.match(text, /\.\.\.$/);
});

test('preflight report allows selected slugs before any comparison edits', () => {
  const report = buildComparisonPreflightReport({
    manifest: {
      batch_id: 'credit-repair-pricing-refunds-001',
      group: 'credit-repair-pricing-refunds',
      selected_slugs: ['alpha-vs-beta'],
      allowed_fields: ['summary', 'winner_reason', 'seo_description'],
    },
    dbFreshness: { ok: true, jsonCount: 1, dbCount: 1, mismatches: [] },
    factsPayload: { ok: true, blockers: [], comparisons: [{ slug: 'alpha-vs-beta' }] },
  });

  assert.equal(report.ok, true);
  assert.equal(report.batch_id, 'credit-repair-pricing-refunds-001');
  assert.equal(report.selected_count, 1);
  assert.deepEqual(report.selected_slugs, ['alpha-vs-beta']);
  assert.deepEqual(report.blockers, []);
  assert.deepEqual(report.reports, ['db_freshness_report.json', 'source_facts.json', 'scope_preview.json']);
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

test('claim scanner blocks unsupported dollar amounts and flags winner language', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha costs $99/month, while Beta costs $777/month.',
      winner_reason: 'Alpha is the clear winner.',
      seo_description: 'Compare Alpha and Beta.',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { pricing: { monthly_price: 99 }, bbb_accredited: false },
        lender_b: { pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'unsupported_money_amount');
  assert.equal(result.blockers[0].amount, '777');
  assert.equal(result.reviews[0].type, 'risky_phrase');
});

test('claim scanner blocks accreditation language when source facts do not support it', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha is BBB accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { pricing: {}, bbb_accredited: false },
        lender_b: { pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'unsupported_accreditation_claim');
});

test('claim scanner allows explicit no-accreditation wording', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha has A+ BBB letter-grade context without accreditation.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { pricing: {}, bbb_accredited: false },
        lender_b: { pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, true);
});

test('claim scanner still blocks positive BBB accredited wording when unsupported', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha is a BBB accredited business.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { pricing: {}, bbb_accredited: false },
        lender_b: { pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'unsupported_accreditation_claim');
});

test('claim scanner blocks unsupported APR and rate claims', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Beta offers 36% APR financing.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'unsupported_rate_claim');
});

test('claim scanner blocks unsupported APR wording without percent symbol', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Beta offers 24 percent APR and an APR of 36.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers.filter((blocker) => blocker.type === 'unsupported_rate_claim').length, 2);
});

test('claim scanner blocks unsupported natural-language APR and interest-rate wording', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: "Beta APR is 24. Beta's interest rate is 25. Beta has APR set at 26. Beta offers 27 APR. Beta APR: 28. Beta APR - 29. Beta APR=30.",
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers.filter((blocker) => blocker.type === 'unsupported_rate_claim').length, 7);
});

test('claim scanner blocks fabricated zero and free pricing when pricing is missing', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Beta costs $0 per month and is free to use.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers.some((blocker) => blocker.type === 'unsupported_money_amount'), true);
  assert.equal(result.blockers.some((blocker) => blocker.type === 'unsupported_free_pricing_claim'), true);
});

test('claim scanner scopes prices to the lender named near the claim', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Beta costs $99 per month.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: { monthly_price: 99 }, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: { monthly_price: 149 }, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'unsupported_money_amount');
});

test('claim scanner blocks swapped prices in while clauses', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha costs $149 per month, while Beta costs $99 per month.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: { monthly_price: 99 }, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: { monthly_price: 149 }, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers.filter((blocker) => blocker.type === 'unsupported_money_amount').length, 2);
});

test('claim scanner scopes accreditation to the lender named near the claim', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Beta is BBB accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'unsupported_accreditation_claim');
});

test('claim scanner allows supported accreditation when the other lender is explicitly not accredited', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha lists A+ BBB accreditation context. Beta lists A+ BBB letter-grade context without accreditation.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, true);
});

test('claim scanner uses local accreditation context when both lenders are mentioned in the field', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha lists A+ BBB accreditation context. Beta remains relevant for lower listed pricing and dashboard access.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, true);
});

test('claim scanner scopes accreditation across while clauses', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha has an A+ BBB rating (accredited), while Beta has an A+ BBB rating.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, true);
});

test('claim scanner blocks swapped repeated accreditation claims in while clauses', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha is BBB accredited, while Beta is BBB accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'unsupported_accreditation_claim');
});

test('claim scanner blocks unsupported positive accreditation before a negative contrast clause', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha is BBB accredited, but Beta is not BBB-accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'unsupported_accreditation_claim');
});

test('claim scanner blocks unsupported positive accreditation after sentence-leading negative contrast clauses', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Although Beta is not BBB-accredited, Alpha is BBB accredited. However Beta is not BBB-accredited, Alpha is BBB accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers.filter((blocker) => blocker.type === 'unsupported_accreditation_claim').length, 2);
});

test('claim scanner blocks mixed positive and negative accreditation claims joined by and', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha is BBB accredited and Beta is not BBB-accredited. Beta is not BBB-accredited, and Alpha is BBB accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers.filter((blocker) => blocker.type === 'unsupported_accreditation_claim').length, 2);
});

test('claim scanner allows supported positive accreditation joined to explicit no-accreditation wording by and', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha is BBB accredited and Beta is not BBB-accredited. Beta is not BBB-accredited, and Alpha is BBB accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, true);
});

test('claim scanner blocks unsupported accreditation for lender names containing and', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'walters-vs-alpha',
      summary: 'Walters Bank and Trust Company is BBB accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'walters-vs-alpha': {
        lender_a: { name: 'Walters Bank and Trust Company', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Alpha', pricing: {}, bbb_accredited: true },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'unsupported_accreditation_claim');
});

test('claim scanner allows supported accreditation for lender names containing and', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'walters-vs-alpha',
      summary: 'Walters Bank and Trust Company is BBB accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'walters-vs-alpha': {
        lender_a: { name: 'Walters Bank and Trust Company', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Alpha', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, true);
});

test('claim scanner allows supported mixed accreditation when a lender name contains and', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'walters-vs-alpha',
      summary: 'Walters Bank and Trust Company is BBB accredited and Alpha is not BBB-accredited. Alpha is not BBB-accredited and Walters Bank and Trust Company is BBB accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'walters-vs-alpha': {
        lender_a: { name: 'Walters Bank and Trust Company', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Alpha', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, true);
});

test('claim scanner checks collective accreditation claims against both lenders', () => {
  const bothSupported = checkComparisonClaimSafety({
    comparisons: [{ slug: 'alpha-vs-beta', summary: 'Alpha and Beta are BBB accredited. Alpha and Beta have BBB accreditation.', winner_reason: '', seo_description: '' }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: true },
      },
    },
  });
  const firstUnsupported = checkComparisonClaimSafety({
    comparisons: [{ slug: 'alpha-vs-beta', summary: 'Alpha and Beta are BBB accredited. Alpha and Beta have BBB accreditation.', winner_reason: '', seo_description: '' }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: true },
      },
    },
  });
  const secondUnsupported = checkComparisonClaimSafety({
    comparisons: [{ slug: 'alpha-vs-beta', summary: 'Alpha and Beta are BBB accredited. Alpha and Beta have BBB accreditation.', winner_reason: '', seo_description: '' }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(bothSupported.ok, true);
  assert.equal(firstUnsupported.ok, false);
  assert.equal(secondUnsupported.ok, false);
});

test('claim scanner checks collective have-accreditation claims against both lenders', () => {
  const bothSupported = checkComparisonClaimSafety({
    comparisons: [{ slug: 'alpha-vs-beta', summary: 'Alpha and Beta have BBB accreditation.', winner_reason: '', seo_description: '' }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: true },
      },
    },
  });
  const firstUnsupported = checkComparisonClaimSafety({
    comparisons: [{ slug: 'alpha-vs-beta', summary: 'Alpha and Beta have BBB accreditation.', winner_reason: '', seo_description: '' }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: true },
      },
    },
  });
  const secondUnsupported = checkComparisonClaimSafety({
    comparisons: [{ slug: 'alpha-vs-beta', summary: 'Alpha and Beta have BBB accreditation.', winner_reason: '', seo_description: '' }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(bothSupported.ok, true);
  assert.equal(firstUnsupported.ok, false);
  assert.equal(secondUnsupported.ok, false);
});

test('claim scanner allows supported mixed accreditation with has-no-accreditation wording', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Alpha is BBB accredited and Beta has no BBB accreditation. Beta has no BBB accreditation and Alpha is BBB accredited. Alpha has BBB accreditation and Beta has no BBB accreditation.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, true);
});

test('claim scanner allows explicit does-not-have accreditation wording', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Beta does not have BBB accreditation. Alpha and Beta do not have BBB accreditation. Alpha is BBB accredited and Beta does not have BBB accreditation. Beta does not hold BBB accreditation. Alpha and Beta do not hold BBB accreditation. Alpha is BBB accredited and Beta does not hold BBB accreditation.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: true },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, true);
});

test('claim scanner allows hyphenated explicit no-accreditation wording', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Beta is not BBB-accredited.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, true);
});

test('claim scanner does not treat default zero pricing as support for free service claims', () => {
  const result = checkComparisonClaimSafety({
    comparisons: [{
      slug: 'alpha-vs-beta',
      summary: 'Beta is free to use.',
      winner_reason: '',
      seo_description: '',
    }],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { name: 'Alpha', pricing: {}, bbb_accredited: false },
        lender_b: { name: 'Beta', pricing: { monthly_price: 0, setup_fee: 0 }, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'unsupported_free_pricing_claim');
});

test('rendered scanner requires enrichment sections and scans rendered claims', () => {
  const dir = tempDir();
  const compareDir = join(dir, 'compare', 'alpha-vs-beta');
  mkdirSync(compareDir, { recursive: true });
  writeFileSync(join(compareDir, 'index.html'), [
    '<h2>Quick Decision Map</h2>',
    '<h2>CreditDoc Tools and Guides for This Comparison</h2>',
    '<h2>Before You Contact Either Company</h2>',
    '<p>Alpha costs $777/month.</p>',
  ].join('\n'));

  const result = checkRenderedComparisonBatch({
    distDir: dir,
    selectedSlugs: ['alpha-vs-beta'],
    factsBySlug: {
      'alpha-vs-beta': {
        lender_a: { pricing: { monthly_price: 99 }, bbb_accredited: false },
        lender_b: { pricing: {}, bbb_accredited: false },
      },
    },
  });

  assert.equal(result.ok, false);
  assert.equal(result.pages[0].sections_ok, true);
  assert.equal(result.blockers[0].type, 'unsupported_money_amount');
});

test('rendered scanner blocks missing enrichment sections', () => {
  const dir = tempDir();
  const compareDir = join(dir, 'compare', 'alpha-vs-beta');
  mkdirSync(compareDir, { recursive: true });
  writeFileSync(join(compareDir, 'index.html'), '<p>No sections here.</p>');

  const result = checkRenderedComparisonBatch({
    distDir: dir,
    selectedSlugs: ['alpha-vs-beta'],
    factsBySlug: { 'alpha-vs-beta': { lender_a: { pricing: {} }, lender_b: { pricing: {} } } },
  });

  assert.equal(result.ok, false);
  assert.equal(result.blockers[0].type, 'missing_rendered_section');
});
