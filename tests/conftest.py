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
from app.database.db import get_db
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database.db import get_db
from app.models.db_model import Base
from app.middleware.ratelimiting_middleware import limiter


TEST_DATABASE_URL = "sqlite+aiosqlite:///test.db"
engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # Keep rate limiter from affecting test traffic and reset test isolation.
    original_requests = limiter.requests
    limiter.requests = 10_000
    limiter.counters.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    limiter.requests = original_requests
    limiter.counters.clear()


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function")
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
