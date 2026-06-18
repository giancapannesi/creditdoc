#!/usr/bin/env node
import { writeFileSync } from 'node:fs';
import {
  extractComparisonSourceFacts,
  loadLendersForComparisons,
  readJson,
  selectComparisonsForManifest,
} from './lib/comparison_batch_utils.mjs';

function argValue(name, fallback) {
  const index = process.argv.indexOf(name);
  return index === -1 ? fallback : process.argv[index + 1];
}

const manifestPath = argValue('--manifest');
const outputPath = argValue('--output');
if (!manifestPath) {
  console.error('Missing --manifest <manifest.json>');
  process.exit(2);
}

const manifest = readJson(manifestPath);
const allComparisons = readJson('src/content/comparisons.json');
const selectedResult = selectComparisonsForManifest({
  allComparisons,
  selectedSlugs: manifest.selected_slugs || [],
});
const { lendersBySlug, missingLenderSlugs, blockers: lenderBlockers } = loadLendersForComparisons({
  comparisons: selectedResult.comparisons,
});
const blockers = [...selectedResult.blockers, ...lenderBlockers].sort();
const facts = {
  batch_id: manifest.batch_id || '',
  generated_at: new Date().toISOString(),
  ok: blockers.length === 0,
  missing_comparison_slugs: selectedResult.missingComparisonSlugs,
  missing_lender_slugs: missingLenderSlugs,
  blockers,
  comparisons: selectedResult.comparisons.map((comparison) => extractComparisonSourceFacts({ comparison, lendersBySlug })),
};

const body = `${JSON.stringify(facts, null, 2)}\n`;
if (outputPath) {
  writeFileSync(outputPath, body);
} else {
  process.stdout.write(body);
}

if (blockers.length > 0) {
  process.exitCode = 1;
}
