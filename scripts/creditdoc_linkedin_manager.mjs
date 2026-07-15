#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const ROOT = '/srv/BusinessOps';
const SECRETS_FILE = `${ROOT}/tools/.linkedin.env`;
const QUEUE_FILE = `${ROOT}/data/creditdoc_linkedin_queue.json`;
const STATE_FILE = `${ROOT}/data/creditdoc_linkedin_state.json`;
const CARD_DIR = `${ROOT}/data/creditdoc_linkedin_cards`;
const PINTEREST_STATE_FILE = `${ROOT}/data/creditdoc_pinterest_state.json`;
const PINTEREST_CARD_DIR = `${ROOT}/data/creditdoc_pinterest_pins`;
const LOG_FILE = `${ROOT}/logs/creditdoc_linkedin_posts.jsonl`;
const PINTEREST_LOG_FILE = `${ROOT}/logs/creditdoc_pinterest_blotato_posts.jsonl`;
const DEFAULT_VERSION = '202606';
const WEEKLY_CAP = 2;
const LINKEDIN_TARGET_REPEAT_BLOCK_DAYS = 90;
const PINTEREST_INTERVAL_DAYS = 3;
const PINTEREST_TARGET_REPEAT_BLOCK_DAYS = 90;
const CROSS_CHANNEL_TARGET_REPEAT_BLOCK_DAYS = 30;
const SOCIAL_DUPLICATE_GUARD_EFFECTIVE_DATE = '2026-07-06';
const DEFAULT_REDIRECT_URI = 'https://www.creditdoc.co/linkedin-oauth-callback/';
const DEFAULT_SCOPES = ['w_organization_social', 'r_organization_social'];
const FILE_ENV = loadEnv();
const CDN_DIR = process.env.CREDITDOC_SOCIAL_CDN_DIR || '/var/www/html/social-media';
const CDN_BASE = (process.env.CREDITDOC_SOCIAL_CDN_BASE || 'https://cdn.supagum.com').replace(/\/$/, '');
const BLOTATO_PROXY = (process.env.BLOTATO_PROXY || FILE_ENV.BLOTATO_PROXY || 'http://localhost:8098').replace(/\/$/, '');
const PINTEREST_DISABLED = ['1', 'true', 'yes'].includes(String(process.env.PINTEREST_DISABLED || FILE_ENV.PINTEREST_DISABLED || '').toLowerCase());
const BLOTATO_PINTEREST_ACCOUNT_ID = process.env.BLOTATO_PINTEREST_ACCOUNT_ID || FILE_ENV.BLOTATO_PINTEREST_ACCOUNT_ID || '7943';
const BLOTATO_PINTEREST_BOARD_ID = process.env.BLOTATO_PINTEREST_BOARD_ID || FILE_ENV.BLOTATO_PINTEREST_BOARD_ID || '';

