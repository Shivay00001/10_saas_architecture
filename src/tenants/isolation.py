"""
Multi-Tenant Isolation - Data isolation patterns for SaaS.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar
from uuid import uuid4


# Current tenant context
current_tenant_var: ContextVar[Optional[str]] = ContextVar("current_tenant", default=None)


class TenantPlan(str, Enum):
    """Subscription plan tiers."""
    
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class PlanLimits:
    """Limits for a subscription plan."""
    
    max_users: int
    max_storage_gb: int
    max_api_calls_per_day: int
    features: List[str] = field(default_factory=list)


PLAN_LIMITS: Dict[TenantPlan, PlanLimits] = {
    TenantPlan.FREE: PlanLimits(
        max_users=3,
        max_storage_gb=1,
        max_api_calls_per_day=1000,
        features=["basic_reports"],
    ),
    TenantPlan.STARTER: PlanLimits(
        max_users=10,
        max_storage_gb=10,
        max_api_calls_per_day=10000,
        features=["basic_reports", "api_access", "email_support"],
    ),
    TenantPlan.PROFESSIONAL: PlanLimits(
        max_users=50,
        max_storage_gb=100,
        max_api_calls_per_day=100000,
        features=["basic_reports", "api_access", "email_support", "advanced_analytics", "integrations"],
    ),
    TenantPlan.ENTERPRISE: PlanLimits(
        max_users=-1,  # Unlimited
        max_storage_gb=-1,
        max_api_calls_per_day=-1,
        features=["basic_reports", "api_access", "email_support", "advanced_analytics", "integrations", "sso", "audit_logs", "sla"],
    ),
}


@dataclass
class Tenant:
    """Tenant entity."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    slug: str = ""
    plan: TenantPlan = TenantPlan.FREE
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def limits(self) -> PlanLimits:
        """Get plan limits."""
        return PLAN_LIMITS[self.plan]
    
    def has_feature(self, feature: str) -> bool:
        """Check if tenant has access to a feature."""
        return feature in self.limits.features
    
    def can_add_user(self, current_count: int) -> bool:
        """Check if tenant can add more users."""
        max_users = self.limits.max_users
        return max_users == -1 or current_count < max_users


def get_current_tenant() -> Optional[str]:
    """Get current tenant ID from context."""
    return current_tenant_var.get()


def set_current_tenant(tenant_id: Optional[str]) -> None:
    """Set current tenant ID in context."""
    current_tenant_var.set(tenant_id)


@contextmanager
def tenant_context(tenant_id: str):
    """
    Context manager for tenant scope.
    
    Usage:
        with tenant_context("tenant-123"):
            # All operations here are scoped to this tenant
            users = get_users()
    """
    previous = get_current_tenant()
    set_current_tenant(tenant_id)
    try:
        yield tenant_id
    finally:
        set_current_tenant(previous)


def require_tenant() -> str:
    """
    Get current tenant or raise error.
    
    Raises:
        ValueError: If no tenant is set
    """
    tenant_id = get_current_tenant()
    if not tenant_id:
        raise ValueError("No tenant context set")
    return tenant_id


class TenantAwareQuery:
    """
    Mixin for tenant-aware database queries.
    
    Automatically filters queries by current tenant.
    """
    
    @classmethod
    def get_tenant_filter(cls):
        """Get SQLAlchemy filter for current tenant."""
        tenant_id = require_tenant()
        return cls.organization_id == tenant_id
    
    @classmethod
    def for_tenant(cls, query):
        """Apply tenant filter to query."""
        return query.filter(cls.get_tenant_filter())


class TenantMiddleware:
    """ASGI middleware for tenant resolution."""
    
    def __init__(self, app, header_name: str = "X-Tenant-ID"):
        self.app = app
        self.header_name = header_name.lower().encode()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract tenant from header or subdomain
        headers = dict(scope.get("headers", []))
        tenant_id = headers.get(self.header_name, b"").decode()
        
        if not tenant_id:
            # Try subdomain
            host = headers.get(b"host", b"").decode()
            if host and "." in host:
                tenant_id = host.split(".")[0]
        
        with tenant_context(tenant_id):
            await self.app(scope, receive, send)
