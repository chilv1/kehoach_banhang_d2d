"""Resource — Work / Material / Cost."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .project import Project
    from .assignment import Assignment


class ResourceType(str, enum.Enum):
    WORK = "WORK"          # Người / thiết bị thời gian-based
    MATERIAL = "MATERIAL"  # Nguyên vật liệu (per-unit cost)
    COST = "COST"          # Chi phí thuần (không theo time)


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(200))
    initials: Mapped[str | None] = mapped_column(String(20), nullable=True)
    type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType), default=ResourceType.WORK,
    )
    group: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)

    max_units: Mapped[float] = mapped_column(Float, default=1.0)  # 1.0 = 100%
    standard_rate: Mapped[float] = mapped_column(Float, default=0.0)
    overtime_rate: Mapped[float] = mapped_column(Float, default=0.0)
    cost_per_use: Mapped[float] = mapped_column(Float, default=0.0)

    calendar_id: Mapped[int | None] = mapped_column(
        ForeignKey("calendars.id"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="resources")
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="resource", cascade="all, delete-orphan",
    )
