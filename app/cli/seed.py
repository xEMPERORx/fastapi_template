"""
Bootstrap script for a fresh deployment.

The hierarchical RBAC model has a chicken-and-egg problem: creating a role
or permission requires a permission, but nothing has any permissions yet.
`is_superuser` is the escape hatch — it bypasses every permission/role/grant
check — and it is deliberately absent from every request schema, so the
only way to set it is here or by hand in the database.

Run once per environment, after migrations:

    alembic upgrade head
    python -m app.cli.seed

Reads SEED_ADMIN_USERNAME / SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD from the
environment if set (useful for non-interactive/CI bootstrap), otherwise
prompts interactively.
"""

import asyncio
import getpass
import os

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database.db import engine
from app.repositories.auth.user import UserRepository
from app.services.auth.password import get_password_hash


async def seed() -> None:
    username = os.getenv("SEED_ADMIN_USERNAME") or input("Superuser username: ")
    email = os.getenv("SEED_ADMIN_EMAIL") or input("Superuser email: ")
    password = os.getenv("SEED_ADMIN_PASSWORD") or getpass.getpass("Superuser password: ")

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        repo = UserRepository(session)

        if await repo.exists_by_username(username):
            print(f"User '{username}' already exists — nothing to do.")
            return

        user = await repo.create(
            username=username,
            email=email,
            password=get_password_hash(password),
            is_verified=True,
            is_superuser=True,
        )
        print(f"Created superuser '{user.username}' ({user.id}).")
        print("Log in with them to create roles/permissions and configure grant delegation for everyone else.")


if __name__ == "__main__":
    asyncio.run(seed())
