"""tenant permission ceiling: allowed_permission_mask on tenants

Revision ID: 7f2a19c3d5e8
Revises: 4a36f94508d1
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f2a19c3d5e8'
down_revision: Union[str, Sequence[str], None] = '4a36f94508d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# TENANT_ROLE_MASK as of this migration (every PERMISSION_REGISTRY bit except
# the 5 SUPERUSER_ONLY_PERMISSIONS: tenant:create/read/read.id/update/deactivate,
# bits 13-17) — bits 0-12 and 18 set, as 32 big-endian bytes. Hardcoded rather
# than imported: this backfill must stay pinned to what
# `RoleRepository.create_root_tenant_role` actually granted every existing
# tenant's admin role at the time they were created, not to whatever the
# registry looks like whenever this migration happens to run.
_TENANT_ROLE_MASK_HEX = "0000000000000000000000000000000000000000000000000000000000041fff"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tenants",
        sa.Column(
            "allowed_permission_mask",
            sa.LargeBinary(length=32),
            nullable=False,
            server_default=sa.text(f"'\\x{_TENANT_ROLE_MASK_HEX}'::bytea"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tenants", "allowed_permission_mask")
