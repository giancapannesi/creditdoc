#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const ROOT = '/srv/BusinessOps';
const SECRETS_FILE = `${ROOT}/tools/.linkedin.env`;
const QUEUE_FILE = `${ROOT}/data/creditdoc_linkedin_queue.json`;
const STATE_FILE = `${ROOT}/data/creditdoc_linkedin_state.json`;
const LOG_FILE = `${ROOT}/logs/creditdoc_linkedin_posts.jsonl`;
const DEFAULT_VERSION = '202606';
const WEEKLY_CAP = 2;
const DEFAULT_REDIRECT_URI = 'https://www.creditdoc.co/linkedin-oauth-callback/';
const DEFAULT_SCOPES = ['w_organization_social', 'r_organization_social'];

const CAMPAIGNS = [
  {
    slug: 'commercial-loan-calculator',
    url: 'https://www.creditdoc.co/tools/commercial-loan-calculator/',
    cadenceSlot: 'tool',
    title: 'Commercial loan calculator',
    angle: 'Commercial mortgages can look simple until balloon maturities, closing costs, and debt-service coverage enter the picture.',
    cta: 'Use the free CreditDoc commercial loan calculator before comparing lender terms.',
    hashtags: ['#SmallBusinessFinance', '#CommercialLoans', '#BusinessFunding'],
  },
  {
    slug: 'business-line-of-credit-calculator',
    url: 'https://www.creditdoc.co/tools/business-line-of-credit-calculator/',
    cadenceSlot: 'tool',
    title: 'Business line of credit calculator',
    angle: 'A business line of credit is flexible, but draw fees, unused line fees, APR, and repayment timing can change the real cost.',
    cta: 'Use the free CreditDoc business line of credit calculator to model a draw before applying.',
    hashtags: ['#BusinessLineOfCredit', '#SmallBusiness', '#WorkingCapital'],
  },
  {
    slug: 'sba-loan-calculator',
    url: 'https://www.creditdoc.co/tools/sba-loan-calculator/',
    cadenceSlot: 'tool',
    title: 'SBA loan calculator',
    angle: 'SBA loans can offer longer terms, but the payment still depends on loan amount, rate, term, and fee treatment.',
    cta: 'Use the CreditDoc SBA loan calculator to estimate payment pressure before speaking with a lender.',
    hashtags: ['#SBALoans', '#SmallBusinessFinance', '#BusinessLoans'],
  },
  {
    slug: 'business-loan-readiness-quiz',
    url: 'https://www.creditdoc.co/tools/business-loan-readiness-quiz/',
    cadenceSlot: 'education',
    title: 'Business loan readiness quiz',
    angle: 'Before a business owner applies, it helps to know whether revenue, documents, time in business, and credit profile match the likely funding path.',
    cta: 'CreditDoc built a free business loan readiness quiz for that first-pass review.',
    hashtags: ['#BusinessLoans', '#Entrepreneurs', '#SmallBusiness'],
  },
  {
    slug: 'best-business-lines-of-credit',
    url: 'https://www.creditdoc.co/best/best-business-lines-of-credit/',
    cadenceSlot: 'education',
    title: 'Business lines of credit research',
    angle: 'Business lines of credit are not one product. Banks, online lenders, secured lines, and startup options can behave very differently.',
    cta: 'CreditDoc’s research page compares business line of credit options and links to planning tools.',
    hashtags: ['#BusinessCredit', '#WorkingCapital', '#SmallBusinessFinance'],
  },
  {
    slug: 'best-sba-loans',
    url: 'https://www.creditdoc.co/best/best-sba-loans/',
    cadenceSlot: 'education',
    title: 'SBA loan research',
    angle: 'SBA funding is often described as one category, but 7(a), 504, Express, and microloan paths solve different problems.',
    cta: 'CreditDoc’s SBA loan research page gives borrowers a clearer starting point.',
    hashtags: ['#SBALoans', '#BusinessFunding', '#SmallBusiness'],
  },
];

