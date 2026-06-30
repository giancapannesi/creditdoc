# CreditDoc LinkedIn Cron

The LinkedIn workflow is intentionally approval-gated.

## Secrets

Secrets are stored outside the repo:

- `/srv/BusinessOps/tools/.linkedin.env`

Expected keys:

- `LINKEDIN_CLIENT_ID`
- `LINKEDIN_CLIENT_SECRET` or `LINKEDIN_API_KEY`
- `LINKEDIN_ACCESS_TOKEN` once OAuth is completed
- `LINKEDIN_ORGANIZATION_URN` once the CreditDoc company page/admin organization is confirmed

## Queue And Logs

- Draft queue: `/srv/BusinessOps/data/creditdoc_linkedin_queue.json`
- Publish state: `/srv/BusinessOps/data/creditdoc_linkedin_state.json`
- Publish log: `/srv/BusinessOps/logs/creditdoc_linkedin_posts.jsonl`

## Safety Rules

- Auto-generation creates drafts only.
- A draft must be manually marked `approved` before publishing.
- The publisher refuses more than two posts per UTC ISO week.
- Live publishing requires `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_ORGANIZATION_URN`.

## Commands

```bash
node scripts/creditdoc_linkedin_manager.mjs auth-check
node scripts/creditdoc_linkedin_manager.mjs auth-url
node scripts/creditdoc_linkedin_manager.mjs exchange-code '<code-from-callback-url>'
node scripts/creditdoc_linkedin_manager.mjs list-organizations
node scripts/creditdoc_linkedin_manager.mjs set-organization 'urn:li:organization:123456'
node scripts/creditdoc_linkedin_manager.mjs draft-week
node scripts/creditdoc_linkedin_manager.mjs status
node scripts/creditdoc_linkedin_manager.mjs approve <draft-id>
node scripts/creditdoc_linkedin_manager.mjs publish-approved --dry-run
node scripts/creditdoc_linkedin_manager.mjs publish-approved
```

## OAuth Setup

The helper uses this redirect URI:

```text
https://www.creditdoc.co/linkedin-oauth-callback/
```

Add that exact URI in the LinkedIn Developer app under OAuth redirect URLs.
Then run:

```bash
node scripts/creditdoc_linkedin_manager.mjs auth-url
```

Open the generated URL, approve the scopes, copy the `code` value from the callback page, and exchange it:

```bash
node scripts/creditdoc_linkedin_manager.mjs exchange-code '<code>'
```

After the access token is saved, find the company page organization URN:

```bash
node scripts/creditdoc_linkedin_manager.mjs list-organizations
```

Then save the correct CreditDoc organization:

```bash
node scripts/creditdoc_linkedin_manager.mjs set-organization 'urn:li:organization:123456'
```

## Recommended Cron

Drafts only, weekly:

```cron
35 10 * * 1 cd /srv/BusinessOps/creditdoc && /usr/bin/node scripts/creditdoc_linkedin_manager.mjs draft-week >> /srv/BusinessOps/logs/creditdoc_linkedin_drafts.log 2>&1
```

Approved-publish check, twice weekly:

```cron
45 10 * * 2,5 cd /srv/BusinessOps/creditdoc && /usr/bin/node scripts/creditdoc_linkedin_manager.mjs publish-approved >> /srv/BusinessOps/logs/creditdoc_linkedin_publish.log 2>&1
```
