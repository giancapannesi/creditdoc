import type { APIRoute } from 'astro';

export const prerender = false;

interface RuntimeEnv {
  SUPABASE_URL?: string;
  SUPABASE_ANON_KEY?: string;
}

interface IntakePayload {
  email?: string;
  name?: string;
  source_page?: string;
  tool_id?: string;
  result_label?: string;
  responses?: Record<string, unknown>;
  utm?: Record<string, string>;
  consent_marketing?: boolean;
  capture_only?: boolean;
  honeypot?: string;
  elapsed_ms?: number;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_JSON_BYTES = 20000;
const RATE_LIMIT_WINDOW_MS = 60 * 60 * 1000;
const RATE_LIMIT_MAX = 12;
const rateBuckets = new Map<string, { count: number; resetAt: number }>();

const TOOL_CONFIG = {
  'credit-repair-qualify-quiz': {
    pillar: 'credit-repair',
    sourcePage: '/tools/credit-repair-qualify-quiz/',
    answerValues: {
      session_id: null,
      reportStatus: ['recent-errors', 'recent-no-errors', 'not-recent'],
      negativeItems: ['errors', 'collections', 'thin-file', 'utilization'],
      accuracy: ['not-accurate', 'mixed', 'accurate'],
      timeline: ['mortgage-loan', 'rent-job', 'general'],
      capacity: ['yes', 'maybe', 'no'],
      risk: ['yes', 'no', 'not-sure'],
    },
    results: {
      repair_research: {
        recommended_route: '/best/best-credit-repair-companies/',
        title: 'Credit repair research may be worth comparing',
      },
      build_first: {
        recommended_route: '/tools/credit-score-simulator/',
        title: 'Credit building or debt steps may matter more first',
      },
      review_first: {
        recommended_route: '/resources/credit-report-checklist/',
        title: 'Start with report review before hiring anyone',
      },
    },
  },
  'business-loan-readiness-quiz': {
    pillar: 'business-loans',
    sourcePage: '/tools/business-loan-readiness-quiz/',
    answerValues: {
      session_id: null,
      timeInBusiness: ['startup', '6-12', '12-24', '24plus'],
      monthlyRevenue: ['pre-revenue', 'under10k', '10k-25k', '25k-75k', '75kplus'],
      creditRange: ['unknown', 'under580', '580-619', '620-679', '680plus'],
      fundingUse: ['working-capital', 'equipment', 'startup', 'debt-refi', 'fast-cash'],
      docsReady: ['ready', 'partial', 'weak'],
      cashFlowPressure: ['low', 'medium', 'high'],
    },
    results: {
      bank_sba_ready: {
        recommended_route: '/best/best-sba-loans/',
        title: 'Bank or SBA research may be worth comparing',
      },
      alternative_lender_fit: {
        recommended_route: '/best/best-small-business-loans/',
        title: 'Alternative business loan research may fit first',
      },
      startup_build_path: {
        recommended_route: '/best/best-startup-business-loans/',
        title: 'Startup funding and document-building path',
      },
      cash_flow_caution: {
        recommended_route: '/answers/merchant-cash-advance-guide/',
        title: 'Cash-flow pressure needs careful review',
      },
      repair_docs_first: {
        recommended_route: '/tools/loan-denial-reason-checker/',
        title: 'Documents, credit, or denial-risk factors need review first',
      },
    },
  },
} as const;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json',
      'cache-control': 'no-store',
    },
  });
}

function cleanText(value: unknown, max = 240): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim().replace(/\s+/g, ' ');
  return trimmed ? trimmed.slice(0, max) : null;
}

function cleanObject(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  const serialized = JSON.stringify(value);
  if (serialized.length > MAX_JSON_BYTES) return {};
  return value as Record<string, unknown>;
}

function sameOrigin(request: Request): boolean {
  const requestHost = new URL(request.url).host;
  const origin = request.headers.get('origin');
  const referer = request.headers.get('referer');
  try {
    if (origin) return new URL(origin).host === requestHost;
    if (referer) return new URL(referer).host === requestHost;
    return false;
  } catch {
    return false;
  }
}

function rateLimitKey(request: Request): string {
  return clientIp(request) || request.headers.get('user-agent') || 'unknown';
}

function isRateLimited(request: Request): boolean {
  const now = Date.now();
  const key = rateLimitKey(request);
  const existing = rateBuckets.get(key);
  if (!existing || existing.resetAt <= now) {
    rateBuckets.set(key, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS });
    return false;
  }
  existing.count += 1;
  return existing.count > RATE_LIMIT_MAX;
}

function containsSensitiveRawData(value: Record<string, unknown>): boolean {
  const serialized = JSON.stringify(value).toLowerCase();
  return (
    /\b\d{3}-\d{2}-\d{4}\b/.test(serialized) ||
    /\b\d{9}\b/.test(serialized) ||
    serialized.includes('social security') ||
    serialized.includes('ssn') ||
    serialized.includes('routing number') ||
    serialized.includes('bank login') ||
    serialized.includes('password')
  );
}

function sanitizeResponses(
  tool: keyof typeof TOOL_CONFIG,
  responses: Record<string, unknown>
): Record<string, string> | null {
  const config = TOOL_CONFIG[tool];
  const clean: Record<string, string> = {};

  for (const [key, allowed] of Object.entries(config.answerValues)) {
    const raw = responses[key];
    if (key === 'session_id') {
      const sessionId = cleanText(raw, 128);
      if (sessionId) clean.session_id = sessionId;
      continue;
    }
    if (typeof raw !== 'string' || !Array.isArray(allowed) || !allowed.includes(raw as never)) {
      return null;
    }
    clean[key] = raw;
  }

  return clean;
}

