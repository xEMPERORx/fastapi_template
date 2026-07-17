"""hierarchical rbac: superuser bootstrap, direct user permissions, role grant delegation

Revision ID: 2d86ed6bd641
Revises: 10328bfc2473
Create Date: 2026-07-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2d86ed6bd641'
down_revision: Union[str, Sequence[str], None] = '10328bfc2473'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_created_by_id_users",
        "users",
        "users",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "user_permissions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True, nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id"), primary_key=True, nullable=False),
    )

    op.create_table(
        "role_grantable_roles",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), primary_key=True, nullable=False),
        sa.Column("grantable_role_id", sa.Integer(), sa.ForeignKey("roles.id"), primary_key=True, nullable=False),
    )

    op.create_table(
        "role_grantable_permissions",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), primary_key=True, nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id"), primary_key=True, nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("role_grantable_permissions")
    op.drop_table("role_grantable_roles")
    op.drop_table("user_permissions")
    op.drop_constraint("fk_users_created_by_id_users", "users", type_="foreignkey")
    op.drop_column("users", "created_by_id")
    op.drop_column("users", "is_superuser")
