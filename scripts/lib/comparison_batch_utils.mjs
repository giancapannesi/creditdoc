import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

export const COMPARISON_FIELDS = ['lender_a', 'lender_b', 'summary', 'winner_reason', 'seo_description'];
export const EDITABLE_COMPARISON_FIELDS = ['summary', 'winner_reason', 'seo_description'];

export function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

export function stableJson(value) {
  if (Array.isArray(value)) {
    return `[${value.map(stableJson).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

export function hashComparedFields(row, fields = COMPARISON_FIELDS) {
  const picked = {};
  for (const field of fields) {
    picked[field] = row?.[field] ?? null;
  }
  return createHash('sha256').update(stableJson(picked)).digest('hex');
}

function mapBySlug(rows) {
  return new Map(rows.map((row) => [row.slug, row]));
}

function readComparisonRowsFromSqlite(dbPath) {
  if (!existsSync(dbPath)) {
    throw new Error(`SQLite DB not found: ${dbPath}`);
  }
  const output = execFileSync('sqlite3', ['-json', dbPath, 'SELECT slug, data FROM comparisons ORDER BY slug;'], {
    encoding: 'utf8',
    maxBuffer: 1024 * 1024 * 50,
  }).trim();
  if (!output) return [];
  return JSON.parse(output).map((row) => JSON.parse(row.data));
}

export function checkComparisonDbFreshness({ comparisonsPath = 'src/content/comparisons.json', dbPath = 'data/creditdoc.db' } = {}) {
  const jsonRows = readJson(comparisonsPath);
  const dbRows = readComparisonRowsFromSqlite(dbPath);
  const jsonBySlug = mapBySlug(jsonRows);
  const dbBySlug = mapBySlug(dbRows);
  const mismatches = [];

  for (const slug of [...jsonBySlug.keys()].sort()) {
    const jsonRow = jsonBySlug.get(slug);
    const dbRow = dbBySlug.get(slug);
    if (!dbRow) {
      mismatches.push({ slug, reason: 'missing_in_db' });
      continue;
    }
    const jsonHash = hashComparedFields(jsonRow);
    const dbHash = hashComparedFields(dbRow);
    if (jsonHash !== dbHash) {
      mismatches.push({ slug, reason: 'field_hash_mismatch', jsonHash, dbHash });
    }
  }

  for (const slug of [...dbBySlug.keys()].sort()) {
    if (!jsonBySlug.has(slug)) {
      mismatches.push({ slug, reason: 'missing_in_json' });
    }
  }

  return {
    ok: mismatches.length === 0 && jsonRows.length === dbRows.length,
    jsonCount: jsonRows.length,
    dbCount: dbRows.length,
    mismatches,
  };
}

function diffRows(baseRow, currentRow) {
  const fields = new Set([...Object.keys(baseRow || {}), ...Object.keys(currentRow || {})]);
  const changed = [];
  for (const field of [...fields].sort()) {
    if (stableJson(baseRow?.[field]) !== stableJson(currentRow?.[field])) {
      changed.push(field);
    }
  }
  return changed;
}

export function compareComparisonBatchScope({ baseRows, currentRows, manifest }) {
  const selected = new Set(manifest.selected_slugs || []);
  const allowed = new Set(manifest.allowed_fields || EDITABLE_COMPARISON_FIELDS);
  const baseBySlug = mapBySlug(baseRows);
  const currentBySlug = mapBySlug(currentRows);
  const blockers = [];
  const changedSlugs = [];
  const changedFieldsBySlug = {};

  for (const slug of [...baseBySlug.keys()].sort()) {
    if (!currentBySlug.has(slug)) {
      blockers.push(`row removed: ${slug}`);
      continue;
    }
    const fields = diffRows(baseBySlug.get(slug), currentBySlug.get(slug));
    if (fields.length > 0) {
      changedSlugs.push(slug);
      changedFieldsBySlug[slug] = fields;
      if (!selected.has(slug)) {
        blockers.push(`unselected changed slug: ${slug}`);
      }
      for (const field of fields) {
        if (!allowed.has(field)) {
          blockers.push(`disallowed field changed: ${slug} ${field}`);
        }
      }
    }
  }

  for (const slug of [...currentBySlug.keys()].sort()) {
    if (!baseBySlug.has(slug)) {
      blockers.push(`row added: ${slug}`);
    }
  }

  for (const slug of [...selected].sort()) {
    if (!changedSlugs.includes(slug)) {
      blockers.push(`selected slug not changed: ${slug}`);
    }
  }

  return {
    ok: blockers.length === 0,
    changedSlugs: changedSlugs.sort(),
    changedFieldsBySlug,
    blockers,
  };
}

function compactArray(value, limit = 8) {
  return Array.isArray(value) ? value.filter(Boolean).slice(0, limit) : [];
}

function hasPricing(pricing) {
  if (!pricing || typeof pricing !== 'object') return false;
  if (pricing.monthly_price || pricing.setup_fee || pricing.annual_fee || pricing.apr || pricing.interest_rate) return true;
  return Array.isArray(pricing.tiers) && pricing.tiers.some((tier) => tier && (tier.price || tier.monthly_price || tier.setup_fee));
}

function lenderFacts(lender = {}) {
  const bbbAccredited = lender.bbb_accredited ?? lender.bbb_data?.accredited ?? lender.company_info?.bbb_accredited ?? null;
  return {
    slug: lender.slug || '',
    name: lender.name || '',
    category: lender.category || '',
    pricing: lender.pricing || {},
    bbb_rating: lender.bbb_rating ?? lender.bbb_data?.rating ?? lender.company_info?.bbb_rating ?? '',
    bbb_accredited: bbbAccredited,
    google_rating: lender.google_rating ?? null,
    google_reviews: lender.google_reviews ?? lender.google_reviews_count ?? null,
    services: compactArray(lender.services),
    pros: compactArray(lender.pros),
    cons: compactArray(lender.cons),
  };
}

export function extractComparisonSourceFacts({ comparison, lendersBySlug }) {
  const lenderA = lenderFacts(lendersBySlug[comparison.lender_a]);
  const lenderB = lenderFacts(lendersBySlug[comparison.lender_b]);
  const hasPricingA = hasPricing(lenderA.pricing);
  const hasPricingB = hasPricing(lenderB.pricing);
  return {
    slug: comparison.slug,
    lender_a: lenderA,
    lender_b: lenderB,
    flags: {
      has_pricing_a: hasPricingA,
      has_pricing_b: hasPricingB,
      pricing_missing_a: !hasPricingA,
      pricing_missing_b: !hasPricingB,
      bbb_accreditation_supported_a: lenderA.bbb_accredited === true,
      bbb_accreditation_supported_b: lenderB.bbb_accredited === true,
    },
  };
}

export function selectComparisonsForManifest({ allComparisons, selectedSlugs }) {
  const selected = new Set(selectedSlugs || []);
  const comparisons = allComparisons.filter((comparison) => selected.has(comparison.slug));
  const found = new Set(comparisons.map((comparison) => comparison.slug));
  const missingComparisonSlugs = [...selected].filter((slug) => !found.has(slug)).sort();
  return {
    comparisons,
    missingComparisonSlugs,
    blockers: missingComparisonSlugs.map((slug) => `selected comparison not found: ${slug}`),
  };
}

export function loadLendersForComparisons({ comparisons, lendersDir = 'src/content/lenders' }) {
  const slugs = new Set(comparisons.flatMap((comparison) => [comparison.lender_a, comparison.lender_b]).filter(Boolean));
  const lendersBySlug = {};
  const missingLenderSlugs = [];
  const blockers = [];
  for (const slug of slugs) {
    const path = join(lendersDir, `${slug}.json`);
    if (existsSync(path)) {
      lendersBySlug[slug] = readJson(path);
    } else {
      missingLenderSlugs.push(slug);
      blockers.push(`missing lender source file: ${slug}`);
    }
  }
  return { lendersBySlug, missingLenderSlugs: missingLenderSlugs.sort(), blockers: blockers.sort() };
}