function clientIp(request: Request): string | null {
  return (
    request.headers.get('cf-connecting-ip') ||
    request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
    null
  );
}

async function postgrestInsert(
  env: RuntimeEnv,
  table: 'lead_captures' | 'user_quiz_responses',
  payload: Record<string, unknown>
): Promise<void> {
  const res = await fetch(`${env.SUPABASE_URL}/rest/v1/${table}`, {
    method: 'POST',
    headers: {
      apikey: env.SUPABASE_ANON_KEY || '',
      authorization: `Bearer ${env.SUPABASE_ANON_KEY || ''}`,
      'content-type': 'application/json',
      prefer: 'return=minimal',
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(5000),
  });

  if (!res.ok) {
    await res.text();
    throw new Error(`${table} insert failed`);
  }
}

export const POST: APIRoute = async ({ request, locals }) => {
  const env = ((locals as any)?.runtime?.env || {}) as RuntimeEnv;
  if (!env.SUPABASE_URL || !env.SUPABASE_ANON_KEY) {
    return json({ ok: false, error: 'Supabase runtime env is not configured' }, 503);
  }

  if (!sameOrigin(request)) {
    return json({ ok: false, error: 'Request rejected' }, 403);
  }

  if (isRateLimited(request)) {
    return json({ ok: false, error: 'Too many requests' }, 429);
  }

  let payload: IntakePayload;
  try {
    payload = (await request.json()) as IntakePayload;
  } catch {
    return json({ ok: false, error: 'Invalid JSON body' }, 400);
  }

  if (cleanText(payload.honeypot, 200)) {
    return json({ ok: false, error: 'Request rejected' }, 400);
  }

  if (payload.email && Number(payload.elapsed_ms || 0) < 2500) {
    return json({ ok: false, error: 'Request rejected' }, 400);
  }

  const email = cleanText(payload.email, 320)?.toLowerCase() || null;
  const name = cleanText(payload.name, 160);
  const toolId = cleanText(payload.tool_id, 100) as keyof typeof TOOL_CONFIG | null;
  if (!toolId || !(toolId in TOOL_CONFIG)) {
    return json({ ok: false, error: 'Unknown tool' }, 400);
  }

  const config = TOOL_CONFIG[toolId];
  const pillar = config.pillar;
  const sourcePage = cleanText(payload.source_page, 500);
  const resultLabel = cleanText(payload.result_label, 100);
  if (!resultLabel || !(resultLabel in config.results)) {
    return json({ ok: false, error: 'Unknown result' }, 400);
  }

  const resultConfig = config.results[resultLabel as keyof typeof config.results];
  const responses = cleanObject(payload.responses);
  const utm = cleanObject(payload.utm);
  const userAgent = cleanText(request.headers.get('user-agent'), 500);
  const ip = clientIp(request);
  const captureOnly = payload.capture_only === true;

  if (email && !EMAIL_RE.test(email)) {
    return json({ ok: false, error: 'Invalid email' }, 400);
  }

  if (captureOnly && !email) {
    return json({ ok: false, error: 'Email is required for lead capture' }, 400);
  }

  if (sourcePage !== config.sourcePage) {
    return json({ ok: false, error: 'Invalid source page' }, 400);
  }

  if (containsSensitiveRawData(responses) || containsSensitiveRawData(utm)) {
    return json({ ok: false, error: 'Sensitive raw data is not accepted here' }, 400);
  }

  const safeResponses = sanitizeResponses(toolId, responses);
  if (!safeResponses) {
    return json({ ok: false, error: 'Invalid response payload' }, 400);
  }

  const sessionId =
    cleanText(safeResponses.session_id || null, 128) ||
    crypto.randomUUID();
  safeResponses.session_id = sessionId;
  const writes = {
    user_quiz_responses: false,
    lead_captures: false,
  };

  try {
    if (!captureOnly) {
      await postgrestInsert(env, 'user_quiz_responses', {
        session_id: sessionId,
        pillar,
        email,
        responses: {
          ...safeResponses,
          tool_id: toolId,
          capture_type: 'completion',
        },
        result_payload: {
          result_label: resultLabel,
          recommended_route: resultConfig.recommended_route,
          title: resultConfig.title,
          source_page: sourcePage,
          capture_type: 'completion',
        },
        ip,
        user_agent: userAgent,
        referrer: request.headers.get('referer'),
        utm,
      });
      writes.user_quiz_responses = true;
    }

    if (email) {
      await postgrestInsert(env, 'lead_captures', {
        email,
        name,
        source_page: sourcePage,
        pillar,
        utm,
        ip,
        user_agent: userAgent,
        consent_marketing: false,
      });
      writes.lead_captures = true;
    }
  } catch (err) {
    console.error('[origination-intake]', (err as Error).message);
    return json({ ok: false, error: 'Intake save failed' }, 502);
  }

  return json({
    ok: true,
    session_id: sessionId,
    capture: {
      email,
      name,
      tool_id: toolId,
      pillar,
      source_page: sourcePage,
      result_label: resultLabel,
      result_title: resultConfig.title,
      recommended_route: resultConfig.recommended_route,
      consent_marketing: false,
      writes,
    },
  });
};

export const GET: APIRoute = async () =>
  json({ ok: false, error: 'POST only' }, 405);
