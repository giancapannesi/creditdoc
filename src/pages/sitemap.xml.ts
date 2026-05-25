export const prerender = false;

export function GET({ url }: { url: URL }) {
  return Response.redirect(new URL('/sitemap-index.xml', url.origin), 301);
}
