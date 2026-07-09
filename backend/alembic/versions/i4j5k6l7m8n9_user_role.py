"""user role for employees

Revision ID: i4j5k6l7m8n9
Revises: h3i4j5k6l7m8
Create Date: 2026-06-17 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "i4j5k6l7m8n9"
down_revision: Union[str, None] = "h3i4j5k6l7m8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="creator"),
    )
    op.execute(
        """
        UPDATE users SET role = 'employee'
        WHERE id IN (
            SELECT oe.user_id FROM organization_employees oe
            WHERE oe.user_id IS NOT NULL AND oe.account_generated = true
        )
        AND id NOT IN (SELECT DISTINCT owner_id FROM organizations)
        AND id NOT IN (SELECT DISTINCT creator_id FROM trainings WHERE creator_id IS NOT NULL)
        """
    )


def downgrade() -> None:
    op.drop_column("users", "role")
