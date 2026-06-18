import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

export const COMPARISON_FIELDS = ['lender_a', 'lender_b', 'summary', 'winner_reason', 'seo_description'];
export const EDITABLE_COMPARISON_FIELDS = ['summary', 'winner_reason', 'seo_description'];
export const REQUIRED_RENDERED_SECTIONS = [
  'Quick Decision Map',
  'CreditDoc Tools and Guides for This Comparison',
  'Before You Contact Either Company',
];

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

function collectPricingNumbers(pricing = {}) {
  const numbers = new Set();
  const visit = (value) => {
    if (value == null) return;
    if (typeof value === 'number' && Number.isFinite(value)) {
      if (value <= 0) return;
      numbers.add(String(Math.round(value * 100) / 100));
      numbers.add(String(Math.round(value)));
      return;
    }
    if (Array.isArray(value)) {
      for (const item of value) visit(item);
      return;
    }
    if (typeof value === 'object') {
      for (const item of Object.values(value)) visit(item);
    }
  };
  visit(pricing);
  return numbers;
}

function collectRateNumbers(pricing = {}) {
  const rates = new Set();
  const visit = (value, key = '') => {
    if (value == null) return;
    const keyLooksLikeRate = /\b(apr|rate|interest)\b/i.test(key);
    if (typeof value === 'number' && Number.isFinite(value) && keyLooksLikeRate) {
      rates.add(String(Math.round(value * 100) / 100));
      rates.add(String(Math.round(value)));
      return;
    }
    if (typeof value === 'string' && keyLooksLikeRate) {
      const match = value.match(/([0-9]+(?:\.\d+)?)/);
      if (match) {
        rates.add(String(Math.round(Number(match[1]) * 100) / 100));
        rates.add(String(Math.round(Number(match[1]))));
      }
      return;
    }
    if (Array.isArray(value)) {
      for (const item of value) visit(item, key);
      return;
    }
    if (typeof value === 'object') {
      for (const [childKey, item] of Object.entries(value)) visit(item, childKey);
    }
  };
  visit(pricing);
  return rates;
}

function normalizeMoneyAmount(value) {
  return String(Number(String(value).replaceAll(',', '')) || 0);
}

function normalizeRateAmount(value) {
  return String(Number(String(value).replaceAll(',', '')) || 0);
}

function lenderFactEntries(fact = {}) {
  return [
    ['lender_a', fact.lender_a || {}],
    ['lender_b', fact.lender_b || {}],
  ];
}

function allowedMoneyAmountsFor(lender = {}) {
  return new Set([...collectPricingNumbers(lender.pricing)].map(normalizeMoneyAmount));
}

function allowedRateAmountsFor(lender = {}) {
  return new Set([...collectRateNumbers(lender.pricing)].map(normalizeRateAmount));
}

function allAllowedMoneyAmounts(fact = {}) {
  return new Set(lenderFactEntries(fact).flatMap(([, lender]) => [...allowedMoneyAmountsFor(lender)]));
}