const CAMPAIGNS = [
  {
    slug: 'commercial-loan-calculator',
    url: 'https://www.creditdoc.co/tools/commercial-loan-calculator/',
    title: 'Commercial loan calculator',
    problem: 'Commercial loan payments can look simple at first, but the real obligation changes once amortization, balloon maturity, closing costs, and debt-service coverage are included.',
    purpose: 'The CreditDoc commercial loan calculator helps business owners model payment, total repayment, estimated closing costs, balloon balance, and DSCR before comparing lender terms.',
    useCases: ['commercial real estate loans', 'owner-occupied property financing', 'balloon-payment planning', 'cash-flow checks before lender conversations'],
    cta: 'Use the free calculator here:',
    hashtags: ['#SmallBusinessFinance', '#CommercialLoans', '#BusinessFunding'],
  },
  {
    slug: 'business-line-of-credit-calculator',
    url: 'https://www.creditdoc.co/tools/business-line-of-credit-calculator/',
    title: 'Business line of credit calculator',
    problem: 'A business line of credit is flexible, but the cost is not just the APR. Draw amount, draw fees, unused-line fees, repayment timing, and utilization all matter.',
    purpose: 'The CreditDoc business line of credit calculator helps borrowers estimate the cost of a draw and understand how repayment choices affect cash flow.',
    useCases: ['working-capital planning', 'seasonal inventory purchases', 'short-term cash-flow gaps', 'comparing bank and online credit lines'],
    cta: 'Use the free calculator here:',
    hashtags: ['#BusinessLineOfCredit', '#SmallBusiness', '#WorkingCapital'],
  },
  {
    slug: 'sba-loan-calculator',
    url: 'https://www.creditdoc.co/tools/sba-loan-calculator/',
    title: 'SBA loan calculator',
    problem: 'SBA loans are often discussed as lower-cost funding, but borrowers still need to estimate monthly payment, interest, fees, and cash-flow pressure.',
    purpose: 'The CreditDoc SBA loan calculator helps business owners test loan amount, term, rate, and fee assumptions before speaking with an SBA lender.',
    useCases: ['SBA 7(a) planning', 'startup or expansion funding', 'monthly payment estimates', 'comparing repayment scenarios'],
    cta: 'Use the free calculator here:',
    hashtags: ['#SBALoans', '#SmallBusinessFinance', '#BusinessLoans'],
  },
  {
    slug: 'state-consumer-credit-regulator-directory',
    kind: 'Research',
    url: 'https://www.creditdoc.co/tools/state-consumer-credit-regulator-directory/',
    title: 'State consumer credit regulator directory',
    problem: 'Before relying on a lender, credit repair company, debt service, or financing offer, consumers and business owners should know where to check state regulator and complaint resources.',
    purpose: 'The CreditDoc regulator directory gives readers a state-by-state starting point for consumer finance regulators, complaint paths, and lending-law context.',
    useCases: ['checking regulator resources before applying', 'finding state consumer complaint offices', 'comparing offers beyond advertised rates', 'safer lender research'],
    cta: 'Open the free directory here:',
    hashtags: ['#ConsumerFinance', '#CreditEducation', '#FinancialWellness'],
  },
  {
    slug: 'state-lending-law-hub',
    kind: 'Research',
    url: 'https://www.creditdoc.co/state/',
    title: 'State lending law hub',
    problem: 'Loan, credit, debt, and consumer-finance rules are not identical in every state. A national list of lenders is only part of the research.',
    purpose: 'The CreditDoc state hub helps readers move from a broad comparison page into state-level lending-law and consumer protection context.',
    useCases: ['state lending-law research', 'local borrower education', 'credit and loan comparison context', 'consumer protection checks'],
    cta: 'Explore the state hub here:',
    hashtags: ['#ConsumerFinance', '#CreditEducation', '#PersonalFinance'],
  },
  {
    slug: 'creditdoc-data-methodology',
    kind: 'Research',
    url: 'https://www.creditdoc.co/about/creditdoc-data/',
    title: 'How CreditDoc uses public finance data',
    problem: 'Financial comparison pages are more useful when readers can see what data sources and limits sit behind the research.',
    purpose: 'CreditDoc explains how it handles public provider, regulator, complaint, and consumer-finance data, including what the data can and cannot prove.',
    useCases: ['understanding CreditDoc research', 'checking data limits', 'consumer finance transparency', 'AI and search engine ingestion'],
    cta: 'Read the data methodology here:',
    hashtags: ['#ConsumerFinance', '#DataTransparency', '#CreditEducation'],
  },
  {
    slug: 'best-business-lines-of-credit-regulatory-research',
    kind: 'Research',
    url: 'https://www.creditdoc.co/best/best-business-lines-of-credit/',
    title: 'Business line of credit comparison with regulatory context',
    problem: 'A business line of credit offer should be compared on cost, repayment pressure, lender fit, and the regulatory context around the provider.',
    purpose: 'CreditDoc now connects its business line of credit guide with state regulator resources, complaint data context, and free planning tools.',
    useCases: ['business line of credit research', 'working-capital comparison', 'lender due diligence', 'checking offers before applying'],
    cta: 'Read the comparison guide here:',
    hashtags: ['#BusinessLineOfCredit', '#SmallBusinessFinance', '#ConsumerFinance'],
  },
  {
    slug: 'accounts-receivable-financing-calculator',
    url: 'https://www.creditdoc.co/tools/accounts-receivable-financing-calculator/',
    title: 'Accounts receivable financing calculator',
    problem: 'Receivables financing can improve cash flow, but advance rates, reserve holds, fees, and collection timing affect how much cash a business actually receives.',
    purpose: 'The CreditDoc accounts receivable financing calculator helps estimate advance amount, reserve, fees, and net funds from unpaid invoices.',
    useCases: ['invoice financing research', 'cash-flow planning', 'fee comparison', 'estimating net proceeds before applying'],
    cta: 'Use the free calculator here:',
    hashtags: ['#AccountsReceivable', '#WorkingCapital', '#BusinessFinance'],
  },
  {
    slug: 'business-loan-calculator',
    url: 'https://www.creditdoc.co/tools/business-loan-calculator/',
    title: 'Business loan calculator',
    problem: 'A business loan headline rate does not show the full repayment picture. Term length, fees, payment frequency, and total interest can change the decision.',
    purpose: 'The CreditDoc business loan calculator gives borrowers a quick way to estimate payment and repayment pressure before comparing financing options.',
    useCases: ['term-loan planning', 'monthly payment estimates', 'total interest checks', 'side-by-side lender comparison'],
    cta: 'Use the free calculator here:',
    hashtags: ['#BusinessLoans', '#SmallBusinessFinance', '#Entrepreneurs'],
  },
  {
    slug: 'equipment-financing-calculator',
    url: 'https://www.creditdoc.co/tools/equipment-financing-calculator/',
    title: 'Equipment financing calculator',
    problem: 'Equipment financing decisions should account for payment, term, down payment, fees, useful life, and whether the asset can support the debt.',
    purpose: 'The CreditDoc equipment financing calculator helps estimate payment and total repayment before a business commits to equipment debt.',
    useCases: ['vehicle or machinery purchases', 'down-payment planning', 'monthly cash-flow review', 'equipment lender comparison'],
    cta: 'Use the free calculator here:',
    hashtags: ['#EquipmentFinancing', '#SmallBusiness', '#BusinessFunding'],
  },
  {
    slug: 'working-capital-calculator',
    url: 'https://www.creditdoc.co/tools/working-capital-calculator/',
    title: 'Working capital calculator',
    problem: 'Working capital is one of the first checks lenders and owners use to understand short-term financial pressure.',
    purpose: 'The CreditDoc working capital calculator helps estimate current assets minus current liabilities and gives a clearer view of short-term operating cushion.',
    useCases: ['cash-flow reviews', 'lender preparation', 'short-term finance planning', 'operating runway checks'],
    cta: 'Use the free calculator here:',
    hashtags: ['#WorkingCapital', '#BusinessFinance', '#SmallBusiness'],
  },
  {
    slug: 'sba-guarantee-fee-calculator',
    url: 'https://www.creditdoc.co/tools/sba-guarantee-fee-calculator/',
    title: 'SBA guarantee fee calculator',
    problem: 'SBA guarantee fees can be easy to overlook, but they may affect total financing cost and cash needed at closing.',
    purpose: 'The CreditDoc SBA guarantee fee calculator helps estimate the guarantee fee impact before a borrower compares SBA loan options.',
    useCases: ['SBA 7(a) planning', 'closing-cost estimates', 'fee comparison', 'lender conversation prep'],
    cta: 'Use the free calculator here:',
    hashtags: ['#SBALoans', '#BusinessLoans', '#SmallBusinessFinance'],
  },
  {
    slug: 'bank-statement-cash-flow-calculator',
    url: 'https://www.creditdoc.co/tools/bank-statement-cash-flow-calculator/',
    title: 'Bank statement cash flow calculator',
    problem: 'Some lenders look closely at business bank activity. Deposits, average balances, and cash-flow consistency can affect the funding conversation.',
    purpose: 'The CreditDoc bank statement cash flow calculator helps business owners review bank-statement cash flow before applying.',
    useCases: ['bank-statement loan prep', 'cash-flow review', 'deposit consistency checks', 'alternative lender comparison'],
    cta: 'Use the free calculator here:',
    hashtags: ['#CashFlow', '#BusinessFunding', '#SmallBusiness'],
  },
  {
    slug: 'mca-repayment-calculator',
    url: 'https://www.creditdoc.co/tools/mca-repayment-calculator/',
    title: 'MCA repayment calculator',
    problem: 'Merchant cash advances can move quickly, but daily or weekly repayment can put pressure on operating cash flow.',
    purpose: 'The CreditDoc MCA repayment calculator helps estimate repayment amount, holdback pressure, and total payback before a business evaluates an advance.',
    useCases: ['MCA comparison', 'daily repayment planning', 'cash-flow stress checks', 'alternative funding review'],
    cta: 'Use the free calculator here:',
    hashtags: ['#BusinessFunding', '#CashFlow', '#SmallBusinessFinance'],
  },
  {
    slug: 'credit-fundamentals-course',
    kind: 'Course',
    url: 'https://www.creditdoc.co/courses/credit-fundamentals/',
    title: 'Credit fundamentals course',
    problem: 'Credit decisions affect borrowing costs, credit cards, loan approvals, housing, insurance, and business funding, but many readers do not have a structured place to learn the basics.',
    purpose: 'The free CreditDoc credit fundamentals course gives readers a guided path through credit reports, scores, debt, disputes, and safer borrowing decisions.',
    useCases: ['credit education', 'financial wellness onboarding', 'rebuilding credit', 'understanding reports before applying for loans'],
    cta: 'Start the free course here:',
    hashtags: ['#CreditEducation', '#FinancialWellness', '#CreditScores'],
  },
  {
    slug: 'how-do-small-business-loans-work',
    kind: 'Answer',
    url: 'https://www.creditdoc.co/answers/how-do-small-business-loans-work/',
    title: 'How small business loans work',
    problem: 'Small business loans can involve different products, eligibility rules, documents, fees, repayment structures, and risks.',
    purpose: 'This CreditDoc answer explains the main small business loan types, what lenders usually review, how applications work, and what borrowers should check before accepting an offer.',
    useCases: ['business loan research', 'first-time borrower education', 'loan type comparison', 'application preparation'],
    cta: 'Read the answer here:',
    hashtags: ['#BusinessLoans', '#SmallBusinessFinance', '#BusinessFunding'],
  },
  {
    slug: 'business-loan-rates-fees-explained',
    kind: 'Answer',
    url: 'https://www.creditdoc.co/answers/business-loan-rates-fees-explained/',
    title: 'Business loan rates and fees explained',
    problem: 'The monthly payment is only one part of a business loan. APR, origination fees, draw fees, prepayment terms, and repayment frequency can all affect cost.',
    purpose: 'This CreditDoc answer breaks down the common rate and fee terms business borrowers should understand before comparing lenders.',
    useCases: ['loan offer review', 'APR comparison', 'fee checks', 'borrower preparation'],
    cta: 'Read the answer here:',
    hashtags: ['#BusinessLoans', '#SmallBusinessFinance', '#APR'],
  },
  {
    slug: 'can-i-get-small-business-loan-with-bad-credit',
    kind: 'Answer',
    url: 'https://www.creditdoc.co/answers/can-i-get-small-business-loan-with-bad-credit/',
    title: 'Small business loans with bad credit',
    problem: 'Bad credit does not always make business funding impossible, but it can affect lender options, pricing, collateral requirements, and personal guarantee risk.',
    purpose: 'This CreditDoc answer explains what borrowers with weaker credit should expect and how to prepare before applying.',
    useCases: ['bad-credit business funding research', 'application preparation', 'risk review', 'alternative funding comparison'],
    cta: 'Read the answer here:',
    hashtags: ['#BusinessLoans', '#BadCredit', '#SmallBusiness'],
  },
  {
    slug: 'business-line-of-credit-guide-new-llc-bad-credit',
    kind: 'Answer',
    url: 'https://www.creditdoc.co/answers/business-line-of-credit-guide-new-llc-bad-credit/',
    title: 'Business line of credit for a new LLC with bad credit',
    problem: 'New LLCs with limited revenue or weak credit often face stricter underwriting, smaller limits, higher costs, or secured funding requirements.',
    purpose: 'This CreditDoc answer explains how business lines of credit may work for new LLCs and what owners should check before applying.',
    useCases: ['new LLC funding research', 'line of credit comparison', 'credit profile preparation', 'working capital planning'],
    cta: 'Read the answer here:',
    hashtags: ['#BusinessLineOfCredit', '#StartupFunding', '#SmallBusiness'],
  },
  {
    slug: 'are-merchant-cash-advances-a-good-idea',
    kind: 'Answer',
    url: 'https://www.creditdoc.co/answers/are-merchant-cash-advances-a-good-idea/',
    title: 'Are merchant cash advances a good idea?',
    problem: 'Merchant cash advances can provide fast capital, but repayment structure, factor rates, and daily or weekly withdrawals can create serious cash-flow pressure.',
    purpose: 'This CreditDoc answer helps business owners understand when an MCA may be risky and what to compare before accepting one.',
    useCases: ['MCA research', 'cash-flow risk review', 'alternative funding comparison', 'repayment pressure checks'],
    cta: 'Read the answer here:',
    hashtags: ['#MerchantCashAdvance', '#BusinessFunding', '#CashFlow'],
  },
  {
    slug: 'business-line-of-credit-guide',
    kind: 'Wellness guide',
    url: 'https://www.creditdoc.co/financial-wellness/business-line-of-credit-guide/',
    title: 'Business line of credit guide',
    problem: 'A business line of credit can help with working capital, but owners still need to understand draw costs, repayment timing, utilization, and the difference between revolving credit and a term loan.',
    purpose: 'This CreditDoc financial-wellness guide explains how business lines of credit work, what lenders may review, and how borrowers can compare offers more carefully.',
    useCases: ['working-capital education', 'business funding research', 'line of credit comparison', 'borrower preparation'],
    cta: 'Read the guide here:',
    hashtags: ['#BusinessLineOfCredit', '#FinancialWellness', '#SmallBusinessFinance'],
  },
  {
    slug: 'business-loan-bad-credit',
    kind: 'Wellness guide',
    url: 'https://www.creditdoc.co/financial-wellness/business-loan-bad-credit/',
    title: 'Business loans with bad credit guide',
    problem: 'Bad credit can change a business loan conversation quickly. It may affect approval odds, rates, collateral, personal guarantees, and whether an alternative lender is worth the cost.',
    purpose: 'This CreditDoc guide helps business owners understand the tradeoffs before applying for funding with weaker credit.',
    useCases: ['bad-credit business funding research', 'loan readiness', 'risk review', 'alternative funding comparison'],
    cta: 'Read the guide here:',
    hashtags: ['#BusinessLoans', '#BadCredit', '#FinancialWellness'],
  },
  {
    slug: 'cash-advance-alternatives',
    kind: 'Wellness guide',
    url: 'https://www.creditdoc.co/financial-wellness/cash-advance-alternatives/',
    title: 'Cash advance alternatives',
    problem: 'Cash advances can solve a short-term problem while creating a harder repayment problem. Borrowers need safer options before fees and repeat borrowing become the pattern.',
    purpose: 'This CreditDoc financial-wellness guide explains alternatives to cash advances and the questions to ask before using fast-cash products.',
    useCases: ['cash-flow stress', 'emergency borrowing research', 'fee comparison', 'safer borrowing decisions'],
    cta: 'Read the guide here:',
    hashtags: ['#FinancialWellness', '#CashAdvance', '#ConsumerFinance'],
  },
  {
    slug: 'credit-score-borrowing-power',
    kind: 'Wellness guide',
    url: 'https://www.creditdoc.co/financial-wellness/credit-score-borrowing-power/',
    title: 'Credit score and borrowing power',
    problem: 'A credit score does not guarantee approval, but it can influence available products, rate ranges, limits, deposits, and how lenders price risk.',
    purpose: 'This CreditDoc guide explains how credit scores can affect borrowing power and why borrowers should compare the full terms, not only the approval result.',
    useCases: ['credit education', 'loan preparation', 'rate comparison', 'borrowing power planning'],
    cta: 'Read the guide here:',
    hashtags: ['#CreditScores', '#FinancialWellness', '#Borrowing'],
  },
  {
    slug: 'sba-loan-application-guide',
    kind: 'Wellness guide',
    url: 'https://www.creditdoc.co/financial-wellness/sba-loan-application-guide/',
    title: 'SBA loan application guide',
    problem: 'SBA loan applications can require more preparation than faster financing products, including financial documents, business history, collateral context, and repayment analysis.',
    purpose: 'This CreditDoc guide helps business owners understand what to prepare before starting an SBA loan conversation.',
    useCases: ['SBA loan preparation', 'document planning', 'business funding research', 'lender conversation prep'],
    cta: 'Read the guide here:',
    hashtags: ['#SBALoans', '#SmallBusinessFinance', '#FinancialWellness'],
  },
  {
    slug: 'predatory-lending-signs',
    kind: 'Wellness guide',
    url: 'https://www.creditdoc.co/financial-wellness/predatory-lending-signs/',
    title: 'Signs of predatory lending',
    problem: 'Fast approvals and simple payments can hide expensive terms, repeat borrowing cycles, aggressive collections, or contract details that borrowers did not understand.',
    purpose: 'This CreditDoc financial-wellness guide explains warning signs to check before accepting a loan or cash advance.',
    useCases: ['loan offer review', 'consumer protection', 'fee and contract checks', 'safer borrowing decisions'],
    cta: 'Read the guide here:',
    hashtags: ['#ConsumerFinance', '#FinancialWellness', '#Borrowing'],
  },
];

