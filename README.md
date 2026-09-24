# 10_saas_architecture

> Tenant-isolation foundation for multi-tenant SaaS: plan entitlements, per-request tenant context, and a working FastAPI demo entrypoint.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)](https://fastapi.tiangolo.com/)

## What exists (real, tested)

- `src/tenants/isolation.py` — the core, and the only library module:
  - `Tenant` dataclass with `TenantPlan` tiers (free/starter/professional/enterprise), per-plan limits (`PlanLimits`), `has_feature()`, `can_add_user()`
  - tenant-scoped context via `ContextVar`: `tenant_context()` context manager, `set_current_tenant()` / `get_current_tenant()` / `require_tenant()`
  - `TenantMiddleware` (ASGI): resolves the tenant from the `X-Tenant-ID` header (falls back to subdomain) and scopes the whole request
  - `TenantAwareQuery` mixin: `for_tenant()` filter helper for SQLAlchemy-style queries (illustrative — no DB wired)
- `src/main.py` — working FastAPI entrypoint: `/health`, `POST /tenants`, `GET /tenants/{id}`, `GET /tenants/{id}/limits`, `GET /me`, `POST /me/feature/{feature}`, `GET /me/quota/users`. In-memory tenant store.
- `tests/test_isolation.py` + `tests/test_api.py` — 15 tests, all passing.
- `Dockerfile`, `docker-compose.yml`, `.env.example` exist from the template but reference billing/DB pieces that are not implemented.

## What is stubbed / not implemented (honest list)

Everything below was claimed by earlier README versions but **does not exist** in this repo:

- ❌ Stripe billing integration, subscriptions, webhooks — no code, only guidance notes in git history
- ❌ Usage metering / quota enforcement pipeline — only static plan-limit values exist
- ❌ Tenant onboarding workflows (`src/tenants/onboarding.py` was listed but never written)
- ❌ SQLAlchemy persistence — no models, no migrations; the API store is in-memory
- ❌ Feature-flags service — only static per-plan feature lists
- ❌ Audit logs, structured logging setup

Use this as a starting point for tenant-scoped request handling and plan entitlements, not as a production SaaS backend.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

Boot the API:

```bash
PYTHONPATH=src uvicorn main:app --host 127.0.0.1 --port 8000
```

Try it:

```bash
curl -X POST localhost:8000/tenants -H 'Content-Type: application/json' \
  -d '{"name":"Acme","slug":"acme","plan":"starter"}'
# -> {"id": "...", "slug": "acme", "plan": "starter", ...}

TID=<id from above>
curl localhost:8000/me -H "X-Tenant-ID: $TID"
curl -X POST localhost:8000/me/feature/sso -H "X-Tenant-ID: $TID"   # {"allowed": false} on starter
curl "localhost:8000/me/quota/users?current_count=3" -H "X-Tenant-ID: $TID"
```

Run the tests:

```bash
PYTHONPATH=src pytest tests/ -q
# 15 passed
```

## Production gaps (before real use)

1. Real tenant store + auth (never trust a client-supplied tenant ID alone — verify membership).
2. Choose and document a formal isolation strategy (shared tables + RLS, schema-per-tenant, etc.) with cross-tenant access tests.
3. Billing/metering only if/when those modules are actually built.
4. Migrations, backups, audit logging, rate limiting.

## License

VisionQuantech Custom Commercial License — see `LICENSE`.