function allAllowedRateAmounts(fact = {}) {
  return new Set(lenderFactEntries(fact).flatMap(([, lender]) => [...allowedRateAmountsFor(lender)]));
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function hasNameReference(text, lender = {}) {
  const candidates = [lender.name, lender.slug].filter(Boolean);
  return candidates.some((candidate) => {
    const normalized = String(candidate).replaceAll('-', ' ').trim();
    if (!normalized) return false;
    return new RegExp(`\\b${escapeRegExp(normalized)}\\b`, 'i').test(String(text).replaceAll('-', ' '));
  });
}

function localClaimText(text, index, length) {
  const start = Math.max(0, index - 80);
  const end = Math.min(text.length, index + length + 80);
  return text.slice(start, end);
}

function sentenceClaimText(text, index, length) {
  const before = text.slice(0, index);
  const after = text.slice(index + length);
  const start = Math.max(before.lastIndexOf('.'), before.lastIndexOf('!'), before.lastIndexOf('?')) + 1;
  const nextStops = ['.', '!', '?']
    .map((mark) => after.indexOf(mark))
    .filter((value) => value >= 0);
  const end = nextStops.length > 0 ? index + length + Math.min(...nextStops) : text.length;
  return text.slice(start, end).trim();
}

function claimSegmentText(text, index, length) {
  const separators = [
    '.', '!', '?', ';',
    ' while ', ' whereas ', ' but ', ' however ', ' although ', ', but ', ', however ', ', although ',
  ];
  const lower = text.toLowerCase();
  let start = 0;
  for (const separator of separators) {
    const position = lower.lastIndexOf(separator, index);
    if (position >= 0) start = Math.max(start, position + separator.length);
  }
  const priorComma = lower.lastIndexOf(',', index);
  const sentenceStart = Math.max(
    lower.lastIndexOf('.', index),
    lower.lastIndexOf('!', index),
    lower.lastIndexOf('?', index),
    -1,
  ) + 1;
  const commaPrefix = text.slice(sentenceStart, priorComma).trim();
  if (priorComma >= sentenceStart && /^(although|however)\b/i.test(commaPrefix)) {
    start = priorComma + 1;
  }

  let end = text.length;
  for (const separator of separators) {
    const position = lower.indexOf(separator, index + length);
    if (position >= 0) end = Math.min(end, position);
  }

  return text.slice(start, end).trim();
}

function clauseClaimText(text, index, length) {
  return claimSegmentText(text, index, length) || sentenceClaimText(text, index, length);
}

function lenderNameRanges(text, fact = {}) {
  const ranges = [];
  for (const [, lender] of lenderFactEntries(fact)) {
    if (!lender.name) continue;
    const pattern = new RegExp(escapeRegExp(lender.name), 'gi');
    for (const match of text.matchAll(pattern)) {
      ranges.push([match.index, match.index + match[0].length]);
    }
  }
  return ranges;
}

function positionInsideRanges(position, ranges) {
  return ranges.some(([start, end]) => position >= start && position < end);
}

function lastSeparatorOutsideRanges(text, separator, beforeIndex, ranges) {
  let cursor = beforeIndex;
  while (cursor >= 0) {
    const position = text.lastIndexOf(separator, cursor);
    if (position < 0) return -1;
    if (!positionInsideRanges(position, ranges)) return position;
    cursor = position - 1;
  }
  return -1;
}

function nextSeparatorOutsideRanges(text, separator, afterIndex, ranges) {
  let cursor = afterIndex;
  while (cursor < text.length) {
    const position = text.indexOf(separator, cursor);
    if (position < 0) return -1;
    if (!positionInsideRanges(position, ranges)) return position;
    cursor = position + separator.length;
  }
  return -1;
}

function accreditationClaimText(text, index, length, fact = {}) {
  const separators = [
    '.', '!', '?', ';',
    ' while ', ' whereas ', ' but ', ' however ', ' although ',
    ', but ', ', however ', ', although ', ' and ', ', and ',
  ];
  const lower = text.toLowerCase();
  const protectedRanges = lenderNameRanges(text, fact);
  let start = 0;
  for (const separator of separators) {
    const position = lastSeparatorOutsideRanges(lower, separator, index, protectedRanges);
    if (position >= 0) {
      start = Math.max(start, position + separator.length);
    }
  }

  let end = text.length;
  for (const separator of separators) {
    const position = nextSeparatorOutsideRanges(lower, separator, index + length, protectedRanges);
    if (position >= 0) {
      end = Math.min(end, position);
    }
  }

  return text.slice(start, end).trim() || clauseClaimText(text, index, length);
}

function referencedLenders(text, fact = {}) {
  return lenderFactEntries(fact).filter(([, lender]) => hasNameReference(text, lender));
}

function isAmountAllowedForClaim({ fact, amount, context }) {
  const referenced = referencedLenders(context, fact);
  if (referenced.length === 0) return allAllowedMoneyAmounts(fact).has(amount);
  return referenced.some(([, lender]) => allowedMoneyAmountsFor(lender).has(amount));
}

function isRateAllowedForClaim({ fact, rate, context }) {
  const referenced = referencedLenders(context, fact);
  if (referenced.length === 0) return allAllowedRateAmounts(fact).has(rate);
  return referenced.some(([, lender]) => allowedRateAmountsFor(lender).has(rate));
}

function accreditationSupportedForClaim({ fact, context }) {
  const referenced = referencedLenders(context, fact);
  if (referenced.length === 0) {
    return fact?.lender_a?.bbb_accredited === true && fact?.lender_b?.bbb_accredited === true;
  }
  return referenced.every(([, lender]) => lender.bbb_accredited === true);
}

function isCollectiveAccreditationContext(context, fact = {}) {
  const referenced = referencedLenders(context, fact);
  const hasExplicitNoAccreditation = /\b(?:(?:without|not|non|no)[\s-]+(?:BBB[\s-]+)?accredit(?:ed|ation)|(?:do|does|did)\s+not\s+(?:have|hold)\s+(?:BBB\s+)?accreditation)\b/i.test(context);
  return !hasExplicitNoAccreditation &&
    referenced.length > 1 &&
    /\b(both|are|were|have|has|had|hold|holds|held)\b/i.test(context);
}

function pricingSupportForFreeClaim({ fact, context }) {
  return false;
}

function hasLocalAccreditationNegation(text, index, length) {
  const lower = text.toLowerCase();
  const start = Math.max(
    0,
    index - 36,
    lower.lastIndexOf(',', index) + 1,
    lower.lastIndexOf(';', index) + 1,
    lower.lastIndexOf('.', index) + 1,
    lower.lastIndexOf('!', index) + 1,
    lower.lastIndexOf('?', index) + 1,
    lower.lastIndexOf(' and ', index) + 5,
  );
  const local = text.slice(start, index + length);
  return /\b(?:(?:without|not|non|no)[\s-]+(?:BBB[\s-]+)?accredit(?:ed|ation)|(?:do|does|did)\s+not\s+(?:have|hold)\s+(?:BBB\s+)?accreditation)\b/i.test(local);
}

function scanTextForClaims({ slug, text, field, fact }) {
  const blockers = [];
  const reviews = [];
  const info = [];
  const moneyMatches = text.matchAll(/\$([0-9][0-9,]*(?:\.\d{1,2})?)/g);
  for (const match of moneyMatches) {
    const amount = normalizeMoneyAmount(match[1]);
    const context = clauseClaimText(text, match.index, match[0].length) || localClaimText(text, match.index, match[0].length);
    if (isAmountAllowedForClaim({ fact, amount, context })) {
      info.push({ slug, field, type: 'source_supported_money_amount', amount });
    } else {
      blockers.push({ slug, field, type: 'unsupported_money_amount', amount, match: match[0] });
    }
  }

  const rateMatches = [
    ...text.matchAll(/([0-9]+(?:\.\d+)?)\s*(?:%|percent)/gi),
    ...text.matchAll(/\b(?:apr|interest\s+rate|rate|interest)\s+(?:of\s+)?([0-9]+(?:\.\d+)?)(?!\s*(?:%|percent))/gi),
    ...text.matchAll(/\b(?:apr|interest\s+rate|rate|interest)\s*(?::|=|-|–|—|\s+(?:is|are|was|were|at|set\s+at|listed\s+at|around|about))\s*([0-9]+(?:\.\d+)?)(?!\s*(?:%|percent))/gi),
    ...text.matchAll(/([0-9]+(?:\.\d+)?)\s+(?:apr|interest\s+rate)\b/gi),
  ];
  for (const match of rateMatches) {
    const context = clauseClaimText(text, match.index, match[0].length) || localClaimText(text, match.index, match[0].length);
    if (!/\b(apr|rate|interest)\b/i.test(context)) continue;
    const rate = normalizeRateAmount(match[1]);
    if (isRateAllowedForClaim({ fact, rate, context })) {
      info.push({ slug, field, type: 'source_supported_rate_amount', rate });
    } else {
      blockers.push({ slug, field, type: 'unsupported_rate_claim', rate, match: match[0] });
    }
  }

  const freePricingPattern = /\b(?:free\s+(?:to use|service|plan|subscription)|costs?\s+nothing|no\s+(?:monthly\s+)?(?:fee|cost|charge))\b/i;
  const freePricingMatch = text.match(freePricingPattern);
  if (freePricingMatch) {
    const context = localClaimText(text, freePricingMatch.index, freePricingMatch[0].length);
    if (!pricingSupportForFreeClaim({ fact, context })) {
      blockers.push({ slug, field, type: 'unsupported_free_pricing_claim', match: freePricingMatch[0] });
    }
  }

  const accreditationMatches = text.matchAll(/\b(accredited|accreditation)\b/gi);
  for (const match of accreditationMatches) {
    const narrowContext = accreditationClaimText(text, match.index, match[0].length, fact);
    const broadContext = clauseClaimText(text, match.index, match[0].length);
    const narrowReferences = referencedLenders(narrowContext, fact);
    const broadReferences = referencedLenders(broadContext, fact);
    const context = isCollectiveAccreditationContext(broadContext, fact) ||
      (narrowReferences.length === 0 && broadReferences.length === 1)
      ? broadContext
      : narrowContext;
    const negativeAccreditation = hasLocalAccreditationNegation(text, match.index, match[0].length);
    if (!negativeAccreditation && !accreditationSupportedForClaim({ fact, context })) {
      blockers.push({ slug, field, type: 'unsupported_accreditation_claim' });
    }
  }

  const riskyPatterns = [
    /\bbest\b/i,
    /\bwinner\b/i,
    /\bguaranteed\b/i,
    /\bguarantee\b/i,
    /\bsuperior\b/i,
    /\bbetter value\b/i,
    /\bclear pick\b/i,
    /\bsafer choice\b/i,
    /\blowest\b/i,
    /\bno BBB rating\b/i,
    /\bred flag\b/i,
    /\bsaves?\b/i,
  ];
  for (const pattern of riskyPatterns) {
    if (pattern.test(text)) {
      reviews.push({ slug, field, type: 'risky_phrase', pattern: pattern.source });
    }
  }

  return { blockers, reviews, info };
}

export function checkComparisonClaimSafety({ comparisons, factsBySlug }) {
  const blockers = [];
  const reviews = [];
  const info = [];
  for (const comparison of comparisons) {
    const fact = factsBySlug[comparison.slug] || {};
    for (const field of EDITABLE_COMPARISON_FIELDS) {
      const text = String(comparison[field] || '');
      const result = scanTextForClaims({ slug: comparison.slug, text, field, fact });
      blockers.push(...result.blockers);
      reviews.push(...result.reviews);
      info.push(...result.info);
    }
  }
  return { ok: blockers.length === 0, blockers, reviews, info };
}

export function factsArrayToMap(facts = []) {
  return Object.fromEntries(facts.map((fact) => [fact.slug, fact]));
}

export function checkRenderedComparisonBatch({ distDir = 'dist', selectedSlugs, factsBySlug }) {
  const blockers = [];
  const reviews = [];
  const info = [];
  const pages = [];
  for (const slug of selectedSlugs || []) {
    const path = join(distDir, 'compare', slug, 'index.html');
    if (!existsSync(path)) {
      blockers.push({ slug, type: 'missing_rendered_page', path });
      pages.push({ slug, path, exists: false, sections_ok: false });
      continue;
    }
    const html = readFileSync(path, 'utf8');
    const missingSections = REQUIRED_RENDERED_SECTIONS.filter((section) => !html.includes(section));
    if (missingSections.length > 0) {
      for (const section of missingSections) {
        blockers.push({ slug, type: 'missing_rendered_section', section });
      }
    }
    const result = scanTextForClaims({
      slug,
      text: html,
      field: 'rendered_html',
      fact: factsBySlug[slug] || {},
    });
    blockers.push(...result.blockers);
    reviews.push(...result.reviews);
    info.push(...result.info);
    pages.push({ slug, path, exists: true, sections_ok: missingSections.length === 0, missing_sections: missingSections });
  }
  return { ok: blockers.length === 0, pages, blockers, reviews, info };
}
