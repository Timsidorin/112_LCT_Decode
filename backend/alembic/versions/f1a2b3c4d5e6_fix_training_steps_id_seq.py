"""fix training_steps id sequence

Revision ID: f1a2b3c4d5e6
Revises: e8f9a0b1c2d3
Create Date: 2026-06-06 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e8f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE
            seq_name text;
            max_id bigint;
        BEGIN
            seq_name := pg_get_serial_sequence('training_steps', 'id');
            IF seq_name IS NULL THEN
                CREATE SEQUENCE IF NOT EXISTS training_steps_id_seq;
                ALTER TABLE training_steps
                    ALTER COLUMN id SET DEFAULT nextval('training_steps_id_seq');
                ALTER SEQUENCE training_steps_id_seq OWNED BY training_steps.id;
                seq_name := 'training_steps_id_seq';
            END IF;

            SELECT COALESCE(MAX(id), 0) INTO max_id FROM training_steps;
            EXECUTE format(
                'SELECT setval(%L, GREATEST(%s, 1))',
                seq_name,
                max_id
            );
        END $$;
        """
    )


def downgrade() -> None:
    pass
