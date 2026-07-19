"""tenants: Tenant model, tenant_id/perm_version/is_active on users and roles

Revision ID: 4a36f94508d1
Revises: 4ad43bc4d43b
Create Date: 2026-07-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4a36f94508d1'
down_revision: Union[str, Sequence[str], None] = '4ad43bc4d43b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index(op.f("ix_tenants_name"), "tenants", ["name"], unique=True)

    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "users",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("perm_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_foreign_key(
        "fk_users_tenant_id_tenants",
        "users",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # roles.name was globally unique (ix_roles_name); replace with
    # tenant-scoped uniqueness plus a partial index for global (tenant_id
    # IS NULL) roles, since Postgres treats every NULL as distinct under a
    # plain composite unique constraint.
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.add_column(
        "roles",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "roles",
        sa.Column(
            "permission_mask",
            sa.LargeBinary(length=32),
            nullable=False,
            server_default=sa.text("'\\x" + "00" * 32 + "'::bytea"),
        ),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=False)
    op.create_foreign_key(
        "fk_roles_tenant_id_tenants",
        "roles",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint("uq_roles_tenant_id_name", "roles", ["tenant_id", "name"])
    op.create_index(
        "uq_roles_global_name",
        "roles",
        ["name"],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_roles_global_name", table_name="roles")
    op.drop_constraint("uq_roles_tenant_id_name", "roles", type_="unique")
    op.drop_constraint("fk_roles_tenant_id_tenants", "roles", type_="foreignkey")
    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_column("roles", "permission_mask")
    op.drop_column("roles", "tenant_id")
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.drop_constraint("fk_users_tenant_id_tenants", "users", type_="foreignkey")
    op.drop_column("users", "perm_version")
    op.drop_column("users", "tenant_id")
    op.drop_column("users", "is_active")

    op.drop_index(op.f("ix_tenants_name"), table_name="tenants")
    op.drop_table("tenants")
