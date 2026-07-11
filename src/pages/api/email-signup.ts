import type { APIRoute } from 'astro';

export const prerender = false;

interface SignupPayload {
  email?: string;
  name?: string;
  signup_type?: string;
  source_page?: string;
  honeypot?: string;
  elapsed_ms?: number;
}

interface RuntimeEnv {
  SUPABASE_URL?: string;
  SUPABASE_ANON_KEY?: string;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const SENDY_URL = 'https://sendy.creditdoc.co/subscribe';
const RATE_LIMIT_WINDOW_MS = 60 * 60 * 1000;
const RATE_LIMIT_MAX = 12;
const rateBuckets = new Map<string, { count: number; resetAt: number }>();

const SIGNUP_TYPES = {
  'credit-fundamentals-course': {
    list: 'Yj7BPjltZ5YG9nUBw892y93g',
    list_name: 'Credit Fundamentals Course',
    pillar: 'credit-education',
    write_lead_capture: true,
    consent_marketing: true,
    allowed_sources: [
      '/courses/credit-fundamentals/',
      '/courses/credit-fundamentals/understanding-your-credit-score/',
      '/courses/credit-fundamentals/how-to-read-your-credit-report/',
      '/courses/credit-fundamentals/building-credit-from-scratch/',
      '/courses/credit-fundamentals/managing-debt-effectively/',
      '/courses/credit-fundamentals/credit-repair-diy-vs-hiring-help/',
      '/courses/credit-fundamentals/personal-loans-and-borrowing-smart/',
      '/courses/credit-fundamentals/avoiding-scams-and-predatory-lending/',
      '/courses/credit-fundamentals/know-your-rights/',
    ],
  },
  'credit-repair-quiz': {
    list: 'rCzcu8brUim88T892Y85IqRQ',
    list_name: 'Credit Repair Quiz Leads',
    pillar: 'credit-repair',
    write_lead_capture: false,
    consent_marketing: false,
    allowed_sources: ['/tools/credit-repair-qualify-quiz/'],
  },
  'business-loan-readiness': {
    list: 'rCzcu8brUim88T892Y85IqRQ',
    list_name: 'Credit Repair Quiz Leads',
    pillar: 'business-loans',
    write_lead_capture: false,
    consent_marketing: false,
    allowed_sources: ['/tools/business-loan-readiness-quiz/'],
  },
  'borrowing-power': {
    list: 'rCzcu8brUim88T892Y85IqRQ',
    list_name: 'Credit Repair Quiz Leads',
    pillar: 'personal-loans',
    write_lead_capture: true,
    consent_marketing: false,
    allowed_sources: ['/tools/borrowing-power-quiz/'],
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

function clientIp(request: Request): string | null {
  return (
    request.headers.get('cf-connecting-ip') ||
    request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
    null
  );
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

function isRateLimited(request: Request): boolean {
  const now = Date.now();
  const key = clientIp(request) || request.headers.get('user-agent') || 'unknown';
  const existing = rateBuckets.get(key);
  if (!existing || existing.resetAt <= now) {
    rateBuckets.set(key, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS });
    return false;
  }
  existing.count += 1;
  return existing.count > RATE_LIMIT_MAX;
}

async function postgrestInsert(
  env: RuntimeEnv,
  table: 'lead_captures',
  payload: Record<string, unknown>
): Promise<void> {
  if (!env.SUPABASE_URL || !env.SUPABASE_ANON_KEY) return;

  const res = await fetch(`${env.SUPABASE_URL}/rest/v1/${table}`, {
    method: 'POST',
    headers: {
      apikey: env.SUPABASE_ANON_KEY,
      authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
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
  if (!sameOrigin(request)) {
    return json({ ok: false, error: 'Request rejected' }, 403);
  }
  if (isRateLimited(request)) {
    return json({ ok: false, error: 'Too many requests' }, 429);
  }

  let payload: SignupPayload;
  try {
    payload = (await request.json()) as SignupPayload;
  } catch {
    return json({ ok: false, error: 'Invalid JSON body' }, 400);
  }

  if (cleanText(payload.honeypot, 200)) {
    return json({ ok: false, error: 'Request rejected' }, 400);
  }
  if (Number(payload.elapsed_ms || 0) < 1500) {
    return json({ ok: false, error: 'Request rejected' }, 400);
  }

  const email = cleanText(payload.email, 320)?.toLowerCase() || '';
  const name = cleanText(payload.name, 160) || '';
  const sourcePage = cleanText(payload.source_page, 500) || '';
  const signupType = cleanText(payload.signup_type, 100) as keyof typeof SIGNUP_TYPES | null;
  if (!email || !EMAIL_RE.test(email)) {
    return json({ ok: false, error: 'Invalid email' }, 400);
  }
  if (!signupType || !(signupType in SIGNUP_TYPES)) {
    return json({ ok: false, error: 'Unknown signup type' }, 400);
  }

  const config = SIGNUP_TYPES[signupType];
  if (!config.allowed_sources.includes(sourcePage as never)) {
    return json({ ok: false, error: 'Invalid source page' }, 400);
  }

  const body = new URLSearchParams({
    list: config.list,
    email,
    name,
    boolean: 'true',
  });
  const sendyRes = await fetch(SENDY_URL, {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
    signal: AbortSignal.timeout(7000),
  }).catch((err) => err as Error);

  if (sendyRes instanceof Error) {
    console.error('[email-signup]', sendyRes.message);
    return json({ ok: false, error: 'Email signup failed' }, 502);
  }

  const sendyText = await sendyRes.text();
  const normalized = sendyText.trim();
  const accepted = normalized === '1' || normalized.toLowerCase().includes('already subscribed');
  if (!accepted) {
    console.error('[email-signup] sendy rejected:', normalized.slice(0, 200));
    return json({ ok: false, error: 'Email signup rejected' }, 502);
  }

  const writes = {
    sendy_subscribers: true,
    lead_captures: false,
  };

  if (config.write_lead_capture) {
    try {
      await postgrestInsert(env, 'lead_captures', {
        email,
        name,
        source_page: sourcePage,
        pillar: config.pillar,
        utm: {},
        ip: clientIp(request),
        user_agent: cleanText(request.headers.get('user-agent'), 500),
        consent_marketing: config.consent_marketing,
      });
      writes.lead_captures = true;
    } catch (err) {
      console.error('[email-signup]', (err as Error).message);
      return json({ ok: false, error: 'Signup save failed' }, 502);
    }
  }

  return json({
    ok: true,
    signup: {
      email,
      name,
      signup_type: signupType,
      source_page: sourcePage,
      list_name: config.list_name,
      sendy_status: normalized === '1' ? 'subscribed' : 'already_subscribed',
      writes,
    },
  });
};

export const GET: APIRoute = async () =>
  json({ ok: false, error: 'POST only' }, 405);
