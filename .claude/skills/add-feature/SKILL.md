---
name: add-feature
description: >
  Step-by-step guide for adding a complete new feature to this FastAPI template.
  Use when user asks to "add a feature", "create a new module", "implement X",
  or when a task touches all layers (route + service + repository + model).
---

Add features following the established layered architecture. Every feature touches every layer.

## Step-by-Step Process

### 1. Define the SQLAlchemy Model

Create in `app/models/` (e.g., `app/models/product.py`):

```python
from sqlalchemy import Column, Integer, String, DateTime, func
from app.database.db import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
```

Export from `app/models/db_model.py`:
```python
from app.models.product import Product
```

### 2. Define Pydantic Schemas

Create `app/schema/product.py`:

```python
from pydantic import BaseModel, Field
from app.core.security.validation import SafeStr

class ProductCreate(BaseModel):
    name: SafeStr = Field(..., min_length=1, max_length=255)

class ProductResponse(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}
```

### 3. Create Repository

Create `app/repositories/product/product.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.logger import LoggedRepository
from app.models.db_model import Product
from app.schema.product import ProductCreate

class ProductRepository(LoggedRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Product]:
        result = await self.db.execute(
            select(Product).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()
```

### 4. Create Service

Create `app/error/product.py` (a new domain gets its own exception file — see the
`project-structure` skill):

```python
from app.error.base import AppException

class ProductException(AppException):
    pass

class ProductExists(AppException):
    def __init__(self, name: str = "unknown"):
        super().__init__(f"Product '{name}' already exists", error_code="product_exists")
```

Register its handler in `app/error/register.py` alongside the others.

Create `app/services/product/service.py`:

```python
from app.core.logger import LoggedService
from app.error.product import ProductExists
from app.repositories.product.product import ProductRepository
from app.schema.product import ProductCreate, ProductResponse
from app.models.db_model import Product

class ProductService(LoggedService):
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    async def create_product(self, data: ProductCreate) -> ProductResponse:
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise ProductExists(data.name)
        product = await self.repo.create(data)
        return ProductResponse.model_validate(product)

    async def list_products(self, skip: int = 0, limit: int = 20) -> list[ProductResponse]:
        products = await self.repo.get_all(skip=skip, limit=limit)
        return [ProductResponse.model_validate(p) for p in products]
```

### 5. Wire Dependencies

Create `app/core/dependency_factory/product.py` (new domain → new module) and add it
to the re-exports in `app/core/dependency_factory/__init__.py`:

```python
def get_product_repository(db: AsyncSession = Depends(get_db)) -> ProductRepository:
    return ProductRepository(db)

def get_product_service(
    repo: ProductRepository = Depends(get_product_repository),
) -> ProductService:
    return ProductService(repo)
```

### 6. Create Route

Create `app/api/v1/routes/product.py`:

```python
from typing import Annotated
from fastapi import APIRouter, Depends, status
from app.core.dependency_factory import get_product_service
from app.core.logger import log_function
from app.schema.product import ProductCreate, ProductResponse
from app.services.product.service import ProductService
from app.core.dependencies import role_required

router = APIRouter(tags=["Products"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
@log_function
async def create_product(
    data: ProductCreate,
    service: Annotated[ProductService, Depends(get_product_service)],
    _: None = Depends(role_required(["admin"])),
):
    return await service.create_product(data)

@router.get("/", response_model=list[ProductResponse])
@log_function
async def list_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    skip: int = 0,
    limit: int = 20,
):
    return await service.list_products(skip=skip, limit=limit)
```

### 7. Register Router

In `app/main.py`:
```python
from app.api.v1.routes import product
app.include_router(product.router, prefix="/api/v1/products")
```

### 8. Create Migration

```bash
alembic revision --autogenerate -m "add products table"
alembic upgrade head
```

## Checklist

- [ ] Model in `app/models/` + exported from `db_model.py`
- [ ] Schema in `app/schema/` with `model_config = {"from_attributes": True}`
- [ ] Repository extends `LoggedRepository`
- [ ] Service extends `LoggedService`, validates + raises exceptions
- [ ] Dependencies wired in `app/core/dependency_factory/<domain>.py`
- [ ] Exceptions (if any) in `app/error/<domain>.py`, handlers registered in `app/error/register.py`
- [ ] Router registered in `app/main.py`
- [ ] Migration created and applied
- [ ] Tests written (see write-tests skill)