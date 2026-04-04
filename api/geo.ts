export const config = { runtime: 'edge' };

export default function handler(request: Request) {
  // Vercel provides geo object on edge function requests
  // @ts-expect-error Vercel extends Request with geo property
  const geo = request.geo || {};

  return new Response(
    JSON.stringify({
      country: geo.country || '',
      region: geo.region || '',
    }),
    {
      headers: {
        'content-type': 'application/json',
        'cache-control': 'private, no-store',
      },
    }
  );
}
