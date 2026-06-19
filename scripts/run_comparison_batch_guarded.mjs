#!/usr/bin/env node
import { execFileSync, spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import {
  buildComparisonPreflightReport,
  checkComparisonClaimSafety,
  checkComparisonDbFreshness,
  checkRenderedComparisonBatch,
  compareComparisonBatchScope,
  extractComparisonSourceFacts,
  factsArrayToMap,
  loadLendersForComparisons,
  readJson,
  selectComparisonsForManifest,
} from './lib/comparison_batch_utils.mjs';

function argValue(name, fallback) {
  const index = process.argv.indexOf(name);
  return index === -1 ? fallback : process.argv[index + 1];
}

function writeJson(path, value) {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
}

function loadBaseRows(base) {
  try {
    return JSON.parse(execFileSync('git', ['show', `${base}:src/content/comparisons.json`], {
      encoding: 'utf8',
      maxBuffer: 1024 * 1024 * 50,
    }));
  } catch {
    return readJson('src/content/comparisons.json');
  }
}

function buildFactsPayload(manifest) {
  const selected = selectComparisonsForManifest({
    allComparisons: readJson('src/content/comparisons.json'),
    selectedSlugs: manifest.selected_slugs || [],
  });
  const { lendersBySlug, missingLenderSlugs, blockers: lenderBlockers } = loadLendersForComparisons({
    comparisons: selected.comparisons,
  });
  const blockers = [...selected.blockers, ...lenderBlockers].sort();
  return {
    batch_id: manifest.batch_id || '',
    generated_at: new Date().toISOString(),
    ok: blockers.length === 0,
    missing_comparison_slugs: selected.missingComparisonSlugs,
    missing_lender_slugs: missingLenderSlugs,
    blockers,
    comparisons: selected.comparisons.map((comparison) => extractComparisonSourceFacts({ comparison, lendersBySlug })),
  };
}

function scopePreview(manifest) {
  return {
    ok: true,
    selected_count: (manifest.selected_slugs || []).length,
    selected_slugs: [...(manifest.selected_slugs || [])].sort(),
    allowed_fields: manifest.allowed_fields || ['summary', 'winner_reason', 'seo_description'],
    note: 'Preflight preview only. Strict changed-scope enforcement runs in check mode after edits.',
  };
}

function statusFor({ manifest, phase, ok, blockers, reports }) {
  return {
    batch_id: manifest.batch_id || '',
    phase,
    ok,
    blockers,
    reports,
  };
}

function runBuild() {
  const result = spawnSync('npm', ['run', 'build'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  return {
    ok: result.status === 0,
    status: result.status,
    stdout_tail: (result.stdout || '').split('\n').slice(-40).join('\n'),
    stderr_tail: (result.stderr || '').split('\n').slice(-40).join('\n'),
  };
}

function runReviewPacket({ manifestPath, outputDir, base }) {
  const result = spawnSync('node', [
    'scripts/build_comparison_review_packet.mjs',
    '--manifest', manifestPath,
    '--facts', join(outputDir, 'source_facts.json'),
    '--claim-report', join(outputDir, 'claim_safety_report.json'),
    '--rendered-report', join(outputDir, 'rendered_report.json'),
    '--output-dir', outputDir,
    '--base', base,
  ], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  return {
    ok: result.status === 0,
    status: result.status,
    stdout: result.stdout || '',
    stderr: result.stderr || '',
  };
}

function runPreflight({ manifest, outputDir, statusPath }) {
  const dbFreshness = checkComparisonDbFreshness();
  const factsPayload = buildFactsPayload(manifest);
  const preview = scopePreview(manifest);
  const preflight = buildComparisonPreflightReport({ manifest, dbFreshness, factsPayload });

  writeJson(join(outputDir, 'db_freshness_report.json'), dbFreshness);
  writeJson(join(outputDir, 'source_facts.json'), factsPayload);
  writeJson(join(outputDir, 'scope_preview.json'), preview);
  writeJson(join(outputDir, 'preflight_report.json'), preflight);

  const status = statusFor({
    manifest,
    phase: 'preflight',
    ok: preflight.ok,
    blockers: preflight.blockers,
    reports: [...preflight.reports, 'preflight_report.json'],
  });
  writeJson(statusPath, status);
  return { status, dbFreshness, factsPayload };
}

function runCheck({ manifestPath, manifest, outputDir, statusPath, base }) {
  const preflight = runPreflight({ manifest, outputDir, statusPath });
  const reports = [
    'db_freshness_report.json',
    'source_facts.json',
    'scope_preview.json',
    'preflight_report.json',
  ];
  const blockers = [...preflight.status.blockers];

  const scope = compareComparisonBatchScope({
    baseRows: loadBaseRows(base),
    currentRows: readJson('src/content/comparisons.json'),
    manifest,
  });
  writeJson(join(outputDir, 'scope_report.json'), scope);
  reports.push('scope_report.json');
  if (!scope.ok) blockers.push(...scope.blockers);

  if (blockers.length === 0) {
    const selected = selectComparisonsForManifest({
      allComparisons: readJson('src/content/comparisons.json'),
      selectedSlugs: manifest.selected_slugs || [],
    });
    const claim = checkComparisonClaimSafety({
      comparisons: selected.comparisons,
      factsBySlug: factsArrayToMap(preflight.factsPayload.comparisons || []),
    });
    claim.selection_blockers = selected.blockers;
    claim.ok = claim.ok && selected.blockers.length === 0;
    writeJson(join(outputDir, 'claim_safety_report.json'), claim);
    reports.push('claim_safety_report.json');
    if (!claim.ok) blockers.push(...claim.blockers.map((blocker) => `${blocker.slug}: ${blocker.type}`), ...claim.selection_blockers);
  }

  if (blockers.length === 0) {
    const build = runBuild();
    writeJson(join(outputDir, 'build_report.json'), build);
    reports.push('build_report.json');
    if (!build.ok) blockers.push('npm run build failed');
  }

  let rendered = null;
  if (blockers.length === 0) {
    rendered = checkRenderedComparisonBatch({
      selectedSlugs: manifest.selected_slugs || [],
      factsBySlug: factsArrayToMap(preflight.factsPayload.comparisons || []),
    });
    writeJson(join(outputDir, 'rendered_report.json'), rendered);
    reports.push('rendered_report.json');
    if (!rendered.ok) blockers.push(...rendered.blockers.map((blocker) => `${blocker.slug}: ${blocker.type}`));
  }

  if (blockers.length === 0) {
    const packet = runReviewPacket({ manifestPath, outputDir, base });
    writeJson(join(outputDir, 'review_packet_command_report.json'), packet);
    reports.push('review_packet_command_report.json');
    if (packet.ok) {
      reports.push('review_packet.json', 'review_packet.md');
    } else {
      blockers.push('review packet generation failed');
    }
  }

  const status = statusFor({
    manifest,
    phase: 'check',
    ok: blockers.length === 0,
    blockers,
    reports,
  });
  writeJson(statusPath, status);
  return status;
}

const manifestPath = argValue('--manifest');
const mode = argValue('--mode');
const base = argValue('--base', 'HEAD');
if (!manifestPath || !existsSync(manifestPath)) {
  console.error('Missing --manifest <manifest.json>');
  process.exit(2);
}
if (!['preflight', 'check'].includes(mode)) {
  console.error('Missing or invalid --mode <preflight|check>');
  process.exit(2);
}

const manifest = readJson(manifestPath);
const outputDir = argValue('--output-dir', dirname(manifestPath));
const statusPath = argValue('--status', join(outputDir, 'batch_status.json'));
mkdirSync(outputDir, { recursive: true });

const status = mode === 'preflight'
  ? runPreflight({ manifest, outputDir, statusPath }).status
  : runCheck({ manifestPath, manifest, outputDir, statusPath, base });

console.log(JSON.stringify(status, null, 2));
if (!status.ok) {
  process.exitCode = 1;
}
