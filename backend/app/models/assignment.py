"""Assignment — gán resource cho task."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .task import Task
    from .resource import Resource


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        UniqueConstraint("task_id", "resource_id", name="uq_task_resource"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"))

    units: Mapped[float] = mapped_column(Float, default=1.0)
    work_hours: Mapped[float] = mapped_column(Float, default=0.0)
    actual_work_hours: Mapped[float] = mapped_column(Float, default=0.0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)

    task: Mapped["Task"] = relationship(back_populates="assignments")
    resource: Mapped["Resource"] = relationship(back_populates="assignments")