function usage() {
  console.log(`Usage:
  node scripts/creditdoc_linkedin_manager.mjs auth-check
  node scripts/creditdoc_linkedin_manager.mjs auth-url
  node scripts/creditdoc_linkedin_manager.mjs exchange-code <code>
  node scripts/creditdoc_linkedin_manager.mjs list-organizations
  node scripts/creditdoc_linkedin_manager.mjs set-organization <urn:li:organization:id>
  node scripts/creditdoc_linkedin_manager.mjs draft-week [--date YYYY-MM-DD]
  node scripts/creditdoc_linkedin_manager.mjs status
  node scripts/creditdoc_linkedin_manager.mjs approve <draft-id>
  node scripts/creditdoc_linkedin_manager.mjs publish-approved [--dry-run]

Safety:
  - Draft generation is automatic.
  - Publishing requires status=approved.
  - Publisher refuses more than ${WEEKLY_CAP} live posts per UTC ISO week.
`);
}

function ensureDir(file) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
}

function loadEnv() {
  const env = {};
  if (!fs.existsSync(SECRETS_FILE)) return env;
  for (const line of fs.readFileSync(SECRETS_FILE, 'utf8').split(/\r?\n/)) {
    if (!line || line.trim().startsWith('#') || !line.includes('=')) continue;
    const [key, ...rest] = line.split('=');
    env[key.trim()] = rest.join('=').trim().replace(/^["']|["']$/g, '');
  }
  return env;
}

function saveEnv(updates) {
  const existing = loadEnv();
  const merged = { ...existing, ...updates };
  const orderedKeys = [
    'LINKEDIN_CLIENT_ID',
    'LINKEDIN_API_KEY',
    'LINKEDIN_CLIENT_SECRET',
    'LINKEDIN_REDIRECT_URI',
    'LINKEDIN_ACCESS_TOKEN',
    'LINKEDIN_EXPIRES_IN',
    'LINKEDIN_ACCESS_TOKEN_SAVED_AT',
    'LINKEDIN_ORGANIZATION_URN',
    'LINKEDIN_VERSION',
  ];
  const keys = [...orderedKeys, ...Object.keys(merged).filter((key) => !orderedKeys.includes(key)).sort()];
  const lines = keys
    .filter((key) => merged[key] !== undefined && merged[key] !== null && String(merged[key]).length > 0)
    .map((key) => `${key}=${merged[key]}`);
  ensureDir(SECRETS_FILE);
  fs.writeFileSync(SECRETS_FILE, `${lines.join('\n')}\n`, { mode: 0o600 });
  fs.chmodSync(SECRETS_FILE, 0o600);
}

function readJson(file, fallback) {
  if (!fs.existsSync(file)) return fallback;
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return fallback;
  }
}

function writeJson(file, payload) {
  ensureDir(file);
  fs.writeFileSync(file, `${JSON.stringify(payload, null, 2)}\n`);
}

function today(dateArg) {
  return dateArg || new Date().toISOString().slice(0, 10);
}

function isoWeek(dateString) {
  const date = new Date(`${dateString}T00:00:00Z`);
  const day = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((date - yearStart) / 86400000) + 1) / 7);
  return `${date.getUTCFullYear()}-W${String(week).padStart(2, '0')}`;
}

