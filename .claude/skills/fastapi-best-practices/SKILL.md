---
name: fastapi-best-practices
description: >
  Enforce FastAPI best practices and project conventions. Auto-triggers when writing
  FastAPI code, routes, services, repositories, middleware, or modifying any file under app/.
  Use when user asks to "follow best practices", "make it production-ready", or writes
  any FastAPI endpoint/service/repository.
---

Always follow this project's layered architecture and conventions. Never bypass layers.

## Architecture

```
middleware -> route -> service -> repository -> db/external service -> response
```

Every request flows through these layers. Never skip a layer. Never put business logic in routes. Never put DB queries in services.

## Dependency Injection

All services and repositories wired through `app/core/dependency_factory.py`. Follow this pattern:

```python
# Repository factory
def get_thing_repository(db: AsyncSession = Depends(get_db)) -> ThingRepository:
    return ThingRepository(db)

# Service factory
def get_thing_service(
    thing_repo: ThingRepository = Depends(get_thing_repository),
) -> ThingService:
    return ThingService(thing_repo)
```

Routes use `Annotated[ServiceType, Depends(get_service_factory)]`.

## When Adding Code

### New Feature (full stack)
1. Pydantic schemas in `app/schema/` (request + response models)
2. SQLAlchemy model in `app/models/` (export from `db_model.py`)
3. Repository in `app/repositories/` (extend `LoggedRepository`)
4. Service in `app/services/` (extend `LoggedService`)
5. Route in `app/api/v1/routes/`
6. Wire dependencies in `app/core/dependency_factory.py`
7. Register router in `app/main.py`
8. Run `alembic revision --autogenerate -m "description"`

### New Route Only
1. Schema in `app/schema/`
2. Route function in `app/api/v1/routes/`
3. Dependencies in `app/core/dependency_factory.py`
4. Router in `app/main.py`

## Database Rules

- Always use async SQLAlchemy: `AsyncSession`, `select()`, `await db.commit()`
- Commit + refresh after mutations in repository, never in service or route
- Use `selectin` loading for relationships: `select(Model).options(selectin(Model.related))`
- Never commit from services or routes — only repositories touch the session

## Error Handling

- Raise exceptions from `app/error/custom_exception.py`, never return error dicts
- Custom exceptions extend `AppException` and take `(message, error_code)`
- Register new exception handlers in `app/error/register_error.py`
- Use `create_exception_handler(status_code, initial_detail)` factory
- Service layer validates and raises, route layer never handles errors

## Logging

- Routes: use `@log_function` decorator
- Services: extend `LoggedService` for auto-logging of all public methods
- Repositories: extend `LoggedRepository` for auto-logging
- Sensitive fields (password, token, secret, key) auto-redacted

## Authentication / Authorization

- `get_current_user` dep for authenticated endpoints
- `role_required(["admin"])` for role-based access
- `permission_required("write:users")` for fine-grained control
- Access tokens in Authorization header, refresh tokens in httpOnly cookie

## Input Validation

- Use Pydantic models for all request bodies
- Use `Annotated[str, AfterValidator(...)]` from `app/core.validation` for field-level checks
- Available validators: `validate_email`, `validate_strong_password`, `validate_no_sql_injection`, `sanitize_text`
- Available types: `SafeStr`, `SafeEmail`, `StrongPassword`

## Error Recovery

- Use `async_retry(func, config=RetryConfig(max_retries=3))` for transient external calls
- Use `CircuitBreaker` for external services that may fail repeatedly
- Import from `app.core.recovery`

## Security

- All responses get security headers automatically (registered via middleware)
- Health check at `/api/v1/health` for monitoring
- Rate limiting enabled by default (10 req/60s per IP)
- Never log secrets — logger auto-redacts password/token/key fields

## What NOT To Do

- Don't put business logic in route functions
- Don't call `db.commit()` outside repositories
- Don't return raw SQLAlchemy models from routes — use response schemas
- Don't catch exceptions in routes — let the global handler deal with them
- Don't create circular imports — dependency_factory isolates all wiring
- Don't skip layers to save time — the pattern exists for a reason