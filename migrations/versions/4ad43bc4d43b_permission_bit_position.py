"""permission bit_position: mirrors the fixed permission registry's bit index

Revision ID: 4ad43bc4d43b
Revises: 2d86ed6bd641
Create Date: 2026-07-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ad43bc4d43b'
down_revision: Union[str, Sequence[str], None] = '2d86ed6bd641'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "permissions",
        sa.Column("bit_position", sa.Integer(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_permissions_bit_position", "permissions", ["bit_position"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_permissions_bit_position", "permissions", type_="unique")
    op.drop_column("permissions", "bit_position")
