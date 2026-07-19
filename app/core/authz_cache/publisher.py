"""Publishes authz-affecting mutations (permission/role changes, user/tenant
deactivation) so every worker's in-process `AuthzCache` can stay current
without either polling Postgres or having each request hit Redis directly.

Two things happen per event, in one pipeline (one round trip regardless of
how many events a single mutation produces — e.g. a role permission change
fans out to every user holding that role):
- A durable write (`HSET`/`SADD`/`SREM`) to a small Redis-side mirror, so a
  worker's periodic anti-entropy resync (`AuthzCache._resync_loop`) has
  something authoritative to read even if it missed the Pub/Sub message.
- A `PUBLISH` for near-instant propagation in the common case where every
  worker's Pub/Sub connection is healthy.

Fails open (logs and returns) if Redis is unreachable — same convention as
`app.core.ratelimit.sliding_window`: an infra outage degrades authz-cache
freshness (workers keep serving from their last-known state, or nothing
known-revoked on a cold start), not availability.
"""

import json

from app.core.authz_cache.channel import (
    AUTHZ_EVENTS_CHANNEL,
    INACTIVE_TENANTS_KEY,
    INACTIVE_USERS_KEY,
    PERM_VERSIONS_KEY,
    RESYNC_INTERVAL_SECONDS,
)
from app.core.logger import logger
from app.database.redis_db import redis_connect


async def publish_events(events: list[dict]) -> None:
    if not events:
        return
    try:
        client = redis_connect()
        pipe = client.pipeline(transaction=False)
        for event in events:
            pipe.publish(AUTHZ_EVENTS_CHANNEL, json.dumps(event))
            event_type = event["type"]
            if event_type == "perm_version":
                pipe.hset(PERM_VERSIONS_KEY, event["user_id"], event["version"])
            elif event_type == "user_status":
                if event["is_active"]:
                    pipe.srem(INACTIVE_USERS_KEY, event["user_id"])
                else:
                    pipe.sadd(INACTIVE_USERS_KEY, event["user_id"])
            elif event_type == "tenant_status":
                if event["is_active"]:
                    pipe.srem(INACTIVE_TENANTS_KEY, event["tenant_id"])
                else:
                    pipe.sadd(INACTIVE_TENANTS_KEY, event["tenant_id"])
        await pipe.execute()
    except Exception as exc:
        logger.warning(
            "Authz cache publish failed, relying on %ss anti-entropy resync: %s",
            RESYNC_INTERVAL_SECONDS, exc,
        )
