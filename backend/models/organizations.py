from datetime import datetime
from typing import List, Optional
import uuid

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy import Column, ForeignKey, Integer, Table, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

organization_trainings = Table(
    "organization_trainings",
    Base.metadata,
    Column(
        "organization_id",
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "training_uuid",
        UUID(as_uuid=True),
        ForeignKey("trainings.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    extend_existing=True,
)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime, server_default=text("NOW()")
    )

    owner: Mapped["User"] = relationship("models.users.User", lazy="selectin")
    employees: Mapped[List["OrganizationEmployee"]] = relationship(
        "OrganizationEmployee",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    trainings: Mapped[List["Training"]] = relationship(
        "models.trainings.Training",
        secondary=organization_trainings,
        lazy="selectin",
    )


class OrganizationEmployee(Base):
    __tablename__ = "organization_employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(sa.String(100), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    position: Mapped[Optional[str]] = mapped_column(sa.String(150), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    account_generated: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false(), default=False
    )
    account_expires_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    provision_ref: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    login_id: Mapped[Optional[str]] = mapped_column(
        sa.String(32), nullable=True, index=True
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime, server_default=text("NOW()")
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="employees", lazy="selectin"
    )
    user: Mapped[Optional["User"]] = relationship(
        "models.users.User", lazy="selectin"
    )
