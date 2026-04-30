# Scoped Token Register — CreditDoc

**CDM-REV-2026-04-29 Phase 3.4.** Doc-only — single source of truth for every credential CreditDoc relies on. Lists scope, where stored, rotation cadence, last-rotated date, and rotation procedure.

**Compliance posture:** OBJ-3 Tier 1 (marketing site). When the business activates payment / KYB / lending product surfaces, this register is the migration entry-point — every additional credential must be added here on the same day it's provisioned.

**Owner:** Jammi (gian.eao@gmail.com).
**Reviewed:** quarterly. Next review due **2026-07-30**.

---

## Storage discipline

| Rule | Why |
|------|-----|
| All secrets live outside the git repo. | Avoid accidental commit / public exposure. |
| All env files are `chmod 600` (owner read+write only). | OS-level protection from other VPS users. |
| `.env` files are listed in `.gitignore`. | Pre-commit safety net. |
| Service-role keys NEVER ship to Cloudflare Pages. | Public preview URL, no privileged access. |
| Anon-only keys reach the edge. | RLS enforces authorization at the row level. |

---

## Token inventory

Each row: **what** it is, **scope** (what it can do), **storage** (where the secret value lives), **rotation cadence**, **last rotated**, **rotation procedure**.

### Cloudflare

| Token | Scope | Storage | Rotation | Last rotated | Rotation procedure |
|-------|-------|---------|----------|--------------|--------------------|
| `CF_API_TOKEN` | account-scoped Pages + Workers + R2 + DNS | `tools/.creditdoc-migration.env` (chmod 600) | 90 days | 2026-04-28 | CF dashboard → My Profile → API Tokens → Roll. Update env file in same shell. |
| `CF_ACCOUNT_EMAIL` + `CF_ACCOUNT_PASSWORD` | Cloudflare account login | `tools/.creditdoc-migration.env` | on-demand only | n/a | Password manager (Jammi). Rotate immediately on suspected compromise. |
| `CF_ACCOUNT_ID` | account identifier (not a secret, but PII-adjacent) | same | n/a | n/a | Doesn't rotate. |

### Supabase

| Token | Scope | Storage | Rotation | Last rotated | Rotation procedure |
|-------|-------|---------|----------|--------------|--------------------|
| `SUPABASE_ANON_KEY` | RLS-gated public reads/writes | `creditdoc/.env`, `tools/.supabase-creditdoc.env`, CF Pages secret `SUPABASE_ANON_KEY` | 90 days | 2026-04-28 | Supabase dashboard → Project Settings → API Keys → Reset anon key. Update CF Pages secret + both env files in same window. RLS keeps blast radius bounded. |
| `SUPABASE_SERVICE_ROLE_KEY` | bypasses RLS — full DB access | `tools/.supabase-creditdoc.env`, `tools/.creditdoc-migration.env` (chmod 600, never on CF Pages) | **rotate post-CDM-REV cutover** | 2026-04-28 | Supabase dashboard → API Keys → Reset service-role. Update env files. **Don't ship to edge.** |
| `SUPABASE_DB_PASSWORD` | direct Postgres connection (psql, pg_dump) | `tools/.supabase-creditdoc.env`, `tools/.creditdoc-migration.env` | on-demand only | 2026-04-28 | Supabase dashboard → Database → Reset password. Update env files. |
| `SUPABASE_DB_URL` | full connection string (host:port + user + db_password) | same | derived from password rotation | 2026-04-28 | Reconstruct after each `SUPABASE_DB_PASSWORD` rotation. |
| `SUPABASE_PUBLISHABLE_KEY` | public anon-equivalent (newer Supabase dual-key model) | `tools/.supabase-creditdoc.env` | 90 days | 2026-04-28 | Same as anon key. |

### R2 (object storage)

| Token | Scope | Storage | Rotation | Last rotated | Rotation procedure |
|-------|-------|---------|----------|--------------|--------------------|
| `R2_ACCESS_KEY_ID` + `R2_SECRET_ACCESS_KEY` | bucket-scoped read/write on `creditdoc-assets` | `tools/.r2-creditdoc.env` (chmod 600) | 90 days | 2026-04-28 | CF dashboard → R2 → Manage R2 API Tokens → Create new, delete old. Update env file. |
| `R2_ENDPOINT` | account-specific S3-compatible endpoint URL | same | n/a | n/a | Doesn't rotate. |

