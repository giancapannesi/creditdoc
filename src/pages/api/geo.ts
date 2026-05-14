export const prerender = false;

export async function GET({ request }: { request: Request }) {
  const cf = (request as any).cf || {};
  return new Response(JSON.stringify({
    city: cf.city || '',
    region: cf.region || '',
    regionCode: cf.regionCode || '',
    country: cf.country || '',
  }), {
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}