function usage() {
  console.log(`Usage:
  node scripts/creditdoc_linkedin_manager.mjs auth-check
  node scripts/creditdoc_linkedin_manager.mjs auth-url
  node scripts/creditdoc_linkedin_manager.mjs exchange-code <code>
  node scripts/creditdoc_linkedin_manager.mjs list-organizations
  node scripts/creditdoc_linkedin_manager.mjs set-organization <urn:li:organization:id>
  node scripts/creditdoc_linkedin_manager.mjs set-pinterest-account <accountId>
  node scripts/creditdoc_linkedin_manager.mjs set-pinterest-board <boardId>
  node scripts/creditdoc_linkedin_manager.mjs draft-week [--date YYYY-MM-DD]
  node scripts/creditdoc_linkedin_manager.mjs run-scheduled-resources [--date YYYY-MM-DD] [--dry-run]
  node scripts/creditdoc_linkedin_manager.mjs run-scheduled-tools [--date YYYY-MM-DD] [--dry-run]
  node scripts/creditdoc_linkedin_manager.mjs run-scheduled-pinterest [--date YYYY-MM-DD] [--dry-run]
  node scripts/creditdoc_linkedin_manager.mjs preview-pinterest-week [--date YYYY-MM-DD] [--days N]
  node scripts/creditdoc_linkedin_manager.mjs audit-social-duplicates [--date YYYY-MM-DD]
  node scripts/creditdoc_linkedin_manager.mjs status
  node scripts/creditdoc_linkedin_manager.mjs approve <draft-id>
  node scripts/creditdoc_linkedin_manager.mjs render-card <draft-id>
  node scripts/creditdoc_linkedin_manager.mjs publish-approved [--dry-run] [--limit N]

Safety:
  - Scheduled resource posting can auto-approve due CreditDoc resource drafts.
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
    'BLOTATO_PROXY',
    'BLOTATO_PINTEREST_ACCOUNT_ID',
    'BLOTATO_PINTEREST_BOARD_ID',
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

function appendJsonl(file, payload) {
  ensureDir(file);
  fs.appendFileSync(file, `${JSON.stringify(payload)}\n`);
}

function readJsonl(file) {
  if (!fs.existsSync(file)) return [];
  return fs.readFileSync(file, 'utf8')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

function isSuccessfulPinterestRecord(record) {
  if (!record || !record.ok) return false;
  const payload = record.payload && typeof record.payload === 'object' ? record.payload : {};
  const raw = typeof payload.raw === 'string' ? payload.raw.toLowerCase() : '';
  if (raw.includes('error')) return false;
  return Boolean(payload.publicUrl || payload.postSubmissionId || payload.status === 'published' || payload.statusCode === 200);
}

function successfulPinterestRecords(state = loadPinterestState()) {
  const records = [];
  for (const record of Array.isArray(state.published) ? state.published : []) {
    const result = record.blotato_result || {};
    if (!result.ok) continue;
    records.push({
      id: record.id,
      target_url: record.target_url,
      created_at: record.published_at,
      public_url: result.payload?.publicUrl || null,
      source: 'state',
    });
  }
  for (const record of readJsonl(PINTEREST_LOG_FILE)) {
    if (!isSuccessfulPinterestRecord(record)) continue;
    records.push({
      id: record.id,
      target_url: record.target_url,
      created_at: record.created_at,
      public_url: record.payload?.publicUrl || null,
      source: 'jsonl',
    });
  }
  return records.filter((record) => record.target_url && record.created_at);
}

function successfulLinkedInRecords(state = loadState()) {
  const records = [];
  for (const record of Array.isArray(state.published) ? state.published : []) {
    if (!record.linkedin_post_urn) continue;
    records.push({
      id: record.id,
      target_url: record.target_url,
      created_at: record.published_at,
      public_url: record.linkedin_post_urn,
      source: 'state',
    });
  }
  for (const record of readJsonl(LOG_FILE)) {
    if (!record || !record.linkedin_post_urn) continue;
    records.push({
      id: record.id,
      target_url: record.target_url,
      created_at: record.published_at,
      public_url: record.linkedin_post_urn,
      source: 'jsonl',
    });
  }
  return records.filter((record) => record.target_url && record.created_at);
}

function recentSocialDuplicate(records, targetUrl, nowDate, blockDays) {
  const matches = records
    .filter((record) => record.target_url === targetUrl)
    .map((record) => ({
      ...record,
      date: String(record.created_at).slice(0, 10),
    }))
    .filter((record) => record.date && daysBetween(record.date, nowDate) >= 0)
    .sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)));
  const latest = matches[0] || null;
  if (!latest) return null;
  const ageDays = daysBetween(latest.date, nowDate);
  if (ageDays >= blockDays) return null;
  return { ...latest, age_days: ageDays, block_days: blockDays };
}

function recentLinkedInDuplicate(targetUrl, nowDate = today(), state = loadState()) {
  return recentSocialDuplicate(successfulLinkedInRecords(state), targetUrl, nowDate, LINKEDIN_TARGET_REPEAT_BLOCK_DAYS);
}

function recentPinterestDuplicate(targetUrl, nowDate = today(), state = loadPinterestState()) {
  return recentSocialDuplicate(successfulPinterestRecords(state), targetUrl, nowDate, PINTEREST_TARGET_REPEAT_BLOCK_DAYS);
}

function recentPublishedTargets(nowDate = today(), blockDays = CROSS_CHANNEL_TARGET_REPEAT_BLOCK_DAYS) {
  const targets = new Map();
  const add = (targetUrl, createdAt, source, id) => {
    if (!targetUrl || !createdAt) return;
    const date = String(createdAt).slice(0, 10);
    const ageDays = daysBetween(date, nowDate);
    if (ageDays < 0 || ageDays >= blockDays) return;
    const current = targets.get(targetUrl);
    if (!current || String(createdAt) > String(current.created_at)) {
      targets.set(targetUrl, { target_url: targetUrl, created_at: createdAt, date, age_days: ageDays, source, id });
    }
  };
  const linkedinState = loadState();
  for (const record of Array.isArray(linkedinState.published) ? linkedinState.published : []) {
    add(record.target_url, record.published_at, 'linkedin-state', record.id);
  }
  for (const record of successfulLinkedInRecords(linkedinState)) {
    add(record.target_url, record.created_at, `linkedin-${record.source}`, record.id);
  }
  for (const record of successfulPinterestRecords()) {
    add(record.target_url, record.created_at, `pinterest-${record.source}`, record.id);
  }
  return targets;
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

function daysBetween(startDate, endDate) {
  const start = new Date(`${startDate}T00:00:00Z`);
  const end = new Date(`${endDate}T00:00:00Z`);
  return Math.floor((end - start) / 86400000);
}

function nextWeekday(dateString, targetDay) {
  const date = new Date(`${dateString}T00:00:00Z`);
  const current = date.getUTCDay();
  const delta = (targetDay - current + 7) % 7;
  return addDays(dateString, delta);
}

function sameWeekday(dateString, targetDay) {
  const date = new Date(`${dateString}T00:00:00Z`);
  const current = date.getUTCDay();
  const delta = targetDay - current;
  return addDays(dateString, delta);
}

function storyForCampaign(campaign) {
  const storyBySlug = {
    'sba-loan-calculator': [
      'A business owner can hear "SBA loan" and immediately think lower-cost funding. That may be true, but the monthly payment, guarantee fees, term, and cash-flow pressure still need to work together.',
      'This calculator is for the moment before a lender conversation, when you want to test the numbers yourself and understand what a realistic repayment picture could look like.',
    ],
    'accounts-receivable-financing-calculator': [
      'Unpaid invoices can make a business look busy while cash still feels tight. Receivables financing may help, but the advance rate, reserve holdback, fees, and collection timing decide how much cash actually reaches the business.',
      'Use this calculator to estimate the net funds before comparing invoice-financing offers.',
    ],
    'business-line-of-credit-calculator': [
      'A business line of credit can feel flexible, but the cost changes once draws, fees, repayment timing, and utilization enter the picture.',
      'Use this calculator to model a draw before relying on a credit line for working capital.',
    ],
    'commercial-loan-calculator': [
      'Commercial loan offers can look simple on the surface. The real picture depends on amortization, balloon maturity, closing costs, and whether cash flow can support the debt.',
      'Use this calculator to compare the payment and repayment pressure before moving deeper into a deal.',
    ],
  };
  return storyBySlug[campaign.slug] || [
    campaign.problem || `Financial decisions are easier to compare when the numbers are visible before you apply.`,
    `Use this CreditDoc ${(campaign.kind || 'Tool').toLowerCase()} to understand the tradeoffs before making the next move.`,
  ];
}

function makePost(campaign) {
  const kind = campaign.kind || 'Tool';
  const story = storyForCampaign(campaign);
  return [
    `${campaign.title} from CreditDoc`,
    '',
    ...story,
    '',
    `Useful for: ${campaign.useCases.join(', ')}.`,
    '',
    campaign.cta,
    campaign.url,
    '',
    campaign.hashtags.join(' '),
  ].join('\n');
}

function makePinterestDescription(draft) {
  const campaign = campaignForDraft(draft);
  const kind = (campaign.kind || 'Tool').toLowerCase();
  const useCases = (campaign.useCases || []).slice(0, 3).join(', ');
  const story = storyForCampaign(campaign);
  return [
    `${campaign.title} from CreditDoc`,
    '',
    ...story,
    '',
    useCases ? `Useful for: ${useCases}.` : '',
    '',
    `Open the free ${kind}:`,
    draft.target_url,
    '',
    (campaign.hashtags || []).join(' '),
  ].filter((line) => line !== '').join('\n');
}

function blotatoPublishSucceeded(responseOk, payload) {
  if (!responseOk || !payload || typeof payload !== 'object') return false;
  const raw = typeof payload.raw === 'string' ? payload.raw.toLowerCase() : '';
  if (raw.includes('error')) return false;
  return Boolean(payload.postSubmissionId || payload.id || payload.publicUrl || payload.url || payload.status === 'success' || payload.status === 'queued');
}

function campaignForDraft(draft) {
  return CAMPAIGNS.find((campaign) => campaign.slug === draft.campaign_slug) || {
    slug: draft.campaign_slug,
    title: draft.title,
    kind: 'Tool',
    problem: `CreditDoc resource: ${draft.title}`,
    useCases: ['financial planning', 'loan research', 'borrower preparation'],
  };
}

function cardPathForDraft(draft) {
  return path.join(CARD_DIR, `${draft.id}.png`);
}

function pinterestPinPathForDraft(draft) {
  return path.join(PINTEREST_CARD_DIR, `${draft.id}.png`);
}

function renderCardForDraft(draft) {
  const campaign = campaignForDraft(draft);
  const out = cardPathForDraft(draft);
  const kind = campaign.kind || 'Tool';
  const args = [
    'scripts/creditdoc_linkedin_card.py',
    '--out',
    out,
    '--kind',
    kind,
    '--title',
    draft.title,
    '--summary',
    campaign.problem || `CreditDoc resource: ${draft.title}`,
    '--use-cases',
    (campaign.useCases || []).join('|'),
  ];
  const result = spawnSync('python3', args, {
    cwd: '/srv/BusinessOps/creditdoc',
    encoding: 'utf8',
  });
  if (result.status !== 0) {
    throw new Error(`Card render failed: ${result.stderr || result.stdout || `exit ${result.status}`}`);
  }
  if (!fs.existsSync(out) || fs.statSync(out).size < 10000) {
    throw new Error(`Card render did not create a valid image: ${out}`);
  }
  draft.image_path = out;
  draft.image_alt = `${draft.title} CreditDoc ${kind.toLowerCase()} resource card`;
  return out;
}

function renderPinterestPinForDraft(draft) {
  const campaign = campaignForDraft(draft);
  const out = pinterestPinPathForDraft(draft);
  const kind = campaign.kind || 'Tool';
  const args = [
    'scripts/creditdoc_pinterest_pin.py',
    '--out',
    out,
    '--kind',
    kind,
    '--title',
    draft.title,
    '--summary',
    campaign.problem || `CreditDoc resource: ${draft.title}`,
    '--use-cases',
    (campaign.useCases || []).join('|'),
    '--url',
    draft.target_url,
  ];
  const campaignIndex = CAMPAIGNS.findIndex((item) => item.slug === draft.campaign_slug);
  if (campaignIndex >= 0) {
    args.push('--variant', String(campaignIndex));
  }
  const result = spawnSync('python3', args, {
    cwd: '/srv/BusinessOps/creditdoc',
    encoding: 'utf8',
  });
  if (result.status !== 0) {
    throw new Error(`Pinterest pin render failed: ${result.stderr || result.stdout || `exit ${result.status}`}`);
  }
  if (!fs.existsSync(out) || fs.statSync(out).size < 10000) {
    throw new Error(`Pinterest pin render did not create a valid image: ${out}`);
  }
  draft.pinterest_image_path = out;
  return out;
}

function renderCardCommand(id) {
  const queue = loadQueue();
  const draft = queue.drafts.find((item) => item.id === id);
  if (!draft) {
    console.error(`Draft not found: ${id}`);
    process.exit(1);
  }
  const imagePath = renderCardForDraft(draft);
  saveQueue(queue);
  console.log(JSON.stringify({
    ok: true,
    id: draft.id,
    image_path: imagePath,
    image_alt: draft.image_alt,
  }, null, 2));
}

function copyCardToCdn(imagePath, draft, suffix = '') {
  fs.mkdirSync(CDN_DIR, { recursive: true });
  const filename = `${draft.id}${suffix}.png`;
  const dest = path.join(CDN_DIR, filename);
  fs.copyFileSync(imagePath, dest);
  fs.chmodSync(dest, 0o644);
  return `${CDN_BASE}/${filename}`;
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

function loadPinterestState() {
  return readJson(PINTEREST_STATE_FILE, { published: [], next_campaign_index: 0, last_published_date: null });
}

function savePinterestState(state) {
  writeJson(PINTEREST_STATE_FILE, state);
}

function existingDraftKeys(queue) {
  return new Set(queue.drafts.map((draft) => `${draft.scheduled_date}:${draft.campaign_slug}`));
}

function campaignFamily(campaign) {
  if ((campaign.kind || 'Tool') === 'Course') return 'course';
  if ((campaign.kind || 'Tool') === 'Answer') return 'answer';
  if ((campaign.kind || 'Tool').toLowerCase().includes('wellness')) return 'wellness';
  return 'tool';
}

function pickCampaignByFamily(family, seed, usedSlugs, usedTargets = new Set()) {
  const pool = CAMPAIGNS.filter((campaign) => campaignFamily(campaign) === family);
  if (pool.length === 0) return null;
  for (let offset = 0; offset < pool.length; offset += 1) {
    const campaign = pool[(seed + offset) % pool.length];
    if (!usedSlugs.has(campaign.slug) && !usedTargets.has(campaign.url)) return campaign;
  }
  for (let offset = 0; offset < pool.length; offset += 1) {
    const campaign = pool[(seed + offset) % pool.length];
    if (!usedSlugs.has(campaign.slug)) return campaign;
  }
  return null;
}

function pickCampaignsForWeek(base, queue) {
  const weekSeed = Number(isoWeek(base).split('W')[1]) || 1;
  const patterns = [
    ['tool', 'wellness'],
    ['course', 'answer'],
    ['tool', 'wellness'],
    ['answer', 'tool'],
  ];
  const pattern = patterns[(weekSeed - 1) % patterns.length];
  const usedSlugs = new Set(queue.drafts.map((draft) => draft.campaign_slug));
  const usedTargets = new Set(recentPublishedTargets(base).keys());
  const picks = [];
  for (const family of pattern) {
    const campaign = pickCampaignByFamily(family, weekSeed + picks.length, usedSlugs, usedTargets);
    if (!campaign) continue;
    usedSlugs.add(campaign.slug);
    usedTargets.add(campaign.url);
    picks.push(campaign);
  }
  return picks;
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

function buildPinterestDraft(campaign, scheduledDate) {
  return {
    id: `cd-pin-${scheduledDate}-${campaign.slug}`,
    campaign_slug: campaign.slug,
    title: campaign.title,
    target_url: campaign.url,
    scheduled_date: scheduledDate,
    slot: 'pinterest',
    status: 'approved',
    created_at: new Date().toISOString(),
    commentary: makePost(campaign),
  };
}

function pickPinterestCampaign(state, nowDate) {
  const start = Number(state.next_campaign_index || 0);
  const usedTargets = new Set(recentPublishedTargets(nowDate).keys());
  for (let offset = 0; offset < CAMPAIGNS.length; offset += 1) {
    const index = (start + offset) % CAMPAIGNS.length;
    const campaign = CAMPAIGNS[index];
    if (!usedTargets.has(campaign.url)) return { campaign, index, skipped_recent: offset };
  }
  return { campaign: null, index: start, skipped_recent: CAMPAIGNS.length };
}

function refreshDraftFromCampaign(draft, campaign, slot) {
  if (draft.status === 'published') return false;
  draft.title = campaign.title;
  draft.target_url = campaign.url;
  draft.slot = slot;
  draft.commentary = makePost(campaign);
  return true;
}

function draftWeek(dateArg, options = {}) {
  const base = today(dateArg);
  const tuesday = sameWeekday(base, 2);
  const friday = sameWeekday(base, 5);
  const queue = options.queue || loadQueue();
  const keys = existingDraftKeys(queue);

  const weekCampaigns = pickCampaignsForWeek(base, queue);
  const picks = [
    { campaign: weekCampaigns[0], date: tuesday, slot: 'resource' },
    { campaign: weekCampaigns[1], date: friday, slot: 'resource' },
  ].filter((pick) => pick.campaign);

  const added = [];
  const refreshed = [];
  const campaignBySlug = new Map(CAMPAIGNS.map((campaign) => [campaign.slug, campaign]));
  for (const pick of picks) {
    if (pick.date < base) continue;
    const dateAlreadyQueued = queue.drafts.some((draft) => draft.status !== 'published' && draft.scheduled_date === pick.date);
    if (dateAlreadyQueued) continue;
    const key = `${pick.date}:${pick.campaign.slug}`;
    if (keys.has(key)) {
      const draft = queue.drafts.find((item) => item.scheduled_date === pick.date && item.campaign_slug === pick.campaign.slug);
      if (draft && refreshDraftFromCampaign(draft, pick.campaign, pick.slot)) refreshed.push(draft.id);
      continue;
    }
    const draft = buildDraft(pick.campaign, pick.date, pick.slot);
    queue.drafts.push(draft);
    added.push(draft.id);
  }
  for (const draft of queue.drafts) {
    const campaign = campaignBySlug.get(draft.campaign_slug);
    if (!campaign) continue;
    if (refreshDraftFromCampaign(draft, campaign, 'resource') && !refreshed.includes(draft.id)) {
      refreshed.push(draft.id);
    }
  }
  queue.drafts.sort((a, b) => `${a.scheduled_date}:${a.id}`.localeCompare(`${b.scheduled_date}:${b.id}`));
  if (!options.dryRun) saveQueue(queue);
  const result = { ok: true, added, refreshed, queue_file: QUEUE_FILE };
  if (!options.silent) console.log(JSON.stringify(result, null, 2));
  return result;
}

function approveDueResourceDrafts(dateArg, options = {}) {
  const nowDate = today(dateArg);
  const queue = options.queue || loadQueue();
  const eligibleSlugs = new Set(CAMPAIGNS.map((campaign) => campaign.slug));
  const approved = [];
  for (const draft of queue.drafts) {
    if (draft.status !== 'draft') continue;
    if (!eligibleSlugs.has(draft.campaign_slug)) continue;
    if (draft.scheduled_date > nowDate) continue;
    draft.status = 'approved';
    draft.approved_at = new Date().toISOString();
    approved.push(draft.id);
  }
  if (approved.length > 0 && !options.dryRun) saveQueue(queue);
  return approved;
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
    pinterest: {
      proxy: BLOTATO_PROXY,
      account_id: BLOTATO_PINTEREST_ACCOUNT_ID,
      has_board_id: Boolean(BLOTATO_PINTEREST_BOARD_ID),
      board_id: BLOTATO_PINTEREST_BOARD_ID || null,
    },
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
  if (!orgUrn) {
    report.ok = false;
    report.api_status = 'missing LINKEDIN_ORGANIZATION_URN; company page organization is required for API posting';
    console.log(JSON.stringify(report, null, 2));
    process.exit(1);
  }

  const organizationId = orgUrn.split(':').pop();
  const response = await fetch('https://api.linkedin.com/v2/organizations?q=vanityName&vanityName=creditdoc-co&projection=(elements*(id,localizedName,vanityName))', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'X-Restli-Protocol-Version': '2.0.0',
    },
  });
  report.api_status = `${response.status} ${response.statusText}`;
  const payload = await response.json().catch(() => ({}));
  const organizations = Array.isArray(payload.elements) ? payload.elements : [];
  report.organization_id = organizationId;
  report.organization_lookup_match = organizations.some((item) => String(item.id) === String(organizationId));
  report.ok = response.ok && report.organization_lookup_match;
  console.log(JSON.stringify(report, null, 2));
  process.exit(report.ok ? 0 : 1);
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

function setPinterestBoard(boardId) {
  if (!boardId) {
    console.error('Missing Pinterest boardId');
    process.exit(1);
  }
  saveEnv({ BLOTATO_PINTEREST_BOARD_ID: boardId });
  console.log(JSON.stringify({
    ok: true,
    saved: 'BLOTATO_PINTEREST_BOARD_ID',
    board_id: boardId,
  }, null, 2));
}

function setPinterestAccount(accountId) {
  if (!accountId) {
    console.error('Missing Pinterest accountId');
    process.exit(1);
  }
  saveEnv({ BLOTATO_PINTEREST_ACCOUNT_ID: accountId });
  console.log(JSON.stringify({
    ok: true,
    saved: 'BLOTATO_PINTEREST_ACCOUNT_ID',
    account_id: accountId,
  }, null, 2));
}

function postsThisWeek(state, week) {
  return state.published.filter((post) => post.iso_week === week).length;
}

async function uploadLinkedInImage(env, imagePath) {
  const owner = env.LINKEDIN_ORGANIZATION_URN;
  const accessToken = env.LINKEDIN_ACCESS_TOKEN;
  const version = env.LINKEDIN_VERSION || DEFAULT_VERSION;
  const initResponse = await fetch('https://api.linkedin.com/rest/images?action=initializeUpload', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Linkedin-Version': version,
      'X-Restli-Protocol-Version': '2.0.0',
    },
    body: JSON.stringify({
      initializeUploadRequest: {
        owner,
      },
    }),
  });
  const initText = await initResponse.text();
  let initPayload = {};
  try { initPayload = JSON.parse(initText); } catch { initPayload = { raw: initText }; }
  if (!initResponse.ok) {
    throw new Error(`LinkedIn image upload init failed: ${initResponse.status} ${initResponse.statusText}: ${initText.slice(0, 500)}`);
  }
  const value = initPayload.value || initPayload;
  const uploadUrl = value.uploadUrl;
  const imageUrn = value.image;
  if (!uploadUrl || !imageUrn) {
    throw new Error(`LinkedIn image upload init returned unexpected payload: ${JSON.stringify(initPayload).slice(0, 500)}`);
  }

  const binary = fs.readFileSync(imagePath);
  const uploadResponse = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'image/png',
    },
    body: binary,
  });
  const uploadText = await uploadResponse.text();
  if (!uploadResponse.ok) {
    throw new Error(`LinkedIn image binary upload failed: ${uploadResponse.status} ${uploadResponse.statusText}: ${uploadText.slice(0, 500)}`);
  }
  return imageUrn;
}

async function publishPinterestViaBlotato(draft, imagePath, options = {}) {
  if (PINTEREST_DISABLED) {
    const skipped = {
      ok: false,
      skipped: 'Pinterest disabled by explicit PINTEREST_DISABLED setting',
      account_id: BLOTATO_PINTEREST_ACCOUNT_ID || null,
      board_id: BLOTATO_PINTEREST_BOARD_ID || null,
    };
    appendJsonl(PINTEREST_LOG_FILE, {
      ...skipped,
      id: draft.id,
      target_url: draft.target_url,
      created_at: new Date().toISOString(),
    });
    return skipped;
  }
  const nowDate = options.date || today();
  const duplicate = recentPinterestDuplicate(draft.target_url, nowDate);
  if (duplicate && !options.allowDuplicate) {
    const skipped = {
      ok: false,
      skipped: 'duplicate target_url blocked',
      target_url: draft.target_url,
      duplicate,
      account_id: BLOTATO_PINTEREST_ACCOUNT_ID,
      board_id: BLOTATO_PINTEREST_BOARD_ID || null,
    };
    appendJsonl(PINTEREST_LOG_FILE, {
      ...skipped,
      id: draft.id,
      created_at: new Date().toISOString(),
    });
    return skipped;
  }
  if (!BLOTATO_PINTEREST_BOARD_ID) {
    const skipped = {
      ok: false,
      skipped: 'missing BLOTATO_PINTEREST_BOARD_ID',
      account_id: BLOTATO_PINTEREST_ACCOUNT_ID,
    };
    appendJsonl(PINTEREST_LOG_FILE, {
      ...skipped,
      id: draft.id,
      target_url: draft.target_url,
      created_at: new Date().toISOString(),
    });
    return skipped;
  }
  const pinPath = imagePath && fs.existsSync(imagePath) ? imagePath : renderPinterestPinForDraft(draft);
  const mediaUrl = copyCardToCdn(pinPath, draft, '-pin');
  const body = {
    accountId: BLOTATO_PINTEREST_ACCOUNT_ID,
    platform: 'pinterest',
    text: makePinterestDescription(draft),
    mediaUrls: [mediaUrl],
    boardId: BLOTATO_PINTEREST_BOARD_ID,
    title: draft.title,
    link: draft.target_url,
  };
  const response = await fetch(`${BLOTATO_PROXY}/publish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  let payload = null;
  try { payload = JSON.parse(text); } catch { payload = { raw: text }; }
  const result = {
    ok: blotatoPublishSucceeded(response.ok, payload),
    status: `${response.status} ${response.statusText}`,
    account_id: BLOTATO_PINTEREST_ACCOUNT_ID,
    board_id: BLOTATO_PINTEREST_BOARD_ID,
    media_url: mediaUrl,
    pin_image_path: pinPath,
    payload,
  };
  appendJsonl(PINTEREST_LOG_FILE, {
    ...result,
    id: draft.id,
    target_url: draft.target_url,
    created_at: new Date().toISOString(),
  });
  return result;
}

async function createLinkedInPost(env, draft) {
  const author = env.LINKEDIN_ORGANIZATION_URN;
  const accessToken = env.LINKEDIN_ACCESS_TOKEN;
  if (!author) throw new Error('Missing LINKEDIN_ORGANIZATION_URN');
  if (!accessToken) throw new Error('Missing LINKEDIN_ACCESS_TOKEN');
  const imagePath = renderPinterestPinForDraft(draft);
  const imageUrn = await uploadLinkedInImage(env, imagePath);
  draft.linkedin_image_urn = imageUrn;
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
      media: {
        id: imageUrn,
        title: draft.title,
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
  return {
    postUrn: response.headers.get('x-restli-id') || text.trim() || null,
    imagePath,
    imageUrn,
  };
}

async function publishApproved(dryRun, options = {}) {
  const env = loadEnv();
  const queue = options.queue || loadQueue();
  const state = options.state || loadState();
  const nowDate = today(options.dateArg);
  const week = isoWeek(nowDate);
  const used = postsThisWeek(state, week);
  if (used >= WEEKLY_CAP) {
    console.log(JSON.stringify({ ok: true, published: [], skipped: `weekly cap reached (${used}/${WEEKLY_CAP})` }, null, 2));
    return { published: [], skipped: `weekly cap reached (${used}/${WEEKLY_CAP})`, weekly_used_after: used };
  }
  const allowed = Math.max(0, Math.min(options.limit || WEEKLY_CAP, WEEKLY_CAP - used));

  const candidates = queue.drafts
    .filter((draft) => draft.status === 'approved' && draft.scheduled_date <= nowDate)
    .sort((a, b) => `${a.scheduled_date}:${a.id}`.localeCompare(`${b.scheduled_date}:${b.id}`));

  const published = [];
  const skipped = [];
  for (const draft of candidates) {
    if (published.length >= allowed) break;
    const duplicate = recentLinkedInDuplicate(draft.target_url, nowDate, state);
    if (duplicate) {
      const record = {
        id: draft.id,
        target_url: draft.target_url,
        skipped: 'duplicate linkedin target_url blocked',
        duplicate,
        created_at: new Date().toISOString(),
      };
      skipped.push(record);
      if (!dryRun) {
        draft.status = 'blocked_duplicate';
        draft.blocked_at = record.created_at;
        draft.blocked_reason = record.skipped;
        draft.blocked_duplicate = duplicate;
        appendJsonl(LOG_FILE, record);
      }
      continue;
    }
    let postUrn = null;
    let imagePath = draft.image_path || null;
    let imageUrn = draft.linkedin_image_urn || null;
    if (!dryRun) postUrn = await createLinkedInPost(env, draft);
    if (!dryRun && postUrn && typeof postUrn === 'object') {
      imagePath = postUrn.imagePath;
      imageUrn = postUrn.imageUrn;
      postUrn = postUrn.postUrn;
    }
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
        linkedin_image_urn: imageUrn,
        image_path: imagePath,
        pinterest_blotato_result: null,
      };
      state.published.push(record);
      appendJsonl(LOG_FILE, record);
    }
    published.push({
      id: draft.id,
      target_url: draft.target_url,
      linkedin_post_urn: postUrn,
      linkedin_image_urn: imageUrn,
      image_path: imagePath,
      pinterest_blotato_result: null,
    });
  }
  if (!dryRun) {
    saveQueue(queue);
    saveState(state);
  }
  const result = { ok: true, dry_run: dryRun, published, skipped, weekly_used_after: used + published.length };
  console.log(JSON.stringify(result, null, 2));
  return result;
}

