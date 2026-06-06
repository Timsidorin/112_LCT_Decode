#!/usr/bin/env python3
"""Помечает зависшие задачи failed и очищает очередь Celery в Redis."""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import async_session
from core.logging_config import logger
from models.tasks import TaskStatus
from repositories.tasks_repository import TasksRepository


async def fail_stuck_tasks(user_id: int | None = None) -> int:
    async with async_session() as session:
        repo = TasksRepository(session)
        count = await repo.fail_active_tasks(
            user_id=user_id,
            error_message="Задача отменена (очистка зависшей очереди)",
        )
    return count


def purge_celery_queue() -> None:
    try:
        from core.celery_app import celery_app

        purged = celery_app.control.purge()
        logger.info("Celery purge: удалено сообщений из очереди: {}", purged)
        print(f"Celery: удалено сообщений из очереди: {purged}")
    except Exception as exc:
        logger.warning("Не удалось очистить очередь Celery: {}", exc)
        print(f"Не удалось очистить очередь Celery: {exc}", file=sys.stderr)


def main() -> None:
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    count = asyncio.run(fail_stuck_tasks(user_id))
    print(f"Помечено failed: {count} задач (статусы {TaskStatus.PENDING.value}/{TaskStatus.PROCESSING.value})")
    purge_celery_queue()
    print("Перезапустите Celery worker: celery -A core.celery_app worker --loglevel=info")


if __name__ == "__main__":
    main()
