from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import UUID4

from core.database import get_async_session
from depends import get_current_user
from models.users import User
from repositories.tasks_repository import TasksRepository
from schemas.tasks import TaskResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/tasks", tags=["Задачи обработки"])


async def get_tasks_repository(
    session: AsyncSession = Depends(get_async_session),
) -> TasksRepository:
    return TasksRepository(session)


@router.get("/", response_model=List[TaskResponse], name="Список задач пользователя")
async def list_tasks(
    active_only: bool = Query(False, description="Только активные (pending/processing)"),
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    tasks_repo: TasksRepository = Depends(get_tasks_repository),
):
    if active_only:
        tasks = await tasks_repo.list_active_by_user(user.id, limit=limit)
    else:
        tasks = await tasks_repo.list_by_user(user.id, limit=limit)
    return tasks


@router.post("/active/dismiss", name="Сбросить зависшие задачи пользователя")
async def dismiss_active_tasks(
    user: User = Depends(get_current_user),
    tasks_repo: TasksRepository = Depends(get_tasks_repository),
):
    """Помечает pending/processing задачи failed — если очередь «зависла» в интерфейсе."""
    count = await tasks_repo.fail_active_tasks(
        user_id=user.id,
        error_message="Задача отменена пользователем",
    )
    return {"dismissed": count}


@router.get("/{task_id}", response_model=TaskResponse, name="Задача по ID")
async def get_task(
    task_id: UUID4,
    user: User = Depends(get_current_user),
    tasks_repo: TasksRepository = Depends(get_tasks_repository),
):
    task = await tasks_repo.get_by_uuid(task_id)
    if not task or task.user_id != user.id:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    return task
