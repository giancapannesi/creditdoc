#!/usr/bin/env node
import { writeFileSync } from 'node:fs';
import {
  checkRenderedComparisonBatch,
  factsArrayToMap,
  readJson,
} from './lib/comparison_batch_utils.mjs';

function argValue(name, fallback) {
  const index = process.argv.indexOf(name);
  return index === -1 ? fallback : process.argv[index + 1];
}

const manifestPath = argValue('--manifest');
const factsPath = argValue('--facts');
const distDir = argValue('--dist', 'dist');
const outputPath = argValue('--output');
if (!manifestPath || !factsPath) {
  console.error('Missing --manifest <manifest.json> or --facts <facts.json>');
  process.exit(2);
}

const manifest = readJson(manifestPath);
const factsPayload = readJson(factsPath);
const result = checkRenderedComparisonBatch({
  distDir,
  selectedSlugs: manifest.selected_slugs || [],
  factsBySlug: factsArrayToMap(factsPayload.comparisons || []),
});

const body = `${JSON.stringify(result, null, 2)}\n`;
if (outputPath) {
  writeFileSync(outputPath, body);
} else {
  process.stdout.write(body);
}
if (!result.ok) {
  process.exitCode = 1;
}
