# SOUS demo: multi-tenant ordering backend

A small demo of three decisions: tenant isolation by default, integrations that are assumed to fail, and product data computed from orders.

## Run it
    docker compose up -d
    docker compose run --rm web python manage.py migrate
    docker compose run --rm web python manage.py seed
    cd frontend && npm install && npm run dev      # http://localhost:5173

Demo logins (fake data, password `demo1234`): parrilla@example.com, empanaderia@example.com, cafe@example.com

## Tests
    docker compose run --rm web pytest -v
    cd frontend && npm test

## The three decisions
1. **Tenant isolation.** `TenantScopedViewSet` filters on the user's tenant and sets it on create; `tenant` isn't in the serializers. Cross-tenant tests prove list, retrieve (404) and create.
2. **Integrations fail.** Webhooks verify an HMAC over the raw body, store the payload first, dedupe on a unique constraint, and record failures. `reprocess_failed` retries up to 3 times.
3. **Product data.** Repeat-guest rate (2nd order within 30 days of the 1st) is computed from orders, with tests that know the answer.

CI is GitHub Actions (`.github/workflows/ci.yml`): lint, pytest against a real Postgres service, frontend test and build. The target stack uses Bitbucket Pipelines; the stages port one-to-one.

## What's faked
- Webhook payloads are simplified. Header names and the HMAC scheme follow Shopify; the carrier payload is invented.
- All data, secrets and passwords are seed data.

## What I cut, and why
- Line items on orders (`total_cents` is stored directly)
- Queues and Celery (a management command is enough for a demo)
- Refresh tokens (the access token lives in memory)
- Generated API client (types are hand-written)
- Firebase, Cloud Run, i18n

## Next
Postgres RLS as a second isolation layer, an event log, OpenAPI-generated types, a queue with backoff, GCP deploy.