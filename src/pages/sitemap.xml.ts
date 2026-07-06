export const prerender = false;

const SITEMAP_FILES = [
  'sitemap-0.xml',
  'sitemap-1.xml',
  'sitemap-2.xml',
  'sitemap-3.xml',
  'sitemap-4.xml',
  'sitemap-5.xml',
];

export function GET({ url }: { url: URL }) {
  const origin = url.origin;
  const body = `<?xml version="1.0" encoding="UTF-8"?>` +
    `<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">` +
    SITEMAP_FILES.map((file) => `<sitemap><loc>${origin}/${file}</loc></sitemap>`).join('') +
    `</sitemapindex>`;

  return new Response(body, {
    status: 200,
    headers: {
      'content-type': 'application/xml; charset=utf-8',
      'cache-control': 'public, max-age=0, must-revalidate',
    },
  });
}
