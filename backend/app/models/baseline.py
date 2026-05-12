"""Baseline — snapshot kế hoạch ban đầu (0..10)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .project import Project


class Baseline(Base):
    __tablename__ = "baselines"
    __table_args__ = (
        UniqueConstraint("project_id", "number", name="uq_project_baseline"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    number: Mapped[int] = mapped_column(Integer)  # 0..10
    name: Mapped[str] = mapped_column(String(200))
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="baselines")
    task_snapshots: Mapped[list["BaselineTask"]] = relationship(
        back_populates="baseline", cascade="all, delete-orphan",
    )


class BaselineTask(Base):
    __tablename__ = "baseline_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    baseline_id: Mapped[int] = mapped_column(ForeignKey("baselines.id"))
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))

    baseline_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    baseline_finish: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    baseline_duration_hours: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_work_hours: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_cost: Mapped[float] = mapped_column(Float, default=0.0)

    baseline: Mapped[Baseline] = relationship(back_populates="task_snapshots")