async function runScheduledResources(args) {
  const dryRun = args.includes('--dry-run');
  const dateArg = args.includes('--date') ? args[args.indexOf('--date') + 1] : args.find((arg) => arg.startsWith('--date='))?.slice(7);
  const queue = loadQueue();
  const state = loadState();
  const draftResult = draftWeek(dateArg, { queue, dryRun, silent: true });
  const approved = approveDueResourceDrafts(dateArg, { queue, dryRun });
  const publishResult = await publishApproved(dryRun, { dateArg, limit: 1, queue, state });
  console.log(JSON.stringify({
    ok: true,
    command: 'run-scheduled-resources',
    date: today(dateArg),
    dry_run: dryRun,
    draft_result: draftResult,
    auto_approved: approved,
    publish_result: publishResult,
  }, null, 2));
}

async function runScheduledPinterest(args) {
  if (PINTEREST_DISABLED) {
    console.log(JSON.stringify({
      ok: true,
      command: 'run-scheduled-pinterest',
      published: null,
      skipped: 'Pinterest disabled by explicit PINTEREST_DISABLED setting',
    }, null, 2));
    return;
  }
  const dryRun = args.includes('--dry-run');
  const dateArg = args.includes('--date') ? args[args.indexOf('--date') + 1] : args.find((arg) => arg.startsWith('--date='))?.slice(7);
  const nowDate = today(dateArg);
  const state = loadPinterestState();
  const lastDate = state.last_published_date || null;
  const daysSinceLast = lastDate ? daysBetween(lastDate, nowDate) : null;
  const due = !lastDate || daysSinceLast >= PINTEREST_INTERVAL_DAYS;
  if (!due) {
    console.log(JSON.stringify({
      ok: true,
      command: 'run-scheduled-pinterest',
      dry_run: dryRun,
      date: nowDate,
      published: null,
      skipped: `not due; last successful pin was ${lastDate}`,
      days_since_last: daysSinceLast,
      interval_days: PINTEREST_INTERVAL_DAYS,
    }, null, 2));
    return;
  }

  const { campaign, index, skipped_recent: skippedRecent } = pickPinterestCampaign(state, nowDate);
  if (!campaign) {
    console.log(JSON.stringify({
      ok: true,
      command: 'run-scheduled-pinterest',
      dry_run: dryRun,
      date: nowDate,
      published: null,
      skipped: 'no non-duplicate campaign available inside repeat block',
      block_days: CROSS_CHANNEL_TARGET_REPEAT_BLOCK_DAYS,
    }, null, 2));
    return;
  }
  const draft = buildPinterestDraft(campaign, nowDate);
  const pinPath = renderPinterestPinForDraft(draft);
  const description = makePinterestDescription(draft);

  if (dryRun) {
    console.log(JSON.stringify({
      ok: true,
      command: 'run-scheduled-pinterest',
      dry_run: true,
      date: nowDate,
      due: true,
      next_campaign_index: index,
      skipped_recent_targets: skippedRecent,
      draft: {
        id: draft.id,
        title: draft.title,
        target_url: draft.target_url,
        pin_image_path: pinPath,
        description,
      },
    }, null, 2));
    return;
  }

  const result = await publishPinterestViaBlotato(draft, pinPath);
  if (result.ok) {
    state.last_published_date = nowDate;
    state.next_campaign_index = index + 1;
    state.published = Array.isArray(state.published) ? state.published : [];
    state.published.push({
      id: draft.id,
      campaign_slug: draft.campaign_slug,
      title: draft.title,
      target_url: draft.target_url,
      published_at: new Date().toISOString(),
      pin_image_path: result.pin_image_path || pinPath,
      media_url: result.media_url || null,
      blotato_result: result,
    });
    savePinterestState(state);
  }

  console.log(JSON.stringify({
    ok: Boolean(result.ok),
    command: 'run-scheduled-pinterest',
    dry_run: false,
    date: nowDate,
    draft: {
      id: draft.id,
      title: draft.title,
      target_url: draft.target_url,
      pin_image_path: pinPath,
    },
    pinterest_result: result,
    next_run_after_success: result.ok ? addDays(nowDate, PINTEREST_INTERVAL_DAYS) : null,
  }, null, 2));
}

