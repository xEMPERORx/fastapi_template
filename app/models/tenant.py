import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.rbac.mask import PermissionMaskType
from app.core.rbac.registry import names_for_mask
from app.database.postgres_db import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Ceiling on what this tenant's roles may ever hold — a superuser sets
    # this at tenant creation (defaulting to every non-superuser-only
    # permission) and can narrow or widen it later. Every tenant-scoped
    # role's mask, at creation or via add_permission_to_role, must be a
    # subset of this (see `RoleService`) — separate from, and stricter than,
    # `TENANT_ROLE_MASK`, which is only the hard ceiling no tenant can ever
    # exceed regardless of what a superuser configures.
    allowed_permission_mask = mapped_column(PermissionMaskType, nullable=False, default=0)

    users = relationship("User", back_populates="tenant")
    roles = relationship("Role", back_populates="tenant")

    @property
    def allowed_permissions(self) -> list[str]:
        """Name form of `allowed_permission_mask`, for API responses."""
        return names_for_mask(self.allowed_permission_mask)
