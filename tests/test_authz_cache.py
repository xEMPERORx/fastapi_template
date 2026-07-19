"""Unit tests for the in-process authz cache itself (app.core.authz_cache) —
fail-open behavior and event application, without needing a real Redis.
End-to-end staleness-detection-through-the-API is covered separately in
tests/test_role_creation_hierarchy.py (a role assignment invalidates an
already-issued token) and tests/test_hierarchy_rbac.py.
"""

import uuid

import pytest

from app.core.authz_cache.cache import AuthzCache


def test_empty_cache_fails_open():
    """Nothing known yet (cold start, or Redis never reachable) must never
    block a request — a user/tenant absent from the cache is trusted."""
    cache = AuthzCache(redis_client_factory=lambda: None)
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    assert cache.is_user_inactive(user_id) is False
    assert cache.is_tenant_inactive(tenant_id) is False
    assert cache.is_tenant_inactive(None) is False
    assert cache.is_stale(user_id, token_perm_version=1) is False


def test_apply_perm_version_event_updates_state():
    cache = AuthzCache(redis_client_factory=lambda: None)
    user_id = uuid.uuid4()

    cache._apply_event({"type": "perm_version", "user_id": str(user_id), "version": 3})

    assert cache.is_stale(user_id, token_perm_version=2) is True
    assert cache.is_stale(user_id, token_perm_version=3) is False
    assert cache.is_stale(user_id, token_perm_version=4) is False


def test_apply_user_status_event_updates_inactive_set():
    cache = AuthzCache(redis_client_factory=lambda: None)
    user_id = uuid.uuid4()

    cache._apply_event({"type": "user_status", "user_id": str(user_id), "is_active": False})
    assert cache.is_user_inactive(user_id) is True

    cache._apply_event({"type": "user_status", "user_id": str(user_id), "is_active": True})
    assert cache.is_user_inactive(user_id) is False


def test_apply_tenant_status_event_updates_inactive_set():
    cache = AuthzCache(redis_client_factory=lambda: None)
    tenant_id = uuid.uuid4()

    cache._apply_event({"type": "tenant_status", "tenant_id": str(tenant_id), "is_active": False})
    assert cache.is_tenant_inactive(tenant_id) is True

    cache._apply_event({"type": "tenant_status", "tenant_id": str(tenant_id), "is_active": True})
    assert cache.is_tenant_inactive(tenant_id) is False


@pytest.mark.asyncio
async def test_resync_fails_open_on_redis_error():
    """A Redis-unreachable resync must log and keep whatever state the
    cache already had — never raise, never wipe existing state."""
    user_id = uuid.uuid4()

    def broken_factory():
        raise ConnectionError("redis unreachable")

    cache = AuthzCache(redis_client_factory=broken_factory)
    cache._apply_event({"type": "perm_version", "user_id": str(user_id), "version": 5})

    await cache._resync_once()

    # State from before the failed resync must survive untouched.
    assert cache.is_stale(user_id, token_perm_version=4) is True


@pytest.mark.asyncio
async def test_resync_replaces_state_from_redis():
    """A successful resync fully replaces in-memory state from Redis's
    durable mirror — the anti-entropy path, used to recover from a missed
    Pub/Sub message."""
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    tenant_a = uuid.uuid4()

    class FakeRedis:
        async def hgetall(self, key):
            return {str(user_a): "7"}

        async def smembers(self, key):
            if "tenant" in key:
                return {str(tenant_a)}
            return {str(user_b)}

    cache = AuthzCache(redis_client_factory=lambda: FakeRedis())
    await cache._resync_once()

    assert cache.is_stale(user_a, token_perm_version=6) is True
    assert cache.is_user_inactive(user_b) is True
    assert cache.is_tenant_inactive(tenant_a) is True
