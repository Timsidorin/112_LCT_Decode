"""organizations tables

Revision ID: g2h3i4j5k6l7
Revises: cdbb8c37e36a
Create Date: 2026-06-17 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g2h3i4j5k6l7"
down_revision: Union[str, None] = "cdbb8c37e36a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_owner_id", "organizations", ["owner_id"])

    op.create_table(
        "organization_trainings",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("training_uuid", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["training_uuid"], ["trainings.uuid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("organization_id", "training_uuid"),
    )

    op.create_table(
        "organization_employees",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("position", sa.String(length=150), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("account_generated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organization_employees_organization_id", "organization_employees", ["organization_id"])
    op.create_index("ix_organization_employees_email", "organization_employees", ["email"])
    op.create_index("ix_organization_employees_user_id", "organization_employees", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_organization_employees_user_id", table_name="organization_employees")
    op.drop_index("ix_organization_employees_email", table_name="organization_employees")
    op.drop_index("ix_organization_employees_organization_id", table_name="organization_employees")
    op.drop_table("organization_employees")
    op.drop_table("organization_trainings")
    op.drop_index("ix_organizations_owner_id", table_name="organizations")
    op.drop_table("organizations")
