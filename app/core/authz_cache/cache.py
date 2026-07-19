"""In-process authorization cache: one instance per worker, kept current via
Redis Pub/Sub with a periodic anti-entropy resync as a fallback.

Why this exists instead of querying Redis (or Postgres) on every request:
Pub/Sub pushes changes to a small in-memory structure at write-time (rare —
an admin changing a permission/deactivating a user, not a per-request event),
so the read path (`is_user_inactive`/`is_tenant_inactive`/`is_stale`, called
from `get_current_user`/`get_current_principal` on every authenticated
request) is a plain in-memory set/dict lookup: no network hop at all, faster
than even a single Redis round trip.

Fails open throughout, mirroring `app.core.ratelimit.sliding_window`'s
convention: if Redis/Pub-Sub is unreachable, a worker keeps serving from
whatever it last had (or "nothing known revoked" on a cold start with no
cache yet) rather than blocking every request. An outage degrades freshness,
not availability — the same tradeoff already made for rate limiting.
"""

import asyncio
import json
import uuid

from app.core.authz_cache.channel import (
    AUTHZ_EVENTS_CHANNEL,
    INACTIVE_TENANTS_KEY,
    INACTIVE_USERS_KEY,
    PERM_VERSIONS_KEY,
    RESYNC_INTERVAL_SECONDS,
)
from app.core.logger import logger
from app.database.redis_db import redis_connect, redis_connect_blocking


class AuthzCache:
    def __init__(self, redis_client_factory=redis_connect, pubsub_client_factory=redis_connect_blocking):
        self._redis_client_factory = redis_client_factory
        self._pubsub_client_factory = pubsub_client_factory
        self.inactive_user_ids: set[uuid.UUID] = set()
        self.inactive_tenant_ids: set[uuid.UUID] = set()
        self.perm_version: dict[uuid.UUID, int] = {}
        self._tasks: list[asyncio.Task] = []
        self._stop_event: asyncio.Event | None = None

    async def start(self) -> None:
        self._stop_event = asyncio.Event()
        self._tasks = [
            asyncio.create_task(self._subscribe_loop()),
            asyncio.create_task(self._resync_loop()),
        ]

    async def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self._tasks = []

    def is_user_inactive(self, user_id: uuid.UUID) -> bool:
        return user_id in self.inactive_user_ids

    def is_tenant_inactive(self, tenant_id: uuid.UUID | None) -> bool:
        return tenant_id is not None and tenant_id in self.inactive_tenant_ids

    def is_stale(self, user_id: uuid.UUID, token_perm_version: int) -> bool:
        """True if the token's `perm_version` claim is behind what this
        cache currently knows for the user. Fails open: a user this cache
        has never heard of (nothing cached yet, or Redis has been
        unreachable since startup) is treated as not stale, consistent with
        "nothing known revoked" being the safe default under an outage."""
        current = self.perm_version.get(user_id)
        if current is None:
            return False
        return token_perm_version < current

    async def _subscribe_loop(self) -> None:
        assert self._stop_event is not None
        while not self._stop_event.is_set():
            try:
                client = self._pubsub_client_factory()
                pubsub = client.pubsub()
                await pubsub.subscribe(AUTHZ_EVENTS_CHANNEL)
                try:
                    async for message in pubsub.listen():
                        if self._stop_event.is_set():
                            break
                        if message.get("type") == "message":
                            self._apply_event(json.loads(message["data"]))
                finally:
                    await pubsub.unsubscribe(AUTHZ_EVENTS_CHANNEL)
                    await pubsub.aclose()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Authz cache Pub/Sub unreachable, keeping last-known state: %s", exc)
                await asyncio.sleep(RESYNC_INTERVAL_SECONDS)

    async def _resync_loop(self) -> None:
        assert self._stop_event is not None
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=RESYNC_INTERVAL_SECONDS)
                break  # stop_event was set
            except asyncio.TimeoutError:
                pass
            await self._resync_once()

    async def _resync_once(self) -> None:
        try:
            client = self._redis_client_factory()
            versions = await client.hgetall(PERM_VERSIONS_KEY)
            inactive_users = await client.smembers(INACTIVE_USERS_KEY)
            inactive_tenants = await client.smembers(INACTIVE_TENANTS_KEY)
            self.perm_version = {uuid.UUID(k): int(v) for k, v in versions.items()}
            self.inactive_user_ids = {uuid.UUID(u) for u in inactive_users}
            self.inactive_tenant_ids = {uuid.UUID(t) for t in inactive_tenants}
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Authz cache anti-entropy resync failed, keeping last-known state: %s", exc)

    def _apply_event(self, event: dict) -> None:
        event_type = event.get("type")
        if event_type == "perm_version":
            self.perm_version[uuid.UUID(event["user_id"])] = event["version"]
        elif event_type == "user_status":
            user_id = uuid.UUID(event["user_id"])
            if event["is_active"]:
                self.inactive_user_ids.discard(user_id)
            else:
                self.inactive_user_ids.add(user_id)
        elif event_type == "tenant_status":
            tenant_id = uuid.UUID(event["tenant_id"])
            if event["is_active"]:
                self.inactive_tenant_ids.discard(tenant_id)
            else:
                self.inactive_tenant_ids.add(tenant_id)


authz_cache = AuthzCache()
