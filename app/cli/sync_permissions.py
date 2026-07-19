"""
Mirrors `app.core.rbac.registry.PERMISSION_REGISTRY` into the `permissions`
table (idempotent — safe to run on every startup, see the `lifespan` in
`app/main.py`).

The registry is the source of truth for a permission's *bit position*; this
script only ever creates a missing row or verifies an existing one still
agrees with the registry. It never edits a bit_position in place — a
mismatch means someone violated the registry's append-only rule (see the
docstring in `registry.py`), and that's a bug to fix in code, not paper over
by silently renumbering a bit a role's mask may already depend on.
"""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.rbac.registry import PERMISSION_REGISTRY
from app.database.postgres_db import engine
from app.repositories.rbac.permission import PermissionRepository


async def sync(session=None) -> None:
    if session is not None:
        await _sync_with_session(session)
        return

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as new_session:
        await _sync_with_session(new_session)


async def _sync_with_session(session) -> None:
    repo = PermissionRepository(session)
    created = 0
    for name, bit in PERMISSION_REGISTRY.items():
        existing = await repo.get_by_name(name)
        if existing is not None:
            if existing.bit_position != bit:
                raise RuntimeError(
                    f"Permission registry mismatch for '{name}': "
                    f"db bit_position={existing.bit_position}, "
                    f"code bit_position={bit}. Never edit an existing "
                    "PERMISSION_REGISTRY value — see registry.py."
                )
            continue
        await repo.create_with_bit(name, bit)
        created += 1
    print(f"Permission registry sync: {created} created, {len(PERMISSION_REGISTRY) - created} already present.")


if __name__ == "__main__":
    asyncio.run(sync())
