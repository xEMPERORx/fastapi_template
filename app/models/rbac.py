from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.db import Base


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

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")

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
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    users = relationship("User", secondary=user_permissions, back_populates="permissions")
    grantable_by_roles = relationship(
        "Role",
        secondary=role_grantable_permissions,
        back_populates="grantable_permissions",
    )
