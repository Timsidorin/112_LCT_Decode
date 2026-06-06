"""Доступ к БД из Celery: сессия привязана к текущей задаче."""

from typing import Optional
from uuid import UUID

from models.tasks import ProcessingTask
from worker.task_runtime import get_worker_session_factory, run_worker_task


async def _update_task_async(
    task_id: UUID,
    status: str,
    *,
    result_url: Optional[str] = None,
    error_message: Optional[str] = None,
    progress: Optional[int] = None,
    steps_created: Optional[int] = None,
) -> Optional[ProcessingTask]:
    factory = get_worker_session_factory()
    async with factory() as session:
        task = await session.get(ProcessingTask, task_id)
        if not task:
            return None
        task.status = status
        if result_url is not None:
            task.result_url = result_url
        if error_message is not None:
            task.error_message = error_message
        if progress is not None:
            task.progress = progress
        if steps_created is not None:
            task.steps_created = steps_created
        await session.commit()
        await session.refresh(task)
        return task


async def _get_task_async(task_id: UUID) -> Optional[ProcessingTask]:
    factory = get_worker_session_factory()
    async with factory() as session:
        return await session.get(ProcessingTask, task_id)


def update_task_status(
    task_id: str,
    status: str,
    *,
    result_url: Optional[str] = None,
    error_message: Optional[str] = None,
    progress: Optional[int] = None,
    steps_created: Optional[int] = None,
) -> Optional[ProcessingTask]:
    return run_worker_task(
        _update_task_async(
            UUID(task_id),
            status,
            result_url=result_url,
            error_message=error_message,
            progress=progress,
            steps_created=steps_created,
        )
    )


def get_task(task_id: str) -> Optional[ProcessingTask]:
    return run_worker_task(_get_task_async(UUID(task_id)))
