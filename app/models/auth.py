from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.postgres_db import Base


class RefreshToken(Base):
    __tablename__ = "refreshtoken"

    token: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # NULL = global superadmin, not tied to any tenant.
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True
    )
    # Bumped whenever this user's effective permission mask could change
    # (their own direct grants, a role's mask, or their role membership) —
    # compared against the JWT's `perm_version` claim by the authz cache
    # (see `app.core.authz_cache`) to detect a stale access token.
    perm_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    roles = relationship("Role", secondary="user_roles", back_populates="users")
    permissions = relationship("Permission", secondary="user_permissions", back_populates="users")
    created_by = relationship("User", remote_side=[id], backref="created_users")
    tenant = relationship("Tenant", back_populates="users")
