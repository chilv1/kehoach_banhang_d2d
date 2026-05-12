"""Project root entity."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .task import Task
    from .resource import Resource
    from .baseline import Baseline


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime)
    finish_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    calendar_id: Mapped[int | None] = mapped_column(
        ForeignKey("calendars.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
    )
    resources: Mapped[list["Resource"]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
    )
    baselines: Mapped[list["Baseline"]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
    )
