"""Изолированный asyncio + DB runtime на одну Celery-задачу."""

from __future__ import annotations

import asyncio
from contextvars import ContextVar
from typing import Any, Coroutine, TypeVar

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import get_db_url

T = TypeVar("T")

_session_factory_var: ContextVar[async_sessionmaker[AsyncSession] | None] = ContextVar(
    "worker_session_factory",
    default=None,
)


def get_worker_session_factory() -> async_sessionmaker[AsyncSession]:
    factory = _session_factory_var.get()
    if factory is None:
        raise RuntimeError("Worker DB session factory is not initialized")
    return factory


async def _run_with_fresh_runtime(coro: Coroutine[Any, Any, T]) -> T:
    engine = create_async_engine(
        get_db_url(),
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=3,
        max_overflow=5,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    token = _session_factory_var.set(factory)
    try:
        return await coro
    finally:
        _session_factory_var.reset(token)
        await engine.dispose()


def run_worker_task(coro: Coroutine[Any, Any, T]) -> T:
    """Новый event loop и пул БД на каждую задачу — без утечек между запусками."""
    return asyncio.run(_run_with_fresh_runtime(coro))
