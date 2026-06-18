#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { compareComparisonBatchScope, readJson } from './lib/comparison_batch_utils.mjs';

function argValue(name, fallback) {
  const index = process.argv.indexOf(name);
  return index === -1 ? fallback : process.argv[index + 1];
}

const base = argValue('--base', 'HEAD');
const manifestPath = argValue('--manifest');
if (!manifestPath || !existsSync(manifestPath)) {
  console.error('Missing --manifest <manifest.json>');
  process.exit(2);
}

let baseRows;
try {
  baseRows = JSON.parse(execFileSync('git', ['show', `${base}:src/content/comparisons.json`], {
    encoding: 'utf8',
    maxBuffer: 1024 * 1024 * 50,
  }));
} catch {
  baseRows = readJson('src/content/comparisons.json');
}

const result = compareComparisonBatchScope({
  baseRows,
  currentRows: readJson('src/content/comparisons.json'),
  manifest: readJson(manifestPath),
});

console.log(JSON.stringify(result, null, 2));
if (result.ok) {
  if (result.changedSlugs.length === 0) {
    console.log('OK no comparison changes');
  } else {
    console.log('OK comparison batch scope matches manifest');
  }
} else {
  console.error('Comparison batch scope check failed');
  process.exitCode = 1;
}
