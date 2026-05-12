"""Task dependency với 4 link type chuẩn MS Project."""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .task import Task


class LinkType(str, enum.Enum):
    FS = "FS"  # Finish-to-Start (phổ biến nhất)
    SS = "SS"  # Start-to-Start
    FF = "FF"  # Finish-to-Finish
    SF = "SF"  # Start-to-Finish (hiếm)


class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        UniqueConstraint("predecessor_id", "successor_id", name="uq_pred_succ"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    predecessor_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    successor_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    link_type: Mapped[LinkType] = mapped_column(Enum(LinkType), default=LinkType.FS)
    # lag_hours dương = delay; âm = lead (overlap)
    lag_hours: Mapped[float] = mapped_column(Float, default=0.0)

    predecessor: Mapped["Task"] = relationship(
        foreign_keys=[predecessor_id], back_populates="successors",
    )
    successor: Mapped["Task"] = relationship(
        foreign_keys=[successor_id], back_populates="predecessors",
    )
