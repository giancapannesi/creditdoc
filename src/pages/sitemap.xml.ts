export const prerender = false;

export function GET({ url }: { url: URL }) {
  return new Response(null, {
    status: 301,
    headers: {
      Location: new URL('/sitemap-index.xml', url.origin).toString(),
    },
  });
}
