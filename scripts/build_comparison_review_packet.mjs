#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import {
  buildComparisonReviewPacket,
  readJson,
} from './lib/comparison_batch_utils.mjs';

function argValue(name, fallback) {
  const index = process.argv.indexOf(name);
  return index === -1 ? fallback : process.argv[index + 1];
}

function optionalJson(path, fallback = {}) {
  return path && existsSync(path) ? readJson(path) : fallback;
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

function markdownFor(packet) {
  const lines = [
    `# Comparison Review Packet: ${packet.batch_id || 'unknown-batch'}`,
    '',
    `Group: ${packet.group || 'unknown'}`,
    `Selected rows: ${packet.selected_count}`,
    `Generated: ${packet.generated_at}`,
    '',
  ];

  for (const row of packet.rows) {
    lines.push(`## ${row.slug}`);
    lines.push('');
    lines.push(`Lenders: ${row.lender_a || 'unknown'} vs ${row.lender_b || 'unknown'}`);
    lines.push(`Changed fields: ${row.changed_fields.length ? row.changed_fields.join(', ') : 'none'}`);
    lines.push('');
    lines.push('Changed field values:');
    if (row.changed_fields.length === 0) {
      lines.push('- none');
    } else {
      for (const field of row.changed_fields) {
        const values = row.before_after[field];
        lines.push(`- ${field}`);
        lines.push(`  - before: ${JSON.stringify(values.before)}`);
        lines.push(`  - after: ${JSON.stringify(values.after)}`);
      }
    }
    lines.push('');
    lines.push('Allowed facts:');
    lines.push('```json');
    lines.push(JSON.stringify(row.allowed_facts, null, 2));
    lines.push('```');
    lines.push('');
    lines.push('Scanner findings:');
    lines.push('```json');
    lines.push(JSON.stringify(row.scanner_findings, null, 2));
    lines.push('```');
    lines.push('');
    lines.push('Reviewer questions:');
    for (const question of row.reviewer_questions) {
      lines.push(`- ${question}`);
    }
    lines.push('');
  }

  return `${lines.join('\n')}\n`;
}

const manifestPath = argValue('--manifest');
const factsPath = argValue('--facts');
const claimReportPath = argValue('--claim-report');
const renderedReportPath = argValue('--rendered-report');
const outputDir = argValue('--output-dir', '.');
const base = argValue('--base', 'HEAD');

if (!manifestPath || !existsSync(manifestPath)) {
  console.error('Missing --manifest <manifest.json>');
  process.exit(2);
}

const packet = buildComparisonReviewPacket({
  manifest: readJson(manifestPath),
  baseRows: loadBaseRows(base),
  currentRows: readJson('src/content/comparisons.json'),
  factsPayload: optionalJson(factsPath, { comparisons: [] }),
  claimReport: optionalJson(claimReportPath),
  renderedReport: optionalJson(renderedReportPath),
});

const jsonPath = join(outputDir, 'review_packet.json');
const markdownPath = join(outputDir, 'review_packet.md');
mkdirSync(dirname(jsonPath), { recursive: true });
writeFileSync(jsonPath, `${JSON.stringify(packet, null, 2)}\n`);
writeFileSync(markdownPath, markdownFor(packet));

console.log(JSON.stringify({
  ok: true,
  batch_id: packet.batch_id,
  selected_count: packet.selected_count,
  outputs: [jsonPath, markdownPath],
}, null, 2));
