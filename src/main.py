"""
Working FastAPI entrypoint for the tenant-isolation foundation.

Run:
    PYTHONPATH=src uvicorn main:app --reload   (from the repo root)

Tenant identity comes from the `X-Tenant-ID` header (or subdomain), resolved
by TenantMiddleware in tenants/isolation.py.

This is a demo/foundation: the tenant store is in-memory, billing/Stripe,
usage metering, onboarding workflows and persistence are intentionally absent
(see README: "What exists vs what is stubbed").
"""

from dataclasses import asdict
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from tenants.isolation import (
    Tenant,
    TenantMiddleware,
    TenantPlan,
    get_current_tenant,
)


class TenantCreate(BaseModel):
    name: str
    slug: str
    plan: TenantPlan = TenantPlan.FREE


def tenant_to_dict(t: Tenant) -> dict:
    d = asdict(t)
    d["plan"] = t.plan.value
    d["created_at"] = t.created_at.isoformat()
    d["limits"] = asdict(t.limits)
    return d


app = FastAPI(
    title="SaaS Tenant Isolation Foundation",
    description="Minimal working entrypoint demonstrating tenant-scoped context.",
    version="1.0.0",
)
app.add_middleware(TenantMiddleware, header_name="X-Tenant-ID")

# In-memory tenant registry (demo only — not persisted).
TENANTS: Dict[str, Tenant] = {}


@app.get("/health")
def health(request: Request):
    return {"status": "ok", "tenant": get_current_tenant()}


@app.post("/tenants", status_code=201)
def create_tenant(body: TenantCreate):
    if any(t.slug == body.slug for t in TENANTS.values()):
        raise HTTPException(status_code=409, detail="slug already exists")
    tenant = Tenant(name=body.name, slug=body.slug, plan=body.plan)
    TENANTS[tenant.id] = tenant
    return tenant_to_dict(tenant)


@app.get("/tenants/{tenant_id}")
def get_tenant(tenant_id: str):
    tenant = TENANTS.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="tenant not found")
    return tenant_to_dict(tenant)


@app.get("/tenants/{tenant_id}/limits")
def tenant_limits(tenant_id: str):
    tenant = TENANTS.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="tenant not found")
    return {"plan": tenant.plan.value, "limits": asdict(tenant.limits)}


@app.get("/me")
def me():
    """Show the tenant resolved by the middleware for this request."""
    tenant_id = get_current_tenant()
    return {"tenant_id": tenant_id, "registered": tenant_id in TENANTS if tenant_id else False}


@app.post("/me/feature/{feature}")
def check_feature(feature: str):
    """Demonstrate a plan-entitlement check inside tenant context."""
    tenant_id = get_current_tenant()
    if not tenant_id or tenant_id not in TENANTS:
        raise HTTPException(status_code=401, detail="unknown or missing tenant (set X-Tenant-ID)")
    tenant = TENANTS[tenant_id]
    return {"tenant_id": tenant_id, "feature": feature, "allowed": tenant.has_feature(feature)}


@app.get("/me/quota/users")
async def check_user_quota(current_count: int = 0):
    """Demonstrate a seat-limit check: /me/quota/users?current_count=3"""
    tenant_id = get_current_tenant()
    if not tenant_id or tenant_id not in TENANTS:
        raise HTTPException(status_code=401, detail="unknown or missing tenant (set X-Tenant-ID)")
    tenant = TENANTS[tenant_id]
    return {
        "tenant_id": tenant_id,
        "current_count": current_count,
        "max_users": tenant.limits.max_users,
        "can_add_user": tenant.can_add_user(current_count),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000)
