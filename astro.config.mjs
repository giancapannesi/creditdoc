// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';

// CDM-REV-2026-04-29 Phase 1.2 — Cloudflare adapter for hybrid SSR.
// In Astro 5, `output: 'static'` is the new hybrid: pages prerender by default,
// individual pages opt INTO server-rendering with `export const prerender = false;`.
// Marketing pages stay prerendered; high-churn routes (/review/[slug] etc.) opt-in
// to SSR. Adapter must be present for any SSR route to build.
export default defineConfig({
  site: 'https://www.creditdoc.co',
  output: 'static',
  adapter: cloudflare({
    // 'passthrough' avoids bundling sharp/detect-libc into the worker (which
    // breaks workerd at runtime — bare require('fs')/'child_process'). Static
    // images in dist/_astro/ are still optimized at build time. SSR pages do
    // not currently use Astro's <Image> runtime — if that changes, switch to
    // 'cloudflare' (Workers Image Resizing) rather than 'compile'.
    imageService: 'passthrough',
  }),
  build: {
    format: 'directory',
  },
  vite: {
    plugins: [tailwindcss()],
  },
  integrations: [
    sitemap({
      // Split into multiple sitemaps (~5000 URLs each) for crawl efficiency
      entryLimit: 5000,
      // Set priority + changefreq per page type
      serialize(item) {
        const url = item.url;
        if (url.includes('/best/')) {
          item.priority = 0.9;
          item.changefreq = 'weekly';
        } else if (url.includes('/answers/')) {
          item.priority = 0.85;
          item.changefreq = 'weekly';
        } else if (url.includes('/financial-wellness/')) {
          item.priority = 0.8;
          item.changefreq = 'monthly';
        } else if (url.includes('/blog/')) {
          item.priority = 0.7;
          item.changefreq = 'monthly';
        } else if (url.includes('/review/')) {
          item.priority = 0.6;
          item.changefreq = 'monthly';
        } else if (url.includes('/compare/')) {
          item.priority = 0.5;
          item.changefreq = 'monthly';
        } else if (url.includes('/city/') || url.includes('/state/')) {
          item.priority = 0.5;
          item.changefreq = 'monthly';
        } else if (url.includes('/categories/')) {
          item.priority = 0.7;
          item.changefreq = 'weekly';
        } else if (url.includes('/brand/')) {
          item.priority = 0.75;
          item.changefreq = 'weekly';
        }
        return item;
      },
    }),
  ],
});
