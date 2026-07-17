import os

os.environ.setdefault("DB_URL", "sqlite+aiosqlite:///test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("REFRESH_KEY", "test-refresh-key")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE", "60")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("MAIL_USERNAME", "test@example.com")
os.environ.setdefault("MAIL_PASSWORD", "test-password")
os.environ.setdefault("MAIL_FROM", "test@example.com")
os.environ.setdefault("MAIL_PORT", "1025")
os.environ.setdefault("MAIL_SERVER", "localhost")
os.environ.setdefault("MAIL_FROM_NAME", "Test Sender")
os.environ.setdefault("DOMAIN", "http://test")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ELASTICSEARCH_URL", "http://localhost:9200")
os.environ.setdefault("SESSION_SECRET", "test-session-secret")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000"]')
os.environ.setdefault("GOOGLE_CLIENT_ID", "")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
os.environ.setdefault("GOOGLE_SCOPE", "openid email profile")
os.environ.setdefault("GOOGLE_ACCESS_TYPE", "offline")
os.environ.setdefault("GOOGLE_PROMPT", "consent")
os.environ.setdefault("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/v2/auth")
os.environ.setdefault("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")
os.environ.setdefault("GOOGLE_USERINFO_URI", "https://openidconnect.googleapis.com/v1/userinfo")
os.environ.setdefault("beat_dburi", "postgresql://postgres:postgres@localhost:5432/app_db")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.database.db import Base, get_db
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import db_model  # noqa: F401  (registers all models on Base.metadata)
from app.core.rate_limiters import limiter, login_limiter


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
# StaticPool: keep a single underlying connection alive for the engine's
# whole lifetime instead of opening a fresh one per checkout. Two problems
# otherwise: (1) pooled/NullPool connections bind to whatever asyncio event
# loop was running when they were created, and pytest-asyncio gives each
# test its own loop, so a connection from a prior test's loop surviving into
# a new one raised "attached to a different loop"/"no such table" errors;
# (2) an in-memory sqlite database is connection-local, so anything other
# than a single shared connection makes every new connection see an empty
# database. check_same_thread=False is required because aiosqlite hands the
# connection to a background thread.
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # Keep rate limiters from affecting test traffic and reset test isolation.
    original_requests = limiter.requests
    original_login_requests = login_limiter.requests
    limiter.requests = 10_000
    login_limiter.requests = 10_000
    await limiter.reset()
    await login_limiter.reset()

    # Defense in depth: some tests reach for `app.dependency_overrides.clear()`
    # (e.g. to strip a `get_current_user` mock) which also wipes this override
    # since it's otherwise only ever set once, at import time below. Re-assert
    # it before every test so a careless `.clear()` elsewhere can't silently
    # send later tests in the run to the real, non-test database.
    app.dependency_overrides[get_db] = override_get_db

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    limiter.requests = original_requests
    login_limiter.requests = original_login_requests
    await limiter.reset()
    await login_limiter.reset()


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db


async def verify_user(username: str) -> None:
    """Mark a user verified directly in the DB.

    Registration never auto-verifies (email verification is a real feature —
    see app/services/auth/register.py), so any test that registers a user and
    then logs in must call this first or `/auth/login` correctly 403s with
    "User Not Verified".
    """
    from sqlalchemy import select
    from app.models.db_model import User

    async with TestingSessionLocal() as session:
        user = await session.scalar(select(User).where(User.username == username))
        if user:
            user.is_verified = True
            await session.commit()


async def make_superuser(username: str) -> None:
    """Promote a user to superuser directly in the DB.

    Simulates what app/cli/seed.py does — no API path can do this,
    `is_superuser` is intentionally absent from every request schema.
    Needed for tests exercising endpoints that re-check authorization at the
    service layer (defense in depth), which a route-dependency override can't
    bypass on its own — see UserManagementService.assign_role.
    """
    from sqlalchemy import select
    from app.models.db_model import User

    async with TestingSessionLocal() as session:
        user = await session.scalar(select(User).where(User.username == username))
        if user:
            user.is_superuser = True
            await session.commit()

@pytest_asyncio.fixture(scope="function")
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
