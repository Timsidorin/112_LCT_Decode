from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskTypeEnum(str, Enum):
    VIDEO_PROCESSING = "video_processing"
    PDF_PROCESSING = "pdf_processing"


class TaskCreateResponse(BaseModel):
    task_id: UUID
    status: TaskStatusEnum
    message: str = "Принято в обработку"
    training_uuid: Optional[UUID] = None


class TaskResponse(BaseModel):
    id: UUID
    user_id: int
    file_url: str
    task_type: str
    status: str
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    progress: int = 0
    original_filename: Optional[str] = None
    training_uuid: Optional[UUID] = None
    steps_created: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskNotificationPayload(BaseModel):
    """Сообщение для WebSocket / Redis PubSub."""

    type: str = "task_update"
    task_id: str
    status: str
    progress: int = 0
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    message: Optional[str] = None
    training_uuid: Optional[str] = None
    steps_created: Optional[int] = None
    task_type: Optional[str] = None
