# 10_saas_architecture

> Multi-tenant SaaS backend foundation for tenant isolation, subscriptions, billing, feature entitlements, and usage-based limits.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SaaS](https://img.shields.io/badge/Architecture-Multi--Tenant%20SaaS-6C47FF)](https://en.wikipedia.org/wiki/Multitenancy)
[![Stripe](https://img.shields.io/badge/Billing-Stripe-635BFF?logo=stripe&logoColor=white)](https://stripe.com/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-D71F00)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-Custom%20Commercial-orange)](./LICENSE)

This repository is a Python SaaS architecture foundation for products that serve multiple customers from a shared platform. It demonstrates tenant lifecycle management, data isolation, subscription plans, Stripe billing, feature entitlements, and usage-based limits.

The project is intended as a modular starting point for B2B SaaS products, internal platforms, subscription services, and usage-metered applications.

## What this project includes

- tenant models and lifecycle management
- tenant onboarding workflows
- data isolation patterns
- subscription plans and entitlements
- Stripe billing integration points
- usage metering and quota enforcement
- feature flags and plan-based access
- SQLAlchemy persistence patterns
- structured application logging
- Pydantic-based configuration

## Repository structure

```text
10_saas_architecture/
├── src/
│   ├── tenants/
│   │   ├── models.py
│   │   ├── isolation.py
│   │   └── onboarding.py
│   ├── billing/
│   │   ├── plans.py
│   │   ├── metering.py
│   │   └── stripe.py
│   ├── features/
│   │   └── flags.py
│   ├── limits/
│   └── main.py
├── tests/
├── pyproject.toml
├── README.md
├── LICENSE
├── .env.example
└── .gitignore
```

## SaaS architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                         Application Users                         │
│             members │ administrators │ service accounts           │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Tenant Context                              │
│       tenant identity │ membership │ roles │ isolation             │
└──────────────────────────────────────────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
┌────────────────────┐ ┌──────────────────┐ ┌────────────────────┐
│ Feature Entitlements│ │ Billing          │ │ Usage and Limits   │
│ plan flags          │ │ subscriptions   │ │ quotas and meters  │
└────────────────────┘ └──────────────────┘ └────────────────────┘
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                 Tenant-Scoped Application Data                    │
└──────────────────────────────────────────────────────────────────┘
```

## Core concepts

### Multi-tenancy

Every tenant-scoped operation must establish and validate tenant context before reading or writing data. Isolation can be implemented through:

- shared tables with a mandatory tenant identifier
- database row-level security
- schema-per-tenant designs
- database-per-tenant designs for stronger isolation

Choose an approach based on compliance, scale, operational complexity, and customer requirements. Never rely only on a client-provided tenant ID without verifying membership and authorization.

### Subscriptions and entitlements

Plans should define explicit entitlements such as:

- enabled features
- user or seat limits
- storage limits
- API request quotas
- usage-based pricing rules
- support or service tiers

Keep entitlement checks centralized so application behavior remains consistent across APIs, jobs, and background workers.

### Usage metering

Usage events should be recorded with enough information to support:

- idempotent aggregation
- billing-period boundaries
- corrections and adjustments
- customer-visible usage reporting
- reconciliation with the billing provider

Avoid charging twice for retried events. Use stable event identifiers and durable processing state.

## Quick start

### Prerequisites

- Python 3.10+
- pip and virtual environment support
- database supported by the configured SQLAlchemy setup
- Stripe test account for billing flows

### Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### Configure environment

```bash
cp .env.example .env
```

Example local configuration:

```env
APP_ENVIRONMENT=development
DATABASE_URL=sqlite:///./saas.db
STRIPE_SECRET_KEY=sk_test_replace_me
STRIPE_WEBHOOK_SECRET=whsec_replace_me
DEFAULT_CURRENCY=usd
USAGE_EVENT_RETENTION_DAYS=90
```

Never commit Stripe keys, webhook secrets, customer payment data, or production database credentials.

### Run the example

```bash
python -m src.main
```

## Stripe integration guidance

Production billing integrations should:

- verify webhook signatures before processing events
- make webhook handlers idempotent
- persist provider event IDs
- handle retries and events arriving out of order
- reconcile subscriptions periodically
- support failed payments and grace periods
- avoid storing raw card data
- keep local subscription state consistent with Stripe

Test subscription creation, upgrades, downgrades, cancellations, refunds, failed payments, and webhook replay behavior.

## Production-readiness assessment

### Current maturity: strong SaaS architecture foundation

This repository provides useful building blocks for a multi-tenant product, but tenant isolation and billing logic require thorough integration, security, and failure-mode testing before production use.

### Strengths

- clear separation of tenant, billing, feature, and limit concerns
- suitable foundation for B2B SaaS products
- supports subscription and usage-based business models
- includes SQLAlchemy and Stripe extension points
- easy to adapt to different tenant-isolation strategies

### Production gaps to address

1. Select and document a formal tenant-isolation strategy.
2. Add automated cross-tenant access tests.
3. Add database constraints and indexes for tenant-scoped data.
4. Add billing webhook idempotency and reconciliation jobs.
5. Add usage event deduplication and correction workflows.
6. Add subscription state transition and failed-payment handling.
7. Add audit logs for tenant administrators and billing actions.
8. Add backups, migrations, retention, and disaster-recovery procedures.

## Security and privacy

Before deployment:

- validate tenant membership on every protected operation
- prevent insecure direct object references across tenants
- use least-privilege database credentials
- encrypt sensitive data in transit and at rest
- protect billing and webhook endpoints
- avoid logging payment secrets or personal data
- define tenant offboarding and data-deletion workflows
- document data retention and export policies

## SaaS metrics

Track metrics such as:

- active tenants and users
- trial conversion and churn
- monthly recurring revenue
- plan distribution and expansion revenue
- feature adoption
- usage against quota
- failed payments and recovery rate
- webhook processing failures
- tenant onboarding completion time

## Monetization opportunities

| Business model | Best use case |
| --- | --- |
| B2B SaaS platform | recurring subscription product |
| usage-based API service | metered processing or automation |
| white-label SaaS foundation | customized customer deployments |
| billing and entitlement toolkit | reusable product infrastructure |
| SaaS architecture consulting | tenant and billing modernization |

## GitHub discoverability

This repository is positioned around:

- Python multi-tenant SaaS architecture
- Stripe subscription billing
- usage-based billing backend
- tenant data isolation
- feature flags and entitlements
- SQLAlchemy SaaS platform
- B2B SaaS backend foundation

To improve discoverability:

- add tenant-isolation diagrams and examples
- document subscription state transitions
- include webhook and metering test scenarios
- publish database schema and migration guidance
- explain trade-offs between shared and isolated databases

## Roadmap ideas

- add PostgreSQL row-level security examples
- add organization membership and invitations
- add self-service billing portal integration
- add plan upgrades, downgrades, and proration
- add usage dashboards and quota alerts
- add tenant-aware background job processing
- add data export and deletion workflows
- add automated billing reconciliation

## Contributing

Contributions are welcome for:

- tenant isolation improvements
- billing and webhook reliability
- usage metering and quota enforcement
- feature entitlement modeling
- migration and database support
- SaaS security tests and documentation

Please do not submit real payment credentials, customer data, or production secrets.

## License

This repository contains a custom commercial license in `LICENSE`.

Review the complete license before personal earning, commercial, enterprise, redistribution, or client deployment use.
