import blogPosts from '../content/blog-posts.json';

const SITE = 'https://www.creditdoc.co';

type BlogPost = {
  slug: string;
  title?: string;
  description?: string;
  seo_description?: string;
  publish_date?: string;
  last_updated?: string;
  status?: string;
  category_label?: string;
};

function escapeXml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function pubDate(value: string | undefined): string {
  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) return new Date().toUTCString();
  return date.toUTCString();
}

export function GET() {
  const posts = (blogPosts as BlogPost[])
    .filter((post) => post.status === 'published' && post.slug)
    .sort((a, b) => {
      const aDate = new Date(a.last_updated || a.publish_date || 0).getTime();
      const bDate = new Date(b.last_updated || b.publish_date || 0).getTime();
      return bDate - aDate;
    })
    .slice(0, 50);

  const latest = posts[0]?.last_updated || posts[0]?.publish_date;
  const items = posts.map((post) => {
    const url = `${SITE}/blog/${post.slug}/`;
    const description = post.seo_description || post.description || '';
    return `    <item>
      <title>${escapeXml(post.title || post.slug)}</title>
      <link>${escapeXml(url)}</link>
      <guid isPermaLink="true">${escapeXml(url)}</guid>
      <description>${escapeXml(description)}</description>
      <pubDate>${escapeXml(pubDate(post.publish_date || post.last_updated))}</pubDate>
      ${post.category_label ? `<category>${escapeXml(post.category_label)}</category>` : ''}
    </item>`;
  }).join('\n');

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>CreditDoc Blog</title>
    <link>${SITE}/blog/</link>
    <description>CreditDoc articles on credit, lending, debt, and consumer finance.</description>
    <language>en-us</language>
    <lastBuildDate>${escapeXml(pubDate(latest))}</lastBuildDate>
    <atom:link href="${SITE}/rss.xml" rel="self" type="application/rss+xml" />
${items}
  </channel>
</rss>
`;

  return new Response(body, {
    headers: {
      'content-type': 'application/rss+xml; charset=utf-8',
      'cache-control': 'public, max-age=3600',
    },
  });
}
