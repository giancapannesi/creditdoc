#!/usr/bin/env node
import { join, dirname } from 'node:path';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import {
  checkLiveComparisonBatch,
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
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
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
    ok: blockers.length === 0,
    missing_comparison_slugs: selected.missingComparisonSlugs,
    missing_lender_slugs: missingLenderSlugs,
    blockers,
    comparisons: selected.comparisons.map((comparison) => extractComparisonSourceFacts({ comparison, lendersBySlug })),
  };
}

const manifestPath = argValue('--manifest');
const factsPath = argValue('--facts');
const outputDir = argValue('--output-dir', manifestPath ? dirname(manifestPath) : '.');
const outputPath = argValue('--output', join(outputDir, 'live_check_report.json'));
const baseUrl = argValue('--base-url', 'https://www.creditdoc.co');

if (!manifestPath || !existsSync(manifestPath)) {
  console.error('Missing --manifest <manifest.json>');
  process.exit(2);
}

const manifest = readJson(manifestPath);
const factsPayload = factsPath && existsSync(factsPath) ? readJson(factsPath) : buildFactsPayload(manifest);
const blockers = [...(factsPayload.blockers || [])];
const live = await checkLiveComparisonBatch({
  selectedSlugs: manifest.selected_slugs || [],
  factsBySlug: factsArrayToMap(factsPayload.comparisons || []),
  baseUrl,
});
const report = {
  ...live,
  batch_id: manifest.batch_id || '',
  ok: blockers.length === 0 && live.ok,
  source_fact_blockers: blockers,
  blockers: [
    ...blockers.map((blocker) => ({ type: 'source_fact_blocker', message: blocker })),
    ...live.blockers,
  ],
};

writeJson(outputPath, report);
console.log(JSON.stringify(report, null, 2));
if (!report.ok) {
  process.exitCode = 1;
}
