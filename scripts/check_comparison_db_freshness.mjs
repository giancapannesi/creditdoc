#!/usr/bin/env node
import { checkComparisonDbFreshness } from './lib/comparison_batch_utils.mjs';

function argValue(name, fallback) {
  const index = process.argv.indexOf(name);
  return index === -1 ? fallback : process.argv[index + 1];
}

const result = checkComparisonDbFreshness({
  comparisonsPath: argValue('--comparisons', 'src/content/comparisons.json'),
  dbPath: argValue('--db', 'data/creditdoc.db'),
});

console.log(JSON.stringify(result, null, 2));
if (result.ok) {
  console.log('OK comparison DB matches src/content/comparisons.json');
} else {
  console.error('STALE comparison DB mismatch detected');
  process.exitCode = 1;
}
