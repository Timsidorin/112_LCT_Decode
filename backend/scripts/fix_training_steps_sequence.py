#!/usr/bin/env python3
"""Синхронизирует training_steps_id_seq с MAX(id) в таблице."""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import async_session
from utils.pg_sequences import sync_training_steps_id_sequence


async def main() -> None:
    async with async_session() as session:
        await sync_training_steps_id_sequence(session)
        await session.commit()
    print("training_steps_id_seq синхронизирован с MAX(id)")


if __name__ == "__main__":
    asyncio.run(main())