function previewPinterestWeek(args) {
  const dateArg = args.includes('--date') ? args[args.indexOf('--date') + 1] : args.find((arg) => arg.startsWith('--date='))?.slice(7);
  const daysArg = args.includes('--days') ? args[args.indexOf('--days') + 1] : args.find((arg) => arg.startsWith('--days='))?.slice(7);
  const startDate = today(dateArg);
  const days = Math.max(1, Number(daysArg || 7));
  const simulatedState = JSON.parse(JSON.stringify(loadPinterestState()));
  const scheduled = [];

  for (let offset = 0; offset < days; offset += 1) {
    const scheduledDate = addDays(startDate, offset);
    const lastDate = simulatedState.last_published_date || null;
    const daysSinceLast = lastDate ? daysBetween(lastDate, scheduledDate) : null;
    const due = !lastDate || daysSinceLast >= PINTEREST_INTERVAL_DAYS;
    if (!due) continue;

    const { campaign, index, skipped_recent: skippedRecent } = pickPinterestCampaign(simulatedState, scheduledDate);
    if (!campaign) {
      scheduled.push({
        date: scheduledDate,
        skipped: 'no non-duplicate campaign available inside repeat block',
      });
      continue;
    }

    const draft = buildPinterestDraft(campaign, scheduledDate);
    const pinPath = renderPinterestPinForDraft(draft);
    const description = makePinterestDescription(draft);
    scheduled.push({
      date: scheduledDate,
      campaign_index: index,
      skipped_recent_targets: skippedRecent,
      id: draft.id,
      title: draft.title,
      target_url: draft.target_url,
      pin_image_path: pinPath,
      description,
    });

    simulatedState.last_published_date = scheduledDate;
    simulatedState.next_campaign_index = index + 1;
  }

  console.log(JSON.stringify({
    ok: true,
    command: 'preview-pinterest-week',
    start_date: startDate,
    days,
    interval_days: PINTEREST_INTERVAL_DAYS,
    scheduled,
  }, null, 2));
}

