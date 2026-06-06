"""processing_tasks training_uuid

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-06-03 19:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, None] = "d7e8f9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processing_tasks",
        sa.Column("training_uuid", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "processing_tasks",
        sa.Column("steps_created", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_processing_tasks_training_uuid"),
        "processing_tasks",
        ["training_uuid"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_processing_tasks_training_uuid"), table_name="processing_tasks"
    )
    op.drop_column("processing_tasks", "steps_created")
    op.drop_column("processing_tasks", "training_uuid")
