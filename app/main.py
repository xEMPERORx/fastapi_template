from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.routes import health, tenant, users
from app.api.v1.routes.auth import account, google_oauth
from app.api.v1.routes.rbac import permission, roles
from app.cli import sync_permissions
from app.core.authz_cache import authz_cache
from app.core.logger import logger
from app.error.register import register_exception
from app.middleware.logger_middleware import register_logger_middleware
from app.middleware.ratelimiting_middleware import register_ratelimit_middleware
from app.middleware.security_middleware import register_security_middleware
from app.settings import Config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent: mirrors the code-defined permission catalog into the DB
    # (see app/core/rbac/registry.py) so every Permission row has the
    # bit_position a mask needs, before anything else can query it.
    await sync_permissions.sync()
    await authz_cache.start()
    yield
    await authz_cache.stop()


app = FastAPI(
    title="FastAPI Starter Template",
    lifespan=lifespan,
)


register_logger_middleware(app)
register_ratelimit_middleware(app)
register_security_middleware(app)

app.add_middleware(
    SessionMiddleware,
    secret_key=Config.SESSION_SECRET,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception(app)

app.include_router(account.router, prefix="/api/v1/auth")
app.include_router(google_oauth.router, prefix="/api/v1/auth")
app.include_router(roles.router, prefix="/api/v1/role")
app.include_router(permission.router, prefix="/api/v1/permission")
app.include_router(users.router, prefix="/api/v1/users")
app.include_router(tenant.router, prefix="/api/v1/tenants")
app.include_router(health.router, prefix="/api/v1")

# Serve the built admin SPA (frontend/) from the same process — no separate
# frontend server. API routes above always win; this only ever handles a
# request FastAPI didn't already have a route for. Skipped entirely if
# `npm run build` hasn't been run yet, so pure-backend dev never breaks.
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.frontend("/", directory=FRONTEND_DIST)
else:
    logger.info(
        "frontend/dist not found, skipping SPA mount "
        "(run `npm run build` in frontend/ to serve the admin UI from this process)"
    )
