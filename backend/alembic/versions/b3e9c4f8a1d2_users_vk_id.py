"""users vk_id for VK OAuth

Revision ID: b3e9c4f8a1d2
Revises: 9c67d7320691
Create Date: 2026-05-03

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b3e9c4f8a1d2"
down_revision: Union[str, None] = "9c67d7320691"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("vk_id", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_users_vk_id", "users", ["vk_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_vk_id", table_name="users")
    op.drop_column("users", "vk_id")
