"""Task model — đầy đủ thuộc tính như MS Project."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .project import Project
    from .assignment import Assignment
    from .dependency import TaskDependency


class TaskConstraint(str, enum.Enum):
    """8 loại ràng buộc của MS Project."""
    ASAP = "ASAP"
    ALAP = "ALAP"
    MSO = "MSO"
    MFO = "MFO"
    SNET = "SNET"
    SNLT = "SNLT"
    FNET = "FNET"
    FNLT = "FNLT"


class TaskType(str, enum.Enum):
    FIXED_DURATION = "FIXED_DURATION"
    FIXED_UNITS = "FIXED_UNITS"
    FIXED_WORK = "FIXED_WORK"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id"), nullable=True,
    )
    wbs: Mapped[str | None] = mapped_column(String(50), nullable=True)
    outline_level: Mapped[int] = mapped_column(Integer, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    name: Mapped[str] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    duration_hours: Mapped[float] = mapped_column(Float, default=8.0)
    is_milestone: Mapped[bool] = mapped_column(Boolean, default=False)
    is_summary: Mapped[bool] = mapped_column(Boolean, default=False)
    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType), default=TaskType.FIXED_UNITS,
    )

    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finish_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    early_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    early_finish: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    late_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    late_finish: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_slack_hours: Mapped[float] = mapped_column(Float, default=0.0)
    free_slack_hours: Mapped[float] = mapped_column(Float, default=0.0)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)

    constraint_type: Mapped[TaskConstraint] = mapped_column(
        Enum(TaskConstraint), default=TaskConstraint.ASAP,
    )
    constraint_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
    )
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    percent_complete: Mapped[float] = mapped_column(Float, default=0.0)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_finish: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_work_hours: Mapped[float] = mapped_column(Float, default=0.0)
    actual_cost: Mapped[float] = mapped_column(Float, default=0.0)

    fixed_cost: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[int] = mapped_column(Integer, default=500)

    calendar_id: Mapped[int | None] = mapped_column(
        ForeignKey("calendars.id"), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")
    parent: Mapped["Task | None"] = relationship(
        remote_side=lambda: [Task.id], back_populates="children",
    )
    children: Mapped[list["Task"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan",
    )
    predecessors: Mapped[list["TaskDependency"]] = relationship(
        foreign_keys="[TaskDependency.successor_id]",
        back_populates="successor", cascade="all, delete-orphan",
    )
    successors: Mapped[list["TaskDependency"]] = relationship(
        foreign_keys="[TaskDependency.predecessor_id]",
        back_populates="predecessor", cascade="all, delete-orphan",
    )
