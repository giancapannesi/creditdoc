# CreditDoc LinkedIn Cron

The LinkedIn workflow publishes one CreditDoc resource post twice per week.

The live schedule is Tuesday and Friday. Each run creates/refreshed the weekly
resource drafts, auto-approves only due CreditDoc resource posts, and publishes at most one post.

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

- Scheduled posting rotates CreditDoc tools, the free course, and selected answer pages.
- Each scheduled run publishes at most one due resource post.
- The publisher refuses more than two posts per UTC ISO week.
- Live publishing requires `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_ORGANIZATION_URN`.
- Each post links to one CreditDoc URL and uses detailed explanatory copy.

## Commands

```bash
node scripts/creditdoc_linkedin_manager.mjs auth-check
node scripts/creditdoc_linkedin_manager.mjs auth-url
node scripts/creditdoc_linkedin_manager.mjs exchange-code '<code-from-callback-url>'
node scripts/creditdoc_linkedin_manager.mjs list-organizations
node scripts/creditdoc_linkedin_manager.mjs set-organization 'urn:li:organization:123456'
node scripts/creditdoc_linkedin_manager.mjs draft-week
node scripts/creditdoc_linkedin_manager.mjs run-scheduled-resources --dry-run
node scripts/creditdoc_linkedin_manager.mjs run-scheduled-resources
node scripts/creditdoc_linkedin_manager.mjs run-scheduled-tools --dry-run
node scripts/creditdoc_linkedin_manager.mjs run-scheduled-tools
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

The authorization helper requests only the organization posting scopes needed for CreditDoc company-page publishing:

- `w_organization_social`
- `r_organization_social`

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

Live twice-weekly resource posting:

```cron
5 14 * * 2,5 cd /srv/BusinessOps/creditdoc && /usr/bin/node scripts/creditdoc_linkedin_manager.mjs run-scheduled-resources >> /srv/BusinessOps/logs/creditdoc_linkedin_resource_posts.log 2>&1
```

Optional manual dry run:

```bash
node scripts/creditdoc_linkedin_manager.mjs run-scheduled-resources --dry-run
```
