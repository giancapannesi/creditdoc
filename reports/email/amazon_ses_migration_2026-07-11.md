# CreditDoc Amazon SES Migration - 2026-07-11

## Completed

- Added the three Amazon SES DKIM CNAME records for the `www.creditdoc.co` SES identity in Cloudflare.
- All three records are DNS-only (`proxied=false`).
- Public resolver checks passed via `1.1.1.1`, `8.8.8.8`, and `9.9.9.9`.
- Updated root SPF for `creditdoc.co` to include Amazon SES while preserving existing SimpleLogin and VPS allowances:
  - `v=spf1 include:simplelogin.co include:amazonses.com ip4:187.77.2.146 ip6:2a02:4780:4:a118::1 ~all`
- Added SPF for the `www.creditdoc.co` SES identity:
  - `v=spf1 include:amazonses.com ~all`

## SES DKIM Records

| Name | Target | Status |
|---|---|---|
| `chf6lh6etffrt5pu43vg6oqjfwu6vj5s._domainkey.www.creditdoc.co` | `chf6lh6etffrt5pu43vg6oqjfwu6vj5s.dkim.amazonses.com` | Resolves |
| `nohyvjvjif3mw6la2h5buqwqmwnsgsiz._domainkey.www.creditdoc.co` | `nohyvjvjif3mw6la2h5buqwqmwnsgsiz.dkim.amazonses.com` | Resolves |
| `q7jw7rhl3hlknvanw4m22tjfpmlma2ri._domainkey.www.creditdoc.co` | `q7jw7rhl3hlknvanw4m22tjfpmlma2ri.dkim.amazonses.com` | Resolves |

## Current Sender State

- CreditDoc site signup API still posts to Sendy through `/api/email-signup`.
- Sendy cron is active:
  - `*/5 * * * * php7.4 /srv/sendy/scheduled.php`
- Sendy brand configuration for CreditDoc currently uses:
  - From: `CreditDoc <noreply@creditdoc.co>`
  - Reply-To: `gian.eao@gmail.com`
  - SMTP host: `localhost`
  - SMTP port: `25`
- Sendy main AWS key/secret fields are currently empty.
- Postfix is not relaying through SES:
  - `relayhost =`
- Postfix queue shows repeated direct-port-25 delivery timeouts to SimpleLogin MX for local root mail. This confirms the current local mail path is not a healthy SES relay.

## Important Alignment Note

The SES DKIM records supplied are for `www.creditdoc.co`, but the active Sendy From domain is `creditdoc.co`.

Current DMARC is strict:

```text
v=DMARC1; p=quarantine; pct=100; adkim=s; aspf=s
```

With strict DMARC, a DKIM signature for `www.creditdoc.co` will not align with a visible From address at `noreply@creditdoc.co`. For best deliverability, either:

1. Verify `creditdoc.co` itself in SES and use `noreply@creditdoc.co`; or
2. Send from an address under `www.creditdoc.co` and keep the supplied SES identity.

Option 1 is cleaner for brand trust.

## Remaining Blocker

To complete the actual send migration, CreditDoc needs SES SMTP credentials or AWS IAM credentials for the selected SES region. Without those, changing Sendy away from `localhost:25` would break course/autoresponder delivery.

Recommended next step:

- In AWS SES, verify the root identity `creditdoc.co` if the intended sender remains `noreply@creditdoc.co`.
- Create SES SMTP credentials for the same SES region.
- Configure Sendy CreditDoc brand SMTP:
  - Host: `email-smtp.<region>.amazonaws.com`
  - Port: `587`
  - TLS: `tls`
  - Username/password: SES SMTP credentials
- Send one test signup through `/api/email-signup` and verify:
  - subscriber is added;
  - autoresponder sends;
  - message headers show SES DKIM pass;
  - DMARC pass.
