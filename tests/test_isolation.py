"""Real tests for the tenant-isolation foundation (isolation.py)."""
import pytest

from tenants.isolation import (
    PLAN_LIMITS,
    Tenant,
    TenantPlan,
    get_current_tenant,
    require_tenant,
    set_current_tenant,
    tenant_context,
)


def setup_function(_):
    set_current_tenant(None)


def test_plan_limits_table():
    assert PLAN_LIMITS[TenantPlan.FREE].max_users == 3
    assert PLAN_LIMITS[TenantPlan.ENTERPRISE].max_users == -1  # unlimited
    assert "sso" in PLAN_LIMITS[TenantPlan.ENTERPRISE].features
    assert "sso" not in PLAN_LIMITS[TenantPlan.STARTER].features


def test_tenant_feature_check():
    t = Tenant(name="A", slug="a", plan=TenantPlan.STARTER)
    assert t.has_feature("api_access")
    assert not t.has_feature("sso")


def test_tenant_user_quota():
    t = Tenant(name="A", slug="a", plan=TenantPlan.FREE)
    assert t.can_add_user(2)
    assert not t.can_add_user(3)
    ent = Tenant(name="E", slug="e", plan=TenantPlan.ENTERPRISE)
    assert ent.can_add_user(10**9)


def test_tenant_context_sets_and_restores():
    assert get_current_tenant() is None
    with tenant_context("t-1"):
        assert get_current_tenant() == "t-1"
        with tenant_context("t-2"):
            assert get_current_tenant() == "t-2"
        assert get_current_tenant() == "t-1"
    assert get_current_tenant() is None


def test_require_tenant_raises_without_context():
    with pytest.raises(ValueError):
        require_tenant()
    with tenant_context("t-9"):
        assert require_tenant() == "t-9"
