#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const ROOT = '/srv/BusinessOps';
const CREDITDOC = `${ROOT}/creditdoc`;
const CALENDAR_PATH = `${CREDITDOC}/automation/two_week_seo_calendar.json`;
const OUTPUT_DIR = `${CREDITDOC}/SEO/two-week-action-calendar`;
const FORCE_QUEUE_PATH = `${ROOT}/data/creditdoc_force_google_indexing_urls.json`;
const LOG_JSONL = `${ROOT}/logs/creditdoc_two_week_seo_calendar_runs.jsonl`;

function parseArgs(argv) {
  const args = { date: null, dryRun: false, list: false };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--dry-run') args.dryRun = true;
    else if (arg === '--list') args.list = true;
    else if (arg === '--date') args.date = argv[++i];
    else if (arg.startsWith('--date=')) args.date = arg.slice('--date='.length);
  }
  return args;
}

function todayUtc() {
  return new Date().toISOString().slice(0, 10);
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function normalizeUrl(url) {
  if (typeof url !== 'string') return null;
  let out = url.trim();
  if (!out) return null;
  out = out.replace('https://creditdoc.co/', 'https://www.creditdoc.co/');
  if (!out.startsWith('https://www.creditdoc.co/')) return null;
  if (!out.endsWith('/')) out = `${out}/`;
  return out;
}

function readForceQueue() {
  if (!fs.existsSync(FORCE_QUEUE_PATH)) return [];
  try {
    const payload = readJson(FORCE_QUEUE_PATH);
    const urls = Array.isArray(payload) ? payload : payload.urls;
    if (!Array.isArray(urls)) return [];
    return [...new Set(urls.map(normalizeUrl).filter(Boolean))];
  } catch {
    return [];
  }
}

function writeForceQueue(urls, dryRun) {
  const normalized = [...new Set(urls.map(normalizeUrl).filter(Boolean))].sort();
  const payload = {
    site: 'creditdoc',
    purpose: 'One-shot forced Google Indexing API priority queue. Accepted URLs are removed by creditdoc_priority_indexing.py.',
    updated: new Date().toISOString(),
    updated_by: 'creditdoc_two_week_seo_runner',
    urls: normalized,
  };
  if (!dryRun) {
    ensureDir(path.dirname(FORCE_QUEUE_PATH));
    fs.writeFileSync(FORCE_QUEUE_PATH, `${JSON.stringify(payload, null, 2)}\n`);
  }
  return normalized.length;
}

function forcePriorityUrls(calendar, dryRun) {
  const existing = readForceQueue();
  const additions = calendar.priority_urls.map(normalizeUrl).filter(Boolean);
  const merged = [...new Set([...existing, ...additions])];
  const count = writeForceQueue(merged, dryRun);
  return {
    action: 'force_priority_urls',
    ok: true,
    detail: `${count} URL(s) in forced priority indexing queue`,
  };
}

function runBuildChecks(dryRun) {
  if (dryRun) {
    return { action: 'run_build_checks', ok: true, detail: 'dry-run skipped npm run build' };
  }
  const result = spawnSync('npm', ['run', 'build'], {
    cwd: CREDITDOC,
    encoding: 'utf8',
    timeout: 1000 * 60 * 8,
  });
  const logPath = `${ROOT}/logs/creditdoc_two_week_seo_build_${new Date().toISOString().replace(/[:.]/g, '-')}.log`;
  ensureDir(path.dirname(logPath));
  fs.writeFileSync(logPath, `${result.stdout || ''}\n${result.stderr || ''}`);
  return {
    action: 'run_build_checks',
    ok: result.status === 0,
    detail: `exit ${result.status}; log ${logPath}`,
  };
}

function auditAnswerMeta(dryRun) {
  if (dryRun) {
    return { action: 'audit_answer_meta', ok: true, detail: 'dry-run skipped answer meta audit' };
  }
  const result = spawnSync('node', ['scripts/creditdoc_answer_meta_audit.mjs', '--limit', '100'], {
    cwd: CREDITDOC,
    encoding: 'utf8',
    timeout: 1000 * 60 * 3,
  });
  const logPath = `${ROOT}/logs/creditdoc_answer_meta_audit_${new Date().toISOString().replace(/[:.]/g, '-')}.log`;
  ensureDir(path.dirname(logPath));
  fs.writeFileSync(logPath, `${result.stdout || ''}\n${result.stderr || ''}`);
  let detail = `exit ${result.status}; report ${CREDITDOC}/reports/answer-seo-meta-audit.json; log ${logPath}`;
  try {
    const summary = JSON.parse(result.stdout || '{}');
    detail = `missing_primary_phrase=${summary.missing_primary_phrase}, needs_meta_review=${summary.needs_meta_review}; report ${CREDITDOC}/reports/answer-seo-meta-audit.json`;
  } catch {
    // Keep the raw exit/log detail if stdout is not JSON.
  }
  return {
    action: 'audit_answer_meta',
    ok: result.status === 0,
    detail,
  };
}

function auditAiIngestion(dryRun) {
  if (dryRun) {
    return { action: 'audit_ai_ingestion', ok: true, detail: 'dry-run skipped AI ingestion contract check' };
  }
  const result = spawnSync('node', ['scripts/check_ai_ingestion_contract.mjs'], {
    cwd: CREDITDOC,
    encoding: 'utf8',
    timeout: 1000 * 60,
  });
  const detail = result.status === 0
    ? (result.stdout || '').trim()
    : `exit ${result.status}; ${(result.stderr || result.stdout || '').trim()}`;
  return {
    action: 'audit_ai_ingestion',
    ok: result.status === 0,
    detail,
  };
}

function writeDailyBrief(calendar, job, actionResults, dryRun) {
  ensureDir(OUTPUT_DIR);
  const file = `${OUTPUT_DIR}/${job.date}-day-${String(job.day).padStart(2, '0')}.md`;
  const lines = [
    `# ${job.date} - Day ${job.day}: ${job.title}`,
    '',
    `Type: ${job.type}`,
    `Source plan: ${calendar.source_plan}`,
    `Generated: ${new Date().toISOString()}`,
    dryRun ? 'Mode: dry-run' : 'Mode: cron/auto',
    '',
    '## Tasks',
    '',
    ...job.tasks.map((task) => `- [ ] ${task}`),
    '',
    '## Auto Actions',
    '',
    ...actionResults.map((result) => `- ${result.ok ? 'PASS' : 'FAIL'} ${result.action}: ${result.detail}`),
    '',
    '## Priority URLs',
    '',
    ...calendar.priority_urls.map((url) => `- ${url}`),
    '',
    '## Operator Notes',
    '',
    '- Cron can create briefs, run checks, and maintain indexing queues.',
    '- Page creation, copy edits, and internal-link changes still need repository edits and a build/commit.',
    '- Do not rewrite pages blindly; use GSC/SE Ranking evidence from the plan.',
  ];
  if (!dryRun) fs.writeFileSync(file, `${lines.join('\n')}\n`);
  return { action: 'write_daily_brief', ok: true, detail: file };
}

function appendRunLog(entry, dryRun) {
  if (dryRun) return;
  ensureDir(path.dirname(LOG_JSONL));
  fs.appendFileSync(LOG_JSONL, `${JSON.stringify(entry)}\n`);
}

function main() {
  const args = parseArgs(process.argv);
  const calendar = readJson(CALENDAR_PATH);
  const runDate = args.date || todayUtc();

  if (args.list) {
    for (const job of calendar.jobs) {
      console.log(`${job.date} day ${job.day}: ${job.title} [${job.type}]`);
    }
    return;
  }

  const job = calendar.jobs.find((item) => item.date === runDate);
  if (!job) {
    const entry = {
      run_date: runDate,
      generated_at: new Date().toISOString(),
      ok: true,
      skipped: true,
      reason: 'No two-week SEO calendar job for date',
    };
    console.log(JSON.stringify(entry));
    appendRunLog(entry, args.dryRun);
    return;
  }

  const results = [];
  for (const action of job.auto_actions) {
    if (action === 'force_priority_urls') results.push(forcePriorityUrls(calendar, args.dryRun));
    else if (action === 'run_build_checks') results.push(runBuildChecks(args.dryRun));
    else if (action === 'audit_answer_meta') results.push(auditAnswerMeta(args.dryRun));
    else if (action === 'audit_ai_ingestion') results.push(auditAiIngestion(args.dryRun));
  }
  results.unshift(writeDailyBrief(calendar, job, results, args.dryRun));

  const ok = results.every((result) => result.ok);
  const entry = {
    run_date: runDate,
    generated_at: new Date().toISOString(),
    job: { day: job.day, title: job.title, type: job.type },
    ok,
    results,
  };
  console.log(JSON.stringify(entry, null, 2));
  appendRunLog(entry, args.dryRun);
  process.exit(ok ? 0 : 1);
}

main();
