---
name: code-review
description: >
  Perform thorough code reviews of this FastAPI template — correctness, security,
  performance, and maintainability, plus adherence to project conventions. Use when
  user asks to review code, check for bugs, audit a codebase, or before committing
  changes.
---

Review code against the checklists below. Flag violations with `file:line`, state the
concrete failure scenario (not just "this is bad practice"), and suggest the fix.
Project-specific checks come first — they catch the mistakes this codebase actually
makes; the general checklist catches everything else.

## Architecture Review

- [ ] Route → Service → Repository → DB. No skipped layers.
- [ ] No business logic in routes (only param extraction + service call + return)
- [ ] No DB access in services (only through repository)
- [ ] No `db.commit()` outside repository layer
- [ ] New dependencies wired in `app/core/dependency_factory.py`, routes use `Annotated[Type, Depends(factory)]`
- [ ] No circular imports — factories isolate wiring

## Project Security Review

- [ ] Input validated via Pydantic schemas (not raw dicts); free-text fields use `SafeStr`/`SafeEmail`/`StrongPassword` from `app/core/validation`. Structured identifiers matched verbatim later (role/permission names, slugs) use `SafeIdentifier` (allow-list) instead of `SafeStr` — `sanitize_text`'s SQL-keyword stripping silently corrupts verb-scoped names like `"permission:create"` → `"permission:"`. Free-text query params (e.g. search) are run through `sanitize_text` before reaching an external query (ES, etc.) — fine there since the result isn't matched verbatim afterward.
- [ ] Auth routes use `Depends(get_current_user)`, `role_required`/`permission_required`, or — for endpoints that assign a role/permission to a user — `grant_role_required()`/`grant_permission_required()` (data-dependent, not a fixed permission string)
- [ ] Nothing outside `app/cli/seed.py` / direct DB access can set `User.is_superuser` — it must never appear in a request schema
- [ ] No secrets logged (passwords, tokens, keys) — `_redact_value` in `app/core/logger.py` handles known field names, verify new sensitive fields actually contain "password"/"token"/"secret"/"key"
- [ ] No raw SQL string concatenation — always use SQLAlchemy parameterized queries, and `text(...)` for raw SQL strings (not a bare string — SQLAlchemy 2.x async rejects those)
- [ ] File paths use `safe_filename()` from `app/core/data_validation`
- [ ] Response schemas exclude password hashes and internal fields

## Error Handling Review

- [ ] Services raise custom `AppException` subclasses from `app/error/custom_exception.py`, never raw `HTTPException`, never return `None`/error dicts
- [ ] New exceptions registered in `app/error/register_error.py`
- [ ] Repository does NOT catch exceptions (let them bubble to service)
- [ ] Route does NOT have try/except — let the global handler catch everything

## Data Flow Review

- [ ] Request schema (Pydantic) → Service → Repository → DB Model
- [ ] DB Model → Service → Response schema (Pydantic with `from_attributes=True`)
- [ ] No SQLAlchemy models returned directly from route
- [ ] No Pydantic schemas passed into repository (convert to dict or model first)

## Logging Review

- [ ] Routes decorated with `@log_function`
- [ ] New services extend `LoggedService`, new repositories extend `LoggedRepository`

## Resilience Review (this codebase's most common latent bug)

- [ ] Any call to Redis, Celery's `.delay()`, or another external service on a request
      path has an explicit connect/socket timeout. The sync `redis` client and Celery's
      result backend have no default timeout and can block a request thread for a very
      long time (minutes, not seconds) if the target is unreachable — this has hung
      this exact codebase's test suite before.
- [ ] Fire-and-forget Celery tasks set `task_ignore_result=True` (or don't need it set
      globally) — without it, `.delay()` sets up a result-tracking subscription even
      though nothing calls `.get()`.
- [ ] `CircuitBreaker` instances are module-level singletons (see
      `app/core/circuit_breakers.py`), never instantiated per-call — a fresh instance
      never accumulates failures and never trips.
- [ ] External calls wrapped with `async_retry`/`CircuitBreaker` use `app.core.recovery`,
      not ad hoc retry loops.

## Testing Review

