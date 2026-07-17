---
name: add-endpoint
description: >
  Guide for adding a new API endpoint to an existing feature in this FastAPI template.
  Use when user asks to "add an endpoint", "add a route", "add an API",
  or when adding endpoints to existing routers.
---

Add endpoints following the project's layered pattern. Even a simple endpoint touches schema, service, repository, and route layers.

## Quick Reference

### Read Endpoint (GET)
```
Route: @router.get("/{id}", response_model=XResponse)
Service: async def get_x(self, id: int) -> XResponse:
Repository: async def get_by_id(self, id: int) -> X | None:
```

### Create Endpoint (POST)
```
Route: @router.post("/", response_model=XResponse, status_code=201)
Service: async def create_x(self, data: XCreate) -> XResponse:
Repository: async def create(self, data: XCreate) -> X:
```

### Update Endpoint (PUT/PATCH)
```
Route: @router.put("/{id}", response_model=XResponse)
Service: async def update_x(self, id: int, data: XUpdate) -> XResponse:
Repository: async def update(self, id: int, data: dict) -> X:
```

### Delete Endpoint (DELETE)
```
Route: @router.delete("/{id}", status_code=204)
Service: async def delete_x(self, id: int) -> None:
Repository: async def delete(self, id: int) -> None:
```

## Full Example: Add GET /users/{id} to existing User module

### 1. Schema (if new response shape needed)

In `app/schema/user.py`:
```python
class UserDetailResponse(UserResponse):
    created_at: datetime
    roles: list[str] = []
```

### 2. Repository method

In existing repository:
```python
async def get_by_id(self, user_id: int) -> User | None:
    from sqlalchemy.orm import selectinload
    result = await self.db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

### 3. Service method

In existing service:
```python
async def get_user_detail(self, user_id: int) -> UserDetailResponse:
    user = await self.repo.get_by_id(user_id)
    if not user:
        raise UserNotFound(username=user_id)
    return UserDetailResponse.model_validate(user)
```

### 4. Dependency wiring

In `app/core/dependency_factory.py` (if not already wired):
```python
def get_user_detail_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserDetailService:
    return UserDetailService(user_repo)
```

### 5. Route

In existing router file:
```python
@router.get("/{user_id}", response_model=UserDetailResponse)
@log_function
async def get_user(
    user_id: int,
    service: Annotated[UserDetailService, Depends(get_user_detail_service)],
):
    return await service.get_user_detail(user_id)
```

## Rules

- Always use `@log_function` on route handlers
- Always use Annotated with Depends for service injection
- Never access DB directly from route — always through service → repository
- Use `response_model` on every route for automatic serialization + validation
- Use `model_config = {"from_attributes": True}` on response schemas (not create schemas)
- Raise custom exceptions from services, never return error tuples
- Auth endpoints: add `current_user = Depends(get_current_user)`, `Depends(role_required([...]))`, or `Depends(permission_required("x:y"))`
- Endpoints that grant a role/permission to a user (path params `role_id`/`permission_id`) use `Depends(grant_role_required())` / `Depends(grant_permission_required())` instead — the allowed set is per-actor and data-dependent (see `app/core/rbac.py`), not a fixed permission string

## What NOT To Do

```python
# BAD - business logic in route
@router.get("/{id}")
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    user = await db.execute(select(User).where(User.id == id))
    return user.scalar_one_or_none()

# BAD - no response model, no logging, no service layer
```