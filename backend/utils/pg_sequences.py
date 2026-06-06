"""Синхронизация PostgreSQL sequences с фактическими MAX(id) в таблицах."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Создаёт sequence при отсутствии и выставляет next id = MAX(id) + 1.
_SYNC_TRAINING_STEPS_ID = text(
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


async def sync_training_steps_id_sequence(session: AsyncSession) -> None:
    """Исправляет рассинхрон training_steps_id_seq (duplicate key на training_steps_pkey)."""
    await session.execute(_SYNC_TRAINING_STEPS_ID)
