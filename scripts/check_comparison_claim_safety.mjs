#!/usr/bin/env node
import { writeFileSync } from 'node:fs';
import {
  checkComparisonClaimSafety,
  factsArrayToMap,
  readJson,
  selectComparisonsForManifest,
} from './lib/comparison_batch_utils.mjs';

function argValue(name, fallback) {
  const index = process.argv.indexOf(name);
  return index === -1 ? fallback : process.argv[index + 1];
}

const manifestPath = argValue('--manifest');
const factsPath = argValue('--facts');
const outputPath = argValue('--output');
if (!manifestPath || !factsPath) {
  console.error('Missing --manifest <manifest.json> or --facts <facts.json>');
  process.exit(2);
}

const manifest = readJson(manifestPath);
const factsPayload = readJson(factsPath);
const selected = selectComparisonsForManifest({
  allComparisons: readJson('src/content/comparisons.json'),
  selectedSlugs: manifest.selected_slugs || [],
});
const factsBySlug = factsArrayToMap(factsPayload.comparisons || []);
const result = checkComparisonClaimSafety({
  comparisons: selected.comparisons,
  factsBySlug,
});
result.selection_blockers = selected.blockers;
result.ok = result.ok && selected.blockers.length === 0;

const body = `${JSON.stringify(result, null, 2)}\n`;
if (outputPath) {
  writeFileSync(outputPath, body);
} else {
  process.stdout.write(body);
}
if (!result.ok) {
  process.exitCode = 1;
}
