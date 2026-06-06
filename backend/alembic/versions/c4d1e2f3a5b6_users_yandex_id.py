"""users yandex_id for Yandex ID OAuth

Revision ID: c4d1e2f3a5b6
Revises: b3e9c4f8a1d2
Create Date: 2026-05-13

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c4d1e2f3a5b6"
down_revision: Union[str, None] = "b3e9c4f8a1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("yandex_id", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_users_yandex_id", "users", ["yandex_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_yandex_id", table_name="users")
    op.drop_column("users", "yandex_id")