function addDays(dateString, days) {
  const date = new Date(`${dateString}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function nextWeekday(dateString, targetDay) {
  const date = new Date(`${dateString}T00:00:00Z`);
  const current = date.getUTCDay();
  const delta = (targetDay - current + 7) % 7;
  return addDays(dateString, delta);
}

function makePost(campaign) {
  return [
    campaign.angle,
    '',
    campaign.cta,
    '',
    campaign.url,
    '',
    campaign.hashtags.join(' '),
  ].join('\n');
}

function loadQueue() {
  return readJson(QUEUE_FILE, { updated: null, drafts: [] });
}

function saveQueue(queue) {
  queue.updated = new Date().toISOString();
  writeJson(QUEUE_FILE, queue);
}

function loadState() {
  return readJson(STATE_FILE, { published: [] });
}

function saveState(state) {
  writeJson(STATE_FILE, state);
}

function existingDraftKeys(queue) {
  return new Set(queue.drafts.map((draft) => `${draft.scheduled_date}:${draft.campaign_slug}`));
}

function buildDraft(campaign, scheduledDate, slot) {
  const id = `cd-li-${scheduledDate}-${campaign.slug}`;
  return {
    id,
    campaign_slug: campaign.slug,
    title: campaign.title,
    target_url: campaign.url,
    scheduled_date: scheduledDate,
    slot,
    status: 'draft',
    created_at: new Date().toISOString(),
    approved_at: null,
    published_at: null,
    linkedin_post_urn: null,
    commentary: makePost(campaign),
  };
}

function draftWeek(dateArg) {
  const base = today(dateArg);
  const tuesday = nextWeekday(base, 2);
  const friday = nextWeekday(base, 5);
  const queue = loadQueue();
  const keys = existingDraftKeys(queue);

  const education = CAMPAIGNS.filter((item) => item.cadenceSlot === 'education');
  const tools = CAMPAIGNS.filter((item) => item.cadenceSlot === 'tool');
  const weekSeed = Number(isoWeek(base).split('W')[1]) || 1;
  const picks = [
    { campaign: education[weekSeed % education.length], date: tuesday, slot: 'education' },
    { campaign: tools[weekSeed % tools.length], date: friday, slot: 'tool' },
  ];

  const added = [];
  for (const pick of picks) {
    const key = `${pick.date}:${pick.campaign.slug}`;
    if (keys.has(key)) continue;
    const draft = buildDraft(pick.campaign, pick.date, pick.slot);
    queue.drafts.push(draft);
    added.push(draft.id);
  }
  queue.drafts.sort((a, b) => `${a.scheduled_date}:${a.id}`.localeCompare(`${b.scheduled_date}:${b.id}`));
  saveQueue(queue);
  console.log(JSON.stringify({ ok: true, added, queue_file: QUEUE_FILE }, null, 2));
}

function status() {
  const env = loadEnv();
  const queue = loadQueue();
  const state = loadState();
  const byStatus = queue.drafts.reduce((acc, draft) => {
    acc[draft.status] = (acc[draft.status] || 0) + 1;
    return acc;
  }, {});
  console.log(JSON.stringify({
    ok: true,
    secrets_file: SECRETS_FILE,
    stored_secret_keys: Object.keys(env).sort(),
    queue_file: QUEUE_FILE,
    state_file: STATE_FILE,
    drafts_by_status: byStatus,
    next_drafts: queue.drafts.filter((draft) => draft.status !== 'published').slice(0, 6).map((draft) => ({
      id: draft.id,
      date: draft.scheduled_date,
      status: draft.status,
      title: draft.title,
      url: draft.target_url,
    })),
    published_count: state.published.length,
  }, null, 2));
}

function approve(id) {
  const queue = loadQueue();
  const draft = queue.drafts.find((item) => item.id === id);
  if (!draft) {
    console.error(`Draft not found: ${id}`);
    process.exit(1);
  }
  if (draft.status === 'published') {
    console.error(`Draft already published: ${id}`);
    process.exit(1);
  }
  draft.status = 'approved';
  draft.approved_at = new Date().toISOString();
  saveQueue(queue);
  console.log(JSON.stringify({ ok: true, approved: id }, null, 2));
}

function redact(value) {
  if (!value) return false;
  return `${String(value).slice(0, 4)}...${String(value).slice(-4)}`;
}

async function authCheck() {
  const env = loadEnv();
  const accessToken = env.LINKEDIN_ACCESS_TOKEN || '';
  const clientId = env.LINKEDIN_CLIENT_ID || '';
  const clientSecret = env.LINKEDIN_CLIENT_SECRET || env.LINKEDIN_API_KEY || '';
  const orgUrn = env.LINKEDIN_ORGANIZATION_URN || '';
  const report = {
    ok: true,
    has_client_id: Boolean(clientId),
    has_client_secret_or_api_key: Boolean(clientSecret),
    has_access_token: Boolean(accessToken),
    has_organization_urn: Boolean(orgUrn),
    client_id_preview: redact(clientId),
    organization_urn: orgUrn || null,
    api_status: 'not_checked',
  };

  if (!accessToken) {
    report.ok = false;
    report.api_status = 'missing LINKEDIN_ACCESS_TOKEN; OAuth user/admin token is required for API posting';
    console.log(JSON.stringify(report, null, 2));
    process.exit(1);
  }

  const response = await fetch('https://api.linkedin.com/v2/userinfo', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  report.api_status = `${response.status} ${response.statusText}`;
  report.ok = response.ok;
  console.log(JSON.stringify(report, null, 2));
  process.exit(response.ok ? 0 : 1);
}

function authUrl() {
  const env = loadEnv();
  const clientId = env.LINKEDIN_CLIENT_ID;
  const redirectUri = env.LINKEDIN_REDIRECT_URI || DEFAULT_REDIRECT_URI;
  if (!clientId) {
    console.error('Missing LINKEDIN_CLIENT_ID');
    process.exit(1);
  }
  saveEnv({ LINKEDIN_REDIRECT_URI: redirectUri });
  const state = `creditdoc-${Date.now()}`;
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: clientId,
    redirect_uri: redirectUri,
    scope: DEFAULT_SCOPES.join(' '),
    state,
  });
  console.log(JSON.stringify({
    ok: true,
    redirect_uri: redirectUri,
    scopes: DEFAULT_SCOPES,
    state,
    note: 'Add this redirect URI in the LinkedIn Developer app first if it is not already present. After approval, copy the code query parameter and run exchange-code.',
    url: `https://www.linkedin.com/oauth/v2/authorization?${params.toString()}`,
  }, null, 2));
}