### Application

| Token | Scope | Storage | Rotation | Last rotated | Rotation procedure |
|-------|-------|---------|----------|--------------|--------------------|
| `REVALIDATE_TOKEN` | bearer for `POST /api/revalidate` (Phase 2.3 wiring) | `tools/.creditdoc-revalidate.env` (chmod 600), CF Pages secret | 90 days | 2026-04-29 | `openssl rand -hex 32` → update env + `wrangler pages secret put REVALIDATE_TOKEN`. Old token rejected on next revalidate POST. |

### Google Cloud

| Token | Scope | Storage | Rotation | Last rotated | Rotation procedure |
|-------|-------|---------|----------|--------------|--------------------|
| GSC service account JSON | GSC read-only (CreditDoc property) | `tools/.gsc-credentials.json` (chmod 600) | 1 year | 2026-03 | GCP console → IAM → Service accounts → Keys → Add key. Replace JSON file. Old key disabled. |
| GA4 service account JSON | GA4 read-only (5 properties) | `tools/.gcal-service-account.json` (shared) | 1 year | 2026-03 | Same as GSC. |
| `GOOGLE_PLACES_API_KEY` | Places API requests (cost-restricted, IP-restricted) | `creditdoc/.env` | on-demand only | n/a | GCP console → APIs → Credentials → Regenerate. Re-restrict by IP + API. Last spend incident: 2026-04-21 ($65). |

### Social platforms

| Token | Scope | Storage | Rotation | Last rotated |
|-------|-------|---------|----------|--------------|
| `LINKEDIN_ACCESS_TOKEN` (+ refresh) | post on behalf of CreditDoc org | `creditdoc/.env` | LinkedIn enforces 60-day expiry on access tokens | 2026-04 (refresh path) |
| `PINTEREST_ACCESS_TOKEN` | post Pins to CreditDoc account | `creditdoc/.env` | 1 year | 2026-04 |

### Compliance attestations (no secret value, but tracked here)

| Field | Value | Where |
|-------|-------|-------|
| `DPA_CLOUDFLARE_SIGNED_AT` | DPA signing date | `tools/.creditdoc-migration.env` |
| `DPA_SUPABASE_SIGNED_AT` | DPA signing date | `tools/.creditdoc-migration.env` |

DPA PDFs themselves: pending download to `creditdoc/docs/compliance/dpa/` (Phase 3.3).

---

## What's NOT in this register

- **CF Global API Key** — deprecated path; we use scoped `CF_API_TOKEN` instead. If a Global API Key is ever issued for emergency use, it must be added here on the day of issuance.
- **Vercel access tokens** — Vercel is the legacy host, scheduled for retirement at Phase 6 cutover. Tokens get revoked at cutover, not rotated.
- **GitHub PAT** — pushes use SSH; no PAT in active use.
- **Personal credentials** (Jammi's password manager). Out of scope.

---

## Rotation runbook (90-day cadence)

1. `date` → confirm we're past the 90-day mark on a token.
2. Open this doc → identify the rotation procedure for that token.
3. Generate the new token in the source system (CF / Supabase / R2 / etc.).
4. Update the env file in the same shell (`chmod 600` preserved).
5. If the token reaches Cloudflare Pages: `wrangler pages secret put <NAME>` in the same shell.
6. Smoke test the affected surface (curl, write, fetch).
7. Update the **Last rotated** date in this doc. Commit.
8. Disable / delete the old token in the source system.
9. Memory Palace drawer (`creditdoc / decisions`) with verbatim rotation log.

## On suspected compromise

1. Rotate the affected token immediately (steps 3-8 above).
2. Audit `audit_log` rows in Supabase since the credential's last legitimate use — look for unexpected `actor`, `ip`, or row_pk patterns.
3. Pull CF dashboard → Audit Log for the last 7 days on that token.
4. File a Memory Palace drawer (`creditdoc / post-mortems`).
5. Tell Jammi.

---

## Maintenance

This file is updated **synchronously** with any credential change. PR / commit blocked otherwise. Pre-commit hook check: any change to `creditdoc/.env`, `tools/.*.env` should pair with an edit to this file.

Reviewed by Jammi quarterly. Next review: **2026-07-30**.
