// Adaptive DB client.
//   1. better-sqlite3 against a local file when CREDITDOC_LOCAL_DB env is set (BUILD time)
//   2. better-sqlite3 against the bundled `data/creditdoc-slim.db` shipped with the
//      Vercel function (RUNTIME — fast, in-process queries)
//   3. libsql/Turso fallback when neither file is available (incremental updates,
//      currently unused at runtime — see ARCHITECTURE.md)
//
// All content tables in creditdoc.db store the full record as a `data JSON` column,
// so reads are SELECT data FROM <table> + JSON.parse, no column mapping needed.

import { createRequire } from 'node:module';
import * as nodePath from 'node:path';
import * as fs from 'node:fs';

type AnyDB = {
  execute(args: { sql: string; args: (string | number)[] }): Promise<{ rows: Array<Record<string, unknown>> }>;
};

let _client: AnyDB | null = null;

function makeLocal(path: string): AnyDB {
  // createRequire works in ESM. better-sqlite3 is a CJS native module, and
  // dynamic ESM import re-introduces loader friction, so we use require directly.
  const require = createRequire(import.meta.url);
  const Database = require('better-sqlite3');
  const db = new Database(path, { readonly: true, fileMustExist: true });
  return {
    async execute({ sql, args }) {
      const stmt = db.prepare(sql);
      const rows = stmt.all(...(args ?? []));
      return { rows: rows as Array<Record<string, unknown>> };
    },
  };
}

function makeTurso(): AnyDB {
  // Lazy require so the runtime function bundle does not need @libsql/client when
  // it has the bundled DB file. Kept for compatibility with seed/incremental flows.
  const require = createRequire(import.meta.url);
  const { createClient } = require('@libsql/client') as typeof import('@libsql/client');
  const url = import.meta.env.TURSO_DATABASE_URL ?? process.env.TURSO_DATABASE_URL;
  const authToken = import.meta.env.TURSO_AUTH_TOKEN ?? process.env.TURSO_AUTH_TOKEN;
  if (!url) throw new Error('TURSO_DATABASE_URL not set');
  if (!authToken) throw new Error('TURSO_AUTH_TOKEN not set');
  const c = createClient({ url, authToken });
  return {
    async execute({ sql, args }) {
      const r = await c.execute({ sql, args });
      return { rows: r.rows.map(row => Object.fromEntries(Object.entries(row))) };
    },
  };
}

// Resolve a bundled DB path that works both at build (cwd = project root)
// and at runtime on Vercel (function bundles `data/creditdoc-slim.db`
// alongside the entry point — discoverable via process.cwd() or relative
// to the entry).
function resolveBundledDb(): string | null {
  const candidates = [
    process.env.CREDITDOC_LOCAL_DB,
    nodePath.join(process.cwd(), 'data', 'creditdoc-slim.db'),
    // Vercel serverless: function root is /var/task. includeFiles preserves
    // the relative path under the function root.
    '/var/task/data/creditdoc-slim.db',
  ];
  for (const p of candidates) {
    if (p && fs.existsSync(p)) return p;
  }
  return null;
}

function client(): AnyDB {
  if (_client) return _client;
  const dbPath = resolveBundledDb();
  if (dbPath) {
    _client = makeLocal(dbPath);
  } else {
    _client = makeTurso();
  }
  return _client;
}

export async function queryJsonRows<T>(
  sql: string,
  args: (string | number)[] = []
): Promise<T[]> {
  const res = await client().execute({ sql, args });
  return res.rows.map(r => JSON.parse(String(r.data)) as T);
}

export async function queryJsonRow<T>(
  sql: string,
  args: (string | number)[] = []
): Promise<T | null> {
  const res = await client().execute({ sql, args });
  if (res.rows.length === 0) return null;
  return JSON.parse(String(res.rows[0].data)) as T;
}

export async function queryRows(
  sql: string,
  args: (string | number)[] = []
): Promise<Record<string, unknown>[]> {
  const res = await client().execute({ sql, args });
  return res.rows;
}
