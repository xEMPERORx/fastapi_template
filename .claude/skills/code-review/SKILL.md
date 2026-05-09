---
name: code-review
description: >
  Review FastAPI template code for correctness, security, and adherence to project
  conventions. Use when user asks to "review this code", "check my code", "is this right?",
  or before committing changes to the codebase.
---

Review code against this checklist. Flag violations with file:line and suggest the fix.

## Architecture Review

- [ ] Route → Service → Repository → DB. No skipped layers.
- [ ] No business logic in routes (only param extraction + service call + return)
- [ ] No DB access in services (only through repository)
- [ ] No `db.commit()` outside repository layer

## Security Review

- [ ] Input validated via Pydantic schemas (not raw dicts)
- [ ] Sensitive fields use validators from `app/core/validation`
- [ ] Auth routes use `Depends(get_current_user)` or `role_required`/`permission_required`
- [ ] No secrets logged (passwords, tokens, keys)
- [ ] No raw SQL string concatenation — always use SQLAlchemy parameterized queries
- [ ] File paths use `safe_filename()` from `app/core/data_validation`
- [ ] Response schemas exclude password hashes and internal fields

## Error Handling Review

- [ ] Services raise custom exceptions (`AppException` subclasses), never return None or error dicts
- [ ] New exceptions registered in `app/error/register_error.py`
- [ ] Repository does NOT catch exceptions (let them bubble to service)
- [ ] Route does NOT have try/except — let global handler catch everything

## Data Flow Review

- [ ] Request schema (Pydantic) → Service → Repository → DB Model
- [ ] DB Model → Service → Response schema (Pydantic with `from_attributes=True`)
- [ ] No SQLAlchemy models returned directly from route
- [ ] No Pydantic schemas passed into repository (convert to dict or model first)

## Logging Review

- [ ] Routes decorated with `@log_function`
- [ ] New services extend `LoggedService`
- [ ] New repositories extend `LoggedRepository`

## Dependency Injection Review

- [ ] New dependencies wired in `app/core/dependency_factory.py`
- [ ] Routes use `Annotated[Type, Depends(factory)]` pattern
- [ ] No circular imports — factories isolate wiring

## Testing Review

- [ ] Tests use `ac: AsyncClient` fixture for HTTP tests
- [ ] Tests marked `@pytest.mark.asyncio`
- [ ] Covers: success case, missing fields, invalid input, auth/protected, not-found
- [ ] No real external services called (use test DB + mocked external calls)

## Common Mistakes to Flag

1. **Service returning raw model**: Must convert to Pydantic response schema
2. **Route importing DB session**: Should use service dependency instead
3. **Repository raising HTTPException**: Should raise AppException, let handler map to HTTP
4. **Password in logs**: `_redact_value` in logger handles this, but verify sensitive field names contain "password"/"token"/"secret"/"key"
5. **Missing `await` on async calls**: All DB calls must be awaited
6. **Sync SQLAlchemy imports**: Must use `sqlalchemy.ext.asyncio.AsyncSession`, never sync Session
7. **No `from_attributes=True` on response schemas**: Without this, `model_validate(orm_obj)` fails
8. **Business logic in route**: Extract to service method