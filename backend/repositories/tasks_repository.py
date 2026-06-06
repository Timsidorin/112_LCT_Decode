from typing import List, Optional
from uuid import UUID

from models.tasks import TaskStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.tasks import ProcessingTask
from repositories.base_repository import BaseRepository


class TasksRepository(BaseRepository[ProcessingTask]):
    def __init__(self, session: AsyncSession):
        super().__init__(ProcessingTask, session, pk_field="id")

    async def get_by_uuid(self, task_id: UUID) -> Optional[ProcessingTask]:
        return await self.session.get(self.model, task_id)

    async def list_active_by_user(
        self, user_id: int, limit: int = 20
    ) -> List[ProcessingTask]:
        active = (TaskStatus.PENDING.value, TaskStatus.PROCESSING.value)
        query = (
            select(self.model)
            .where(self.model.user_id == user_id, self.model.status.in_(active))
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def fail_active_tasks(
        self,
        *,
        user_id: Optional[int] = None,
        error_message: str = "Задача отменена",
    ) -> int:
        active = (TaskStatus.PENDING.value, TaskStatus.PROCESSING.value)
        query = select(self.model).where(self.model.status.in_(active))
        if user_id is not None:
            query = query.where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        tasks = list(result.scalars().all())
        for task in tasks:
            task.status = TaskStatus.FAILED.value
            task.error_message = error_message
            task.progress = 0
        if tasks:
            await self.session.commit()
        return len(tasks)

    async def list_by_user(
        self, user_id: int, skip: int = 0, limit: int = 50
    ) -> List[ProcessingTask]:
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        task_id: UUID,
        status: str,
        *,
        result_url: Optional[str] = None,
        error_message: Optional[str] = None,
        progress: Optional[int] = None,
    ) -> Optional[ProcessingTask]:
        task = await self.get_by_uuid(task_id)
        if not task:
            return None
        task.status = status
        if result_url is not None:
            task.result_url = result_url
        if error_message is not None:
            task.error_message = error_message
        if progress is not None:
            task.progress = progress
        await self.session.commit()
        await self.session.refresh(task)
        return task