async function exchangeCode(code) {
  const env = loadEnv();
  const clientId = env.LINKEDIN_CLIENT_ID;
  const clientSecret = env.LINKEDIN_CLIENT_SECRET || env.LINKEDIN_API_KEY;
  const redirectUri = env.LINKEDIN_REDIRECT_URI || DEFAULT_REDIRECT_URI;
  if (!clientId || !clientSecret) {
    console.error('Missing LINKEDIN_CLIENT_ID or LINKEDIN_CLIENT_SECRET/LINKEDIN_API_KEY');
    process.exit(1);
  }
  if (!code) {
    console.error('Missing authorization code');
    process.exit(1);
  }
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: redirectUri,
    client_id: clientId,
    client_secret: clientSecret,
  });
  const response = await fetch('https://www.linkedin.com/oauth/v2/accessToken', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  const payload = await response.json().catch(async () => ({ raw: await response.text() }));
  if (!response.ok || !payload.access_token) {
    console.error(JSON.stringify({ ok: false, status: response.status, payload }, null, 2));
    process.exit(1);
  }
  saveEnv({
    LINKEDIN_REDIRECT_URI: redirectUri,
    LINKEDIN_ACCESS_TOKEN: payload.access_token,
    LINKEDIN_EXPIRES_IN: String(payload.expires_in || ''),
    LINKEDIN_ACCESS_TOKEN_SAVED_AT: new Date().toISOString(),
  });
  console.log(JSON.stringify({
    ok: true,
    saved: ['LINKEDIN_ACCESS_TOKEN', 'LINKEDIN_EXPIRES_IN', 'LINKEDIN_ACCESS_TOKEN_SAVED_AT'],
    expires_in: payload.expires_in || null,
  }, null, 2));
}

async function listOrganizations() {
  const env = loadEnv();
  const accessToken = env.LINKEDIN_ACCESS_TOKEN;
  if (!accessToken) {
    console.error('Missing LINKEDIN_ACCESS_TOKEN');
    process.exit(1);
  }
  const response = await fetch('https://api.linkedin.com/rest/organizationAcls?q=roleAssignee&role=ADMINISTRATOR&state=APPROVED', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Linkedin-Version': env.LINKEDIN_VERSION || DEFAULT_VERSION,
      'X-Restli-Protocol-Version': '2.0.0',
    },
  });
  const text = await response.text();
  let payload = null;
  try { payload = JSON.parse(text); } catch { payload = { raw: text }; }
  const elements = Array.isArray(payload.elements) ? payload.elements : [];
  console.log(JSON.stringify({
    ok: response.ok,
    status: `${response.status} ${response.statusText}`,
    organizations: elements.map((item) => ({
      organization: item.organization,
      role: item.role,
      state: item.state,
    })),
    raw_count: elements.length,
    payload: response.ok ? undefined : payload,
  }, null, 2));
  process.exit(response.ok ? 0 : 1);
}

function setOrganization(urn) {
  if (!urn || !/^urn:li:organization:\d+$/.test(urn)) {
    console.error('Expected organization URN like urn:li:organization:123456');
    process.exit(1);
  }
  saveEnv({ LINKEDIN_ORGANIZATION_URN: urn });
  console.log(JSON.stringify({ ok: true, saved: 'LINKEDIN_ORGANIZATION_URN' }, null, 2));
}

