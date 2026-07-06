#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const ROOT = '/srv/BusinessOps/creditdoc';
const ANSWERS_DIR = path.join(ROOT, 'src/content/answers');
const DB_PATH = path.join(ROOT, 'data/creditdoc.db');
const REPORT_JSON = path.join(ROOT, 'reports/answer-seo-meta-audit.json');
const REPORT_CSV = path.join(ROOT, 'reports/answer-seo-meta-audit.csv');

function parseArgs(argv) {
  const args = { apply: false, limit: 50 };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--apply') args.apply = true;
    else if (arg === '--limit') args.limit = Number(argv[++i]);
    else if (arg.startsWith('--limit=')) args.limit = Number(arg.slice('--limit='.length));
  }
  if (!Number.isFinite(args.limit) || args.limit < 1) args.limit = 50;
  return args;
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function cleanTitle(value) {
  return String(value || '')
    .replace(/\s*\|\s*CreditDoc\s*$/i, '')
    .replace(/\s*\((?:20\d{2}|19\d{2})[^)]*\)\s*/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function titleFromSlug(slug) {
  return String(slug || '')
    .replace(/-/g, ' ')
    .replace(/\b\w/g, (m) => m.toUpperCase())
    .trim();
}

function normalizePhrase(value, fallbackSlug) {
  const cleaned = cleanTitle(value)
    .replace(/[|]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return (cleaned || titleFromSlug(fallbackSlug)).trim();
}

function moneyPagePhrase(targetMoneyPage) {
  if (!targetMoneyPage) return null;
  const last = String(targetMoneyPage).split('/').filter(Boolean).pop();
  if (!last) return null;
  return last.replace(/^best-/, '').replace(/-/g, ' ').trim();
}

function unique(values) {
  const seen = new Set();
  const out = [];
  for (const value of values) {
    const item = String(value || '').replace(/\s+/g, ' ').trim();
    const key = item.toLowerCase();
    if (!item || seen.has(key)) continue;
    seen.add(key);
    out.push(item);
  }
  return out;
}

function proposeMetadata(row, json) {
  const primary = normalizePhrase(
    json.primary_question || json.h1 || row.h1 || json.title || row.title || json.primary_phrase || row.primary_phrase,
    row.slug,
  );
  const faqQuestions = Array.isArray(json.faq_schema)
    ? json.faq_schema.map((item) => item?.question).filter(Boolean)
    : [];
  const secondary = unique([
    ...(Array.isArray(json.secondary_phrases) ? json.secondary_phrases : []),
    ...faqQuestions.slice(0, 3),
    moneyPagePhrase(json.target_money_page || row.target_money_page),
    String(json.cluster_pillar || row.cluster_pillar || '').replace(/-/g, ' '),
  ]).filter((item) => item.toLowerCase() !== primary.toLowerCase()).slice(0, 6);
  return { primary, secondary };
}

function isGeneratedPhrase(value, json) {
  const phrase = normalizePhrase(value, json.slug);
  if (!phrase) return false;
  const sources = [
    json.primary_question,
    json.h1,
    json.title,
  ].map((item) => normalizePhrase(item, json.slug)).filter(Boolean);
  return sources.some((source) => source === phrase || source.startsWith(phrase));
}

function needsPrimaryRepair(row, json, proposed) {
  const current = normalizePhrase(row.primary_phrase || json.primary_phrase, row.slug);
  if (!current) return false;
  if (current === proposed.primary) return false;

  const reviewedByThisSchedule = json.seo_meta_reviewed_at === '2026-07-06';
  if (!reviewedByThisSchedule) return false;

  return current.length < proposed.primary.length && isGeneratedPhrase(current, json);
}

function significantTokens(value) {
  const stop = new Set(['a', 'an', 'and', 'are', 'can', 'do', 'does', 'for', 'get', 'how', 'i', 'in', 'is', 'of', 'or', 'the', 'to', 'what', 'with', 'you', 'your']);
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, ' ')
    .split(/\s+/)
    .filter((token) => token.length > 2 && !stop.has(token));
}

function phraseOverlap(meta, phrase) {
  const metaTokens = new Set(significantTokens(meta));
  const phraseTokens = unique(significantTokens(phrase));
  if (!phraseTokens.length) return 0;
  const hits = phraseTokens.filter((token) => metaTokens.has(token)).length;
  return hits / phraseTokens.length;
}

function csvCell(value) {
  return `"${String(value ?? '').replace(/"/g, '""')}"`;
}

function sqlString(value) {
  return `'${String(value ?? '').replace(/'/g, "''")}'`;
}

function readDbRows() {
  const sql = [
    'SELECT slug, cluster_pillar, title, h1, meta_description, target_money_page,',
    'primary_phrase, secondary_phrases, status, published_at, updated_at, data',
    "FROM cluster_answers WHERE status='published' ORDER BY published_at, slug;",
  ].join(' ');
  const result = spawnSync('sqlite3', ['-json', DB_PATH, sql], {
    cwd: ROOT,
    encoding: 'utf8',
    maxBuffer: 1024 * 1024 * 80,
    timeout: 1000 * 30,
  });
  if (result.status !== 0) {
    throw new Error(`sqlite3 failed: ${result.stderr || result.stdout}`);
  }
  return JSON.parse(result.stdout || '[]');
}

function readAnswerJson(slug) {
  const file = path.join(ANSWERS_DIR, `${slug}.json`);
  if (!fs.existsSync(file)) return { file, json: null };
  return { file, json: JSON.parse(fs.readFileSync(file, 'utf8')) };
}

function applyBatch(rows) {
  const statements = ['BEGIN;'];
  for (const item of rows) {
    const { row, file, json, proposed } = item;
    const nextJson = {
      ...json,
      primary_phrase: proposed.primary,
      secondary_phrases: proposed.secondary,
      seo_meta_reviewed_at: new Date().toISOString().slice(0, 10),
    };
    fs.writeFileSync(file, `${JSON.stringify(nextJson, null, 2)}\n`);
    statements.push([
      'UPDATE cluster_answers SET',
      `primary_phrase=${sqlString(proposed.primary)},`,
      `secondary_phrases=${sqlString(JSON.stringify(proposed.secondary))},`,
      `data=${sqlString(JSON.stringify(nextJson))},`,
      "updated_at=CURRENT_TIMESTAMP,",
      "updated_by='answer_meta_schedule'",
      `WHERE slug=${sqlString(row.slug)};`,
    ].join(' '));
  }
  statements.push('COMMIT;');
  const result = spawnSync('sqlite3', [DB_PATH], {
    cwd: ROOT,
    input: statements.join('\n'),
    encoding: 'utf8',
    maxBuffer: 1024 * 1024 * 20,
    timeout: 1000 * 30,
  });
  if (result.status !== 0) {
    throw new Error(`sqlite3 apply failed: ${result.stderr || result.stdout}`);
  }
}

function main() {
  const args = parseArgs(process.argv);
  const dbRows = readDbRows();
  const audited = [];
  const candidates = [];
  let missingJson = 0;

  for (const row of dbRows) {
    const { file, json } = readAnswerJson(row.slug);
    if (!json) {
      missingJson += 1;
      continue;
    }
    const proposed = proposeMetadata(row, json);
    const meta = json.meta_description || row.meta_description || '';
    const hasPrimary = Boolean(String(row.primary_phrase || json.primary_phrase || '').trim());
    const repairPrimary = needsPrimaryRepair(row, json, proposed);
    const metaLength = meta.length;
    const overlap = phraseOverlap(meta, proposed.primary);
    const needsMetaReview = metaLength < 120 || metaLength > 160 || overlap < 0.25;
    const item = {
      row,
      file,
      json,
      proposed,
      audit: {
        slug: row.slug,
        title: json.title || row.title,
        target_money_page: json.target_money_page || row.target_money_page || '',
        current_primary_phrase: row.primary_phrase || json.primary_phrase || '',
        proposed_primary_phrase: proposed.primary,
        proposed_secondary_phrases: proposed.secondary,
        meta_length: metaLength,
        phrase_meta_overlap: Number(overlap.toFixed(2)),
        needs_primary_phrase: !hasPrimary,
        needs_primary_repair: repairPrimary,
        needs_meta_review: needsMetaReview,
      },
    };
    audited.push(item);
    if (!hasPrimary || repairPrimary) candidates.push(item);
  }

  const batch = candidates.slice(0, args.limit);
  if (args.apply && batch.length) applyBatch(batch);

  const summary = {
    generated_at: new Date().toISOString(),
    mode: args.apply ? 'apply' : 'audit',
    limit: args.limit,
    published_answers: dbRows.length,
    answer_json_missing: missingJson,
    with_primary_phrase: audited.filter((item) => !item.audit.needs_primary_phrase).length,
    missing_primary_phrase: audited.filter((item) => item.audit.needs_primary_phrase).length,
    needs_primary_repair: audited.filter((item) => item.audit.needs_primary_repair).length,
    meta_too_short: audited.filter((item) => item.audit.meta_length < 120).length,
    meta_too_long: audited.filter((item) => item.audit.meta_length > 160).length,
    needs_meta_review: audited.filter((item) => item.audit.needs_meta_review).length,
    candidate_count: candidates.length,
    selected_candidate_count: batch.length,
    applied: args.apply ? batch.length : 0,
    primary_phrase_coverage_complete: candidates.length === 0,
  };

  const report = {
    summary,
    applied: args.apply ? batch.map((item) => item.audit) : [],
    selected_candidates: args.apply ? [] : batch.map((item) => item.audit),
    next_candidates: candidates.slice(args.apply ? args.limit : 0, args.apply ? args.limit + 100 : 100).map((item) => item.audit),
    meta_review_candidates: audited.filter((item) => item.audit.needs_meta_review).slice(0, 100).map((item) => item.audit),
  };

  ensureDir(path.dirname(REPORT_JSON));
  fs.writeFileSync(REPORT_JSON, `${JSON.stringify(report, null, 2)}\n`);
  const csvRows = [
    ['slug', 'target_money_page', 'current_primary_phrase', 'proposed_primary_phrase', 'meta_length', 'phrase_meta_overlap', 'needs_primary_phrase', 'needs_primary_repair', 'needs_meta_review'].join(','),
    ...audited.map((item) => [
      csvCell(item.audit.slug),
      csvCell(item.audit.target_money_page),
      csvCell(item.audit.current_primary_phrase),
      csvCell(item.audit.proposed_primary_phrase),
      item.audit.meta_length,
      item.audit.phrase_meta_overlap,
      item.audit.needs_primary_phrase,
      item.audit.needs_primary_repair,
      item.audit.needs_meta_review,
    ].join(',')),
  ];
  fs.writeFileSync(REPORT_CSV, `${csvRows.join('\n')}\n`);

  console.log(JSON.stringify(summary, null, 2));
}

main();
