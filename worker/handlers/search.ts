/**
 * /api/search — PostgREST-backed lender search.
 * Ported from src/pages/api/search.ts (245 LoC).
 *
 * Handles free-text (q) + category + state + BBB + money-back-guarantee +
 * free-consultation filters. Overfetches 4× the limit, applies quality
 * gate + BBB filter + ranking pass, returns compact result set.
 */
import { normalizedBbbRating } from "../../src/utils/data";
import type { Env } from "../index";

interface BodyInline {
  rating?: number;
  google_rating?: number;
  description_short?: string;
  services?: string[];
  best_for?: string[];
  states_served?: string[];
  cities_served?: string[];
  google_reviews_count?: number;
  quality_score?: number;
  has_been_enriched?: boolean;
  data_source?: string;
  subcategories?: string[];
  pricing?: {
    monthly_price?: number;
    setup_fee?: number;
    money_back_guarantee?: boolean;
    free_consultation?: boolean;
  };
  company_info?: {
    bbb_rating?: string;
  };
}

interface RawLender {
  slug: string;
  name: string;
  category: string;
  state: string | null;
  state_abbr: string | null;
  brand_slug: string | null;
  body_inline: BodyInline | null;
}

const SAFE = /[^a-z0-9 \-_'&.,/]/gi;
function sanitizeSearchTerm(s: string): string {
  return s.replace(SAFE, "").replace(/[%_*]/g, "").slice(0, 80).trim();
}

function pcEnc(s: string): string {
  return encodeURIComponent(s).replace(/'/g, "%27");
}

function slugify(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

function compact(r: RawLender) {
  const b = r.body_inline || {};
  const gr = b.google_rating;
  const grc = b.google_reviews_count;
  const rating =
    gr && gr > 0 && !(gr > 5) && grc && grc >= 1 ? gr : 0;
  return {
    s: r.slug,
    n: r.name,
    c: r.category,
    sc: b.subcategories || [],
    r: rating,
    mp: b.pricing?.monthly_price || 0,
    bb: normalizedBbbRating(b.company_info?.bbb_rating),
    mg: !!b.pricing?.money_back_guarantee,
    fc: !!b.pricing?.free_consultation,
    st: b.states_served || [],
    ct: (b.cities_served || []).slice(0, 30),
    ds: (b.description_short || "").slice(0, 200),
    bf: (b.best_for || []).slice(0, 3),
    gr: b.google_reviews_count || 0,
    qs: b.quality_score || 0,
    en:
      b.has_been_enriched ||
      b.data_source === "enriched" ||
      b.data_source === "editorial" ||
      b.data_source === "verified"
        ? 1
        : 0,
    br: r.brand_slug,
  };
}

function json(body: unknown, status: number, extraHeaders: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...extraHeaders },
  });
}

export async function handleSearch(request: Request, env: Env): Promise<Response> {
  if (!env.SUPABASE_URL || !env.SUPABASE_ANON_KEY) {
    return json({ error: "config" }, 500);
  }
  const url = new URL(request.url);
  const sp = url.searchParams;
  const q = sanitizeSearchTerm(sp.get("q") || "");
  const category = (sp.get("category") || "").trim();
  const state = (sp.get("state") || "").trim();
  const stateAbbr = (sp.get("state_abbr") || "").trim().toUpperCase();
  const bbbFilter = (sp.get("bbb") || "").trim();
  const guarantee = sp.get("guarantee") === "1";
  const freeConsult = sp.get("free_consult") === "1";
  const bbbAPlus = sp.get("bbb_a_plus") === "1";
  const limit = Math.min(parseInt(sp.get("limit") || "200", 10) || 200, 500);

  const params = new URLSearchParams();
  params.set(
    "select",
    "slug,name,category,state,state_abbr,brand_slug,body_inline",
  );
  params.set("processing_status", "eq.ready_for_index");
  params.set("limit", String(Math.min(limit * 4, 1000)));

  if (category) params.set("category", `eq.${pcEnc(category)}`);
  if (stateAbbr) {
    params.set("state_abbr", `eq.${stateAbbr}`);
  } else if (state) {
    params.append(
      "or",
      `(state.ilike.*${pcEnc(state)}*,body_inline->states_served.cs.${pcEnc(JSON.stringify([state]))})`,
    );
  }
  if (q) {
    params.append(
      "or",
      `(name.ilike.*${pcEnc(q)}*,body_inline->>description_short.ilike.*${pcEnc(q)}*,body_inline->>services.ilike.*${pcEnc(q)}*,brand_slug.ilike.*${pcEnc(slugify(q))}*)`,
    );
  }

  const supaUrl = `${env.SUPABASE_URL}/rest/v1/lenders?${params.toString()}`;

  let rows: RawLender[] = [];
  try {
    const res = await fetch(supaUrl, {
      headers: {
        apikey: env.SUPABASE_ANON_KEY,
        authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
        accept: "application/json",
      },
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) {
      const text = await res.text();
      return json({ error: "upstream", status: res.status, detail: text.slice(0, 200) }, 502);
    }
    rows = (await res.json()) as RawLender[];
  } catch (err) {
    return json({ error: "fetch_failed", detail: (err as Error).message }, 502);
  }

  const compactRows = rows
    .map(compact)
    .filter((r) => r.qs >= 3 || r.en === 1)
    .filter((r) => (guarantee ? r.mg : true))
    .filter((r) => (freeConsult ? r.fc : true))
    .filter((r) => {
      if (bbbAPlus && r.bb !== "A+") return false;
      if (bbbFilter === "a-plus" && r.bb !== "A+") return false;
      if (bbbFilter === "a-or-higher" && r.bb !== "A+" && r.bb !== "A") return false;
      if (
        bbbFilter === "b-or-higher" &&
        ["C", "C+", "C-", "D", "F", "NR"].indexOf(r.bb) !== -1
      ) {
        return false;
      }
      return true;
    });

  compactRows.sort((a, b) => {
    if (a.en !== b.en) return b.en - a.en;
    const aTier = a.qs >= 10 ? 2 : a.qs >= 5 ? 1 : 0;
    const bTier = b.qs >= 10 ? 2 : b.qs >= 5 ? 1 : 0;
    if (aTier !== bTier) return bTier - aTier;
    return (b.r || 0) - (a.r || 0);
  });

  const trimmed = compactRows.slice(0, limit);
  return json(
    { count: trimmed.length, total_matched: compactRows.length, results: trimmed },
    200,
    { "cache-control": "public, max-age=60, s-maxage=300" },
  );
}