function duplicateGroups(records, nowDate, blockDays) {
  const byTarget = new Map();
  const seen = new Set();
  for (const record of records) {
    const date = String(record.created_at || '').slice(0, 10);
    if (!date) continue;
    const ageDays = daysBetween(date, nowDate);
    if (ageDays < 0 || ageDays >= blockDays) continue;
    const recordKey = record.public_url || `${record.id}:${record.target_url}:${record.created_at}`;
    if (seen.has(recordKey)) continue;
    seen.add(recordKey);
    if (!byTarget.has(record.target_url)) byTarget.set(record.target_url, []);
    byTarget.get(record.target_url).push({
      id: record.id,
      created_at: record.created_at,
      age_days: ageDays,
      public_url: record.public_url || null,
      source: record.source || null,
    });
  }
  return [...byTarget.entries()]
    .map(([target_url, entries]) => ({
      target_url,
      count: entries.length,
      entries: entries.sort((a, b) => String(a.created_at).localeCompare(String(b.created_at))),
    }))
    .filter((group) => group.count > 1)
    .sort((a, b) => b.count - a.count || a.target_url.localeCompare(b.target_url));
}

function auditSocialDuplicates(args) {
  const dateArg = args.includes('--date') ? args[args.indexOf('--date') + 1] : args.find((arg) => arg.startsWith('--date='))?.slice(7);
  const nowDate = today(dateArg);
  const splitHistorical = (groups) => {
    const active = [];
    const historical = [];
    for (const group of groups) {
      const latestDate = group.entries
        .map((entry) => String(entry.created_at || '').slice(0, 10))
        .sort()
        .at(-1);
      if (latestDate && latestDate < SOCIAL_DUPLICATE_GUARD_EFFECTIVE_DATE) {
        historical.push(group);
      } else {
        active.push(group);
      }
    }
    return { active, historical };
  };
  const linkedinSplit = splitHistorical(duplicateGroups(successfulLinkedInRecords(), nowDate, LINKEDIN_TARGET_REPEAT_BLOCK_DAYS));
  const pinterestSplit = splitHistorical(duplicateGroups(successfulPinterestRecords(), nowDate, PINTEREST_TARGET_REPEAT_BLOCK_DAYS));
  const activeDuplicateCount = linkedinSplit.active.length + pinterestSplit.active.length;
  console.log(JSON.stringify({
    ok: activeDuplicateCount === 0,
    command: 'audit-social-duplicates',
    date: nowDate,
    guard_effective_date: SOCIAL_DUPLICATE_GUARD_EFFECTIVE_DATE,
    linkedin_repeat_block_days: LINKEDIN_TARGET_REPEAT_BLOCK_DAYS,
    pinterest_repeat_block_days: PINTEREST_TARGET_REPEAT_BLOCK_DAYS,
    linkedin_duplicate_targets: linkedinSplit.active,
    pinterest_duplicate_targets: pinterestSplit.active,
    historical_linkedin_duplicate_targets: linkedinSplit.historical,
    historical_pinterest_duplicate_targets: pinterestSplit.historical,
  }, null, 2));
  if (activeDuplicateCount > 0) {
    process.exitCode = 1;
  }
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
  else if (command === 'set-pinterest-account') setPinterestAccount(args[0]);
  else if (command === 'set-pinterest-board') setPinterestBoard(args[0]);
  else if (command === 'draft-week') {
    const dateArg = args.includes('--date') ? args[args.indexOf('--date') + 1] : args.find((arg) => arg.startsWith('--date='))?.slice(7);
    draftWeek(dateArg);
  } else if (command === 'status') status();
  else if (command === 'approve') approve(args[0]);
  else if (command === 'render-card') renderCardCommand(args[0]);
  else if (command === 'publish-approved') {
    const limitArg = args.includes('--limit') ? args[args.indexOf('--limit') + 1] : args.find((arg) => arg.startsWith('--limit='))?.slice(8);
    await publishApproved(args.includes('--dry-run'), { limit: limitArg ? Number(limitArg) : undefined });
  } else if (command === 'run-scheduled-resources' || command === 'run-scheduled-tools') await runScheduledResources(args);
  else if (command === 'run-scheduled-pinterest') await runScheduledPinterest(args);
  else if (command === 'preview-pinterest-week') previewPinterestWeek(args);
  else if (command === 'audit-social-duplicates') auditSocialDuplicates(args);
  else {
    usage();
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