- [ ] Tests use the `ac: AsyncClient` fixture for HTTP tests, marked `@pytest.mark.asyncio`
- [ ] Covers: success case, missing fields, invalid input, auth/protected (401),
      forbidden (403 — including grant-delegation denial for hierarchy endpoints),
      not-found (404), duplicate/conflict (400)
- [ ] No real external services called — Redis/ES/Celery are either mocked or expected
      to fail open/fast in the test environment (they aren't running in CI/sandbox)

## General Review Checklist

### Security

- [ ] **Injection**: SQL, command, template injection — parameterized queries only, never `os.system`/`subprocess` with unsanitized input
- [ ] **Authentication/Authorization**: no hardcoded credentials, no IDOR (does the endpoint check the caller may act on *this specific* resource, not just that they're logged in?)
- [ ] **Data exposure**: no sensitive data in logs, error messages, or response bodies
- [ ] **Cryptography**: `bcrypt` for passwords (already standard here), no home-rolled hashing/encoding as a security control
- [ ] **Dependencies**: run `uv run pip-audit` (or `pip-audit` in whatever env is active) for known CVEs in installed packages

### Correctness

- [ ] Logic errors: off-by-one, null/None handling, edge cases (empty list, zero, boundary values)
- [ ] Race conditions: concurrent access without synchronization (check `CircuitBreaker`-style shared mutable state uses its lock)
- [ ] Resource leaks: unclosed sessions/connections/files — async context managers (`async with`) used consistently
- [ ] Error handling: no swallowed exceptions (bare `except: pass`), no missing error paths
- [ ] Missing `await` on async calls

### Performance

- [ ] N+1 queries: DB calls inside a loop — use `selectinload`/batched `IN` queries instead (see `RoleRepository.get_by_ids`, `PermissionRepository.get_by_ids` for the pattern)
- [ ] Blocking/sync I/O in async code (sync `redis`, `requests`, blocking file I/O inside an `async def`)
- [ ] Inefficient algorithms: O(n²) where O(n) is available on hot paths
- [ ] Missing caching for genuinely repeated expensive computations — but don't cache prematurely

### Maintainability

- [ ] Naming: clear, consistent, matches existing conventions in the same layer
- [ ] Complexity: functions > 50 lines or nesting > 3 levels deep are candidates to split
- [ ] Duplication: copy-pasted blocks that should be a shared helper
- [ ] Dead code: unused imports, unreachable branches, unused constructor params
- [ ] Comments explain *why*, not *what* — delete comments that just restate the code

## Common Mistakes to Flag

1. **Service returning raw model**: Must convert to Pydantic response schema
2. **Route importing DB session**: Should use service dependency instead
3. **Service/repository raising `HTTPException`**: Should raise an `AppException` subclass, let the registered handler map it to an HTTP status
4. **Password/token in logs**: verify sensitive field names actually match the logger's redaction keywords
5. **Missing `await` on async calls**
6. **Sync SQLAlchemy imports**: must use `sqlalchemy.ext.asyncio.AsyncSession`, never sync `Session`
7. **No `from_attributes=True` on response schemas**: without it, `model_validate(orm_obj)` fails
8. **Business logic in route**: extract to a service method
9. **Blocking external call with no timeout on a request path** (see Resilience Review above)
10. **Mutable default argument**: `def f(x, lst=[]):` shares state across calls — use `None` and default inside

## Useful commands

```bash
# Recent changes
git diff HEAD~5 --stat
git log --oneline -10

# Flag markers and secret-shaped strings
grep -rn "TODO\|FIXME\|HACK\|XXX" app/
grep -rn "password\|secret\|token" app/ --include="*.py"

# Dependency vulnerabilities
uv run pip-audit

# Complexity (install radon first if not present: uv add --dev radon)
uv run radon cc app -a -nb

# Run the test suite (per-test timeout guards against the hang class above)
uv run pytest -q --timeout=30
```

## Review Output Format

```markdown
## Code Review: [file/component name]

### Summary
[1-2 sentence overview]

### Critical Issues
1. **[Issue]** (file:line): [Description]
   - Impact: [concrete failure scenario — inputs/state that trigger it]
   - Fix: [suggested solution]

### Improvements
1. **[Suggestion]** (file:line): [Description]

### Positive Notes
- [What was done well]

### Verdict
[ ] Ready to merge
[ ] Needs minor changes
[ ] Needs major revision
```
