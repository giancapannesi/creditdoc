// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';
import vercel from '@astrojs/vercel';

export default defineConfig({
  site: 'https://www.creditdoc.co',
  output: 'static',
  adapter: vercel({
    isr: {
      expiration: 60 * 60 * 24, // 24h default; per-route can override via headers
    },
    // Bundle the slim SQLite + better-sqlite3 native module into the serverless
    // function so SSR routes can read in-process (no network round-trips).
    // node-file-trace can't follow createRequire(), so we add them explicitly.
    includeFiles: [
      './data/creditdoc-slim.db',
      './node_modules/better-sqlite3/build/Release/better_sqlite3.node',
      './node_modules/better-sqlite3/lib/index.js',
      './node_modules/better-sqlite3/lib/database.js',
      './node_modules/better-sqlite3/lib/sqlite-error.js',
      './node_modules/better-sqlite3/lib/util.js',
      './node_modules/better-sqlite3/lib/methods/aggregate.js',
      './node_modules/better-sqlite3/lib/methods/backup.js',
      './node_modules/better-sqlite3/lib/methods/function.js',
      './node_modules/better-sqlite3/lib/methods/inspect.js',
      './node_modules/better-sqlite3/lib/methods/pragma.js',
      './node_modules/better-sqlite3/lib/methods/serialize.js',
      './node_modules/better-sqlite3/lib/methods/table.js',
      './node_modules/better-sqlite3/lib/methods/transaction.js',
      './node_modules/better-sqlite3/lib/methods/wrappers.js',
      './node_modules/better-sqlite3/package.json',
      './node_modules/bindings/bindings.js',
      './node_modules/bindings/package.json',
      './node_modules/file-uri-to-path/index.js',
      './node_modules/file-uri-to-path/package.json',
    ],
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
