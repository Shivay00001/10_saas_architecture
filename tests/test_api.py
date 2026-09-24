"""API tests for the FastAPI entrypoint (main.py), incl. middleware isolation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient

import main


def _client():
    main.TENANTS.clear()
    return TestClient(main.app)


def test_health():
    c = _client()
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["tenant"] in (None, "")


def test_create_and_fetch_tenant():
    c = _client()
    r = c.post("/tenants", json={"name": "Acme", "slug": "acme", "plan": "starter"})
    assert r.status_code == 201
    tid = r.json()["id"]
    r = c.get(f"/tenants/{tid}")
    assert r.status_code == 200
    assert r.json()["slug"] == "acme"
    assert r.json()["plan"] == "starter"


def test_duplicate_slug_rejected():
    c = _client()
    c.post("/tenants", json={"name": "A", "slug": "dup", "plan": "free"})
    r = c.post("/tenants", json={"name": "B", "slug": "dup", "plan": "free"})
    assert r.status_code == 409


def test_unknown_tenant_404():
    c = _client()
    assert c.get("/tenants/nope").status_code == 404
    assert c.get("/tenants/nope/limits").status_code == 404


def test_limits_endpoint():
    c = _client()
    tid = c.post("/tenants", json={"name": "A", "slug": "a", "plan": "professional"}).json()["id"]
    r = c.get(f"/tenants/{tid}/limits")
    assert r.status_code == 200
    body = r.json()
    assert body["plan"] == "professional"
    assert body["limits"]["max_users"] == 50


def test_middleware_resolves_tenant_header():
    c = _client()
    tid = c.post("/tenants", json={"name": "A", "slug": "a", "plan": "starter"}).json()["id"]
    r = c.get("/me", headers={"X-Tenant-ID": tid})
    assert r.status_code == 200
    assert r.json() == {"tenant_id": tid, "registered": True}


def test_tenant_isolation_between_requests():
    c = _client()
    tid = c.post("/tenants", json={"name": "A", "slug": "a", "plan": "starter"}).json()["id"]
    r = c.get("/me", headers={"X-Tenant-ID": tid})
    assert r.json()["tenant_id"] == tid
    r = c.get("/me", headers={"X-Tenant-ID": "other"})
    assert r.json() == {"tenant_id": "other", "registered": False}
    r = c.get("/me")  # no header
    assert r.json()["registered"] is False


def test_feature_check_endpoint():
    c = _client()
    tid = c.post("/tenants", json={"name": "A", "slug": "a", "plan": "free"}).json()["id"]
    h = {"X-Tenant-ID": tid}
    assert c.post("/me/feature/basic_reports", headers=h).json()["allowed"] is True
    assert c.post("/me/feature/sso", headers=h).json()["allowed"] is False
    assert c.post("/me/feature/basic_reports").status_code == 401  # no tenant


def test_user_quota_endpoint():
    c = _client()
    tid = c.post("/tenants", json={"name": "A", "slug": "a", "plan": "free"}).json()["id"]
    h = {"X-Tenant-ID": tid}
    r = c.get("/me/quota/users?current_count=2", headers=h)
    assert r.json()["can_add_user"] is True
    r = c.get("/me/quota/users?current_count=3", headers=h)
    assert r.json()["can_add_user"] is False
