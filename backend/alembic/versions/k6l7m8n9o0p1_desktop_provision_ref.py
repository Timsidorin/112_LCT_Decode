"""desktop provision_ref for HR app

Revision ID: k6l7m8n9o0p1
Revises: j5k6l7m8n9o0
Create Date: 2026-07-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "k6l7m8n9o0p1"
down_revision: Union[str, None] = "j5k6l7m8n9o0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organization_employees",
        sa.Column("provision_ref", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "organization_employees",
        sa.Column("login_id", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_organization_employees_provision_ref",
        "organization_employees",
        ["provision_ref"],
    )
    op.create_index(
        "ix_organization_employees_login_id",
        "organization_employees",
        ["login_id"],
    )
    op.create_unique_constraint(
        "uq_organization_employees_org_provision_ref",
        "organization_employees",
        ["organization_id", "provision_ref"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_organization_employees_org_provision_ref",
        "organization_employees",
        type_="unique",
    )
    op.drop_index("ix_organization_employees_login_id", table_name="organization_employees")
    op.drop_index("ix_organization_employees_provision_ref", table_name="organization_employees")
    op.drop_column("organization_employees", "login_id")
    op.drop_column("organization_employees", "provision_ref")
