"""Calendar & WorkingTime — định nghĩa lịch làm việc."""
from __future__ import annotations

from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .project import Project


class Calendar(Base):
    """Standard / 24 Hours / Night Shift / custom."""

    __tablename__ = "calendars"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    base_calendar_id: Mapped[int | None] = mapped_column(
        ForeignKey("calendars.id"), nullable=True
    )

    working_times: Mapped[list["WorkingTime"]] = relationship(
        back_populates="calendar", cascade="all, delete-orphan",
    )


class WorkingTime(Base):
    """Khung giờ làm việc cho 1 calendar.

    - day_of_week 0..6 (Mon..Sun) → áp dụng hàng tuần.
    - exception_date có giá trị → ngoại lệ cho 1 ngày cụ thể.
    """

    __tablename__ = "working_times"

    id: Mapped[int] = mapped_column(primary_key=True)
    calendar_id: Mapped[int] = mapped_column(ForeignKey("calendars.id"))
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exception_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[time] = mapped_column(Time, default=time(8, 0))
    end_time: Mapped[time] = mapped_column(Time, default=time(17, 0))
    is_working: Mapped[bool] = mapped_column(Boolean, default=True)

    calendar: Mapped[Calendar] = relationship(back_populates="working_times")
