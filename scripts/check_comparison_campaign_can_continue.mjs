#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import {
  checkComparisonCampaignCanContinue,
  readJson,
} from './lib/comparison_batch_utils.mjs';

function argValue(name, fallback) {
  const index = process.argv.indexOf(name);
  return index === -1 ? fallback : process.argv[index + 1];
}

function optionalJson(path, fallback = null) {
  return path && existsSync(path) ? readJson(path) : fallback;
}

function readGitStatus(path) {
  if (path && existsSync(path)) return readFileSync(path, 'utf8');
  return execFileSync('git', ['status', '--short', '--untracked-files=all'], { encoding: 'utf8' });
}

const campaignReportPath = argValue('--campaign-report');
const latestBatchDir = argValue('--latest-batch-dir');
const gitStatusFile = argValue('--git-status-file');

if (!campaignReportPath || !existsSync(campaignReportPath)) {
  console.error('Missing --campaign-report <campaign_report.json>');
  process.exit(2);
}
if (!latestBatchDir || !existsSync(latestBatchDir)) {
  console.error('Missing --latest-batch-dir <batch-report-dir>');
  process.exit(2);
}

const result = checkComparisonCampaignCanContinue({
  campaignReport: readJson(campaignReportPath),
  latestBatchStatus: optionalJson(`${latestBatchDir}/batch_status.json`),
  finalCheckerResult: optionalJson(`${latestBatchDir}/final_checker_result.json`),
  liveReport: optionalJson(`${latestBatchDir}/live_check_report.json`),
  gitStatus: readGitStatus(gitStatusFile),
});

console.log(JSON.stringify(result, null, 2));
if (!result.ok) {
  process.exitCode = 1;
}
