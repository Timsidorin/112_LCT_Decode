import enum
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, enum.Enum):
    VIDEO_PROCESSING = "video_processing"
    PDF_PROCESSING = "pdf_processing"


class ProcessingTask(Base):
    """Задача фоновой обработки медиафайла."""

    __tablename__ = "processing_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    task_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(32),
        nullable=False,
        default=TaskStatus.PENDING.value,
        index=True,
    )
    result_url: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    progress: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    original_filename: Mapped[Optional[str]] = mapped_column(
        sa.String(512), nullable=True
    )
    training_uuid: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )
    steps_created: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("NOW()"),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    user: Mapped["User"] = relationship("User", back_populates="processing_tasks")


# Гарантируем регистрацию User в mapper registry
from .users import User  # noqa: E402,F401
