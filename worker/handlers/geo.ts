/**
 * /api/geo — return CF geo headers as JSON.
 * Ported verbatim from src/pages/api/geo.ts (13 LoC).
 */
export function handleGeo(request: Request): Response {
  const cf = ((request as unknown as { cf?: Record<string, string> }).cf) || {};
  return new Response(
    JSON.stringify({
      city: cf.city || "",
      region: cf.region || "",
      regionCode: cf.regionCode || "",
      country: cf.country || "",
    }),
    {
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    },
  );
}
