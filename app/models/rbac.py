from sqlalchemy import Column, ForeignKey, Index, Integer, String, Table, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.rbac.mask import PermissionMaskType
from app.database.postgres_db import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)

user_permissions = Table(
    "user_permissions",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)

# Self-referential: which roles a holder of `role_id` is allowed to assign to other users.
role_grantable_roles = Table(
    "role_grantable_roles",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("grantable_role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)

# Which permissions a holder of `role_id` is allowed to grant directly to a user.
role_grantable_permissions = Table(
    "role_grantable_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    __table_args__ = (
        # Enforces name-uniqueness among tenant-owned roles (tenant_id NOT NULL).
        UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_id_name"),
        # Postgres/SQLite treat every NULL as distinct for the constraint above,
        # so a second partial index is needed to enforce uniqueness among
        # *global* roles (tenant_id IS NULL) — otherwise two different global
        # roles could both be named "admin" without either constraint noticing.
        Index(
            "uq_roles_global_name",
            "name",
            unique=True,
            postgresql_where=text("tenant_id IS NULL"),
            sqlite_where=text("tenant_id IS NULL"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    # NULL = a global/system role available to every tenant (e.g. seed roles).
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    # Cached OR-reduction of this role's permissions' bit positions —
    # recomputed in the same transaction as any role_permissions mutation
    # (see `RoleRepository.add_permission`/`remove_permission`), so it never
    # needs to be recomputed from the join table on the read/token-mint path.
    permission_mask = Column(PermissionMaskType, nullable=False, default=0)
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")
    tenant = relationship("Tenant", back_populates="roles")

    grantable_roles = relationship(
        "Role",
        secondary=role_grantable_roles,
        primaryjoin=id == role_grantable_roles.c.role_id,
        secondaryjoin=id == role_grantable_roles.c.grantable_role_id,
        backref="grantable_by_roles",
    )
    grantable_permissions = relationship(
        "Permission",
        secondary=role_grantable_permissions,
        back_populates="grantable_by_roles",
    )


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    # Mirrors this permission's fixed bit position in
    # `app.core.rbac.registry.PERMISSION_REGISTRY` — kept in sync by
    # `app/cli/sync_permissions.py` on every startup. Nullable only for a
    # legacy row that predates the registry (should not happen in practice
    # since the registry is synced before any other permission can be
    # created); such a row simply can't be OR'd into any mask.
    bit_position = Column(Integer, unique=True, nullable=True)
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    users = relationship("User", secondary=user_permissions, back_populates="permissions")
    grantable_by_roles = relationship(
        "Role",
        secondary=role_grantable_permissions,
        back_populates="grantable_permissions",
    )