function postsThisWeek(state, week) {
  return state.published.filter((post) => post.iso_week === week).length;
}

async function createLinkedInPost(env, draft) {
  const author = env.LINKEDIN_ORGANIZATION_URN;
  const accessToken = env.LINKEDIN_ACCESS_TOKEN;
  if (!author) throw new Error('Missing LINKEDIN_ORGANIZATION_URN');
  if (!accessToken) throw new Error('Missing LINKEDIN_ACCESS_TOKEN');
  const body = {
    author,
    commentary: draft.commentary,
    visibility: 'PUBLIC',
    distribution: {
      feedDistribution: 'MAIN_FEED',
      targetEntities: [],
      thirdPartyDistributionChannels: [],
    },
    content: {
      article: {
        source: draft.target_url,
        title: draft.title,
        description: `CreditDoc resource: ${draft.title}`,
      },
    },
    lifecycleState: 'PUBLISHED',
    isReshareDisabledByAuthor: false,
  };
  const response = await fetch('https://api.linkedin.com/rest/posts', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Linkedin-Version': env.LINKEDIN_VERSION || DEFAULT_VERSION,
      'X-Restli-Protocol-Version': '2.0.0',
    },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`LinkedIn post failed: ${response.status} ${response.statusText}: ${text.slice(0, 500)}`);
  }
  return response.headers.get('x-restli-id') || text.trim() || null;
}

async function publishApproved(dryRun) {
  const env = loadEnv();
  const queue = loadQueue();
  const state = loadState();
  const nowDate = today();
  const week = isoWeek(nowDate);
  const used = postsThisWeek(state, week);
  if (used >= WEEKLY_CAP) {
    console.log(JSON.stringify({ ok: true, published: [], skipped: `weekly cap reached (${used}/${WEEKLY_CAP})` }, null, 2));
    return;
  }

  const candidates = queue.drafts
    .filter((draft) => draft.status === 'approved' && draft.scheduled_date <= nowDate)
    .sort((a, b) => `${a.scheduled_date}:${a.id}`.localeCompare(`${b.scheduled_date}:${b.id}`))
    .slice(0, WEEKLY_CAP - used);

  const published = [];
  for (const draft of candidates) {
    let postUrn = null;
    if (!dryRun) postUrn = await createLinkedInPost(env, draft);
    draft.status = dryRun ? 'approved' : 'published';
    draft.published_at = dryRun ? null : new Date().toISOString();
    draft.linkedin_post_urn = dryRun ? null : postUrn;
    if (!dryRun) {
      const record = {
        id: draft.id,
        iso_week: week,
        published_at: draft.published_at,
        target_url: draft.target_url,
        linkedin_post_urn: postUrn,
      };
      state.published.push(record);
      ensureDir(LOG_FILE);
      fs.appendFileSync(LOG_FILE, `${JSON.stringify(record)}\n`);
    }
    published.push({ id: draft.id, target_url: draft.target_url, linkedin_post_urn: postUrn });
  }
  if (!dryRun) {
    saveQueue(queue);
    saveState(state);
  }
  console.log(JSON.stringify({ ok: true, dry_run: dryRun, published, weekly_used_after: used + published.length }, null, 2));
}

async function main() {
  const [command, ...args] = process.argv.slice(2);
  if (!command || command === '--help' || command === 'help') {
    usage();
    return;
  }
  if (command === 'auth-check') await authCheck();
  else if (command === 'auth-url') authUrl();
  else if (command === 'exchange-code') await exchangeCode(args[0]);
  else if (command === 'list-organizations') await listOrganizations();
  else if (command === 'set-organization') setOrganization(args[0]);
  else if (command === 'draft-week') {
    const dateArg = args.includes('--date') ? args[args.indexOf('--date') + 1] : args.find((arg) => arg.startsWith('--date='))?.slice(7);
    draftWeek(dateArg);
  } else if (command === 'status') status();
  else if (command === 'approve') approve(args[0]);
  else if (command === 'publish-approved') await publishApproved(args.includes('--dry-run'));
  else {
    usage();
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
