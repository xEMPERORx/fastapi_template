from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.routes import auth, google_oauth, health, permission, roles, search
from app.core.esclient import INDEX_CONFIG, close_es_client, es_client
from app.core.logger import logger
from app.error.register_error import register_exception
from app.middleware.logger_middleware import register_logger_middleware
from app.middleware.ratelimiting_middleware import register_ratelimit_middleware
from app.middleware.security_middleware import register_security_middleware
from app.settings import Config


@asynccontextmanager
async def lifespan(app: FastAPI):
    index_name = "search_index"
    try:
        if await es_client.ping():
            logger.info("Connected to Elasticsearch successfully")

            exists = await es_client.indices.exists(index=index_name)
            if not exists:
                await es_client.indices.create(index=index_name, body=INDEX_CONFIG)
                logger.info("Index '%s' created with custom mapping", index_name)
        else:
            logger.warning("Elasticsearch ping failed")
    except Exception as e:
        logger.exception("Error during ES initialization: %s", e)

    yield

    await close_es_client()
    logger.info("Elasticsearch connection closed")


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

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(google_oauth.router, prefix="/api/v1/auth")
app.include_router(roles.router, prefix="/api/v1/role")
app.include_router(permission.router, prefix="/api/v1/permission")
app.include_router(search.router, prefix="/api/v1/search")
app.include_router(health.router, prefix="/api/v1")
