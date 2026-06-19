#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import {
  buildComparisonCampaignReport,
  readJson,
} from './lib/comparison_batch_utils.mjs';

function valuesFor(name) {
  const values = [];
  for (let index = 0; index < process.argv.length; index += 1) {
    if (process.argv[index] === name && process.argv[index + 1]) {
      values.push(process.argv[index + 1]);
    }
  }
  return values;
}

function argValue(name, fallback) {
  const values = valuesFor(name);
  return values.length > 0 ? values.at(-1) : fallback;
}

function optionalJson(path, fallback = null) {
  return path && existsSync(path) ? readJson(path) : fallback;
}

function readGitStatus(path) {
  if (path && existsSync(path)) return readFileSync(path, 'utf8');
  return execFileSync('git', ['status', '--short', '--untracked-files=all'], { encoding: 'utf8' });
}

function markdownFor(report) {
  const lines = [
    `# Comparison Campaign Report: ${report.campaign_id || 'unknown-campaign'}`,
    '',
    `Generated: ${report.generated_at}`,
    `Progress: ${report.progress.completed_batches} of ${report.progress.planned_batches}`,
    `Selected pages: ${report.totals.selected_pages}`,
    `Changed pages: ${report.totals.changed_pages}`,
    `Skipped pages: ${report.totals.skipped_pages}`,
    `Final checker passes: ${report.totals.final_checker_passes}`,
    `Live check passes: ${report.totals.live_check_passes}`,
    `Can start next batch: ${report.can_start_next_batch ? 'yes' : 'no'}`,
    '',
    'Completed batches:',
    ...(report.progress.completed_batch_ids.length ? report.progress.completed_batch_ids.map((id) => `- ${id}`) : ['- none']),
    '',
    'Blockers:',
    ...(report.blockers.length ? report.blockers.map((blocker) => `- ${blocker}`) : ['- none']),
    '',
    'Repo status:',
    '```',
    report.git_status.trim() || 'clean',
    '```',
    '',
  ];
  return `${lines.join('\n')}\n`;
}

const campaignPath = argValue('--campaign');
const outputDir = argValue('--output-dir', campaignPath ? dirname(campaignPath) : '.');
const gitStatusFile = argValue('--git-status-file');
const batchDirs = valuesFor('--batch-dir');

if (!campaignPath || !existsSync(campaignPath)) {
  console.error('Missing --campaign <campaign_manifest.json>');
  process.exit(2);
}

const batchManifests = [];
const batchStatuses = [];
const finalCheckerResults = [];
const liveReports = [];
for (const batchDir of batchDirs) {
  const manifest = optionalJson(join(batchDir, 'manifest.json'));
  const status = optionalJson(join(batchDir, 'batch_status.json'));
  const finalChecker = optionalJson(join(batchDir, 'final_checker_result.json'));
  const liveReport = optionalJson(join(batchDir, 'live_check_report.json'));
  if (manifest) batchManifests.push(manifest);
  if (status) batchStatuses.push(status);
  if (finalChecker) finalCheckerResults.push(finalChecker);
  if (liveReport) liveReports.push(liveReport);
}

const report = buildComparisonCampaignReport({
  campaignManifest: readJson(campaignPath),
  batchManifests,
  batchStatuses,
  finalCheckerResults,
  liveReports,
  gitStatus: readGitStatus(gitStatusFile),
});

mkdirSync(outputDir, { recursive: true });
writeFileSync(join(outputDir, 'campaign_report.json'), `${JSON.stringify(report, null, 2)}\n`);
writeFileSync(join(outputDir, 'campaign_report.md'), markdownFor(report));
console.log(JSON.stringify({
  ok: report.ok,
  campaign_id: report.campaign_id,
  can_start_next_batch: report.can_start_next_batch,
  blockers: report.blockers,
  outputs: [join(outputDir, 'campaign_report.json'), join(outputDir, 'campaign_report.md')],
}, null, 2));
if (!report.ok) {
  process.exitCode = 1;
}
