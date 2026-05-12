"""Tính toán thời gian theo calendar (working time math).

Hàm chính:
  add_working_hours(start, hours, calendar) -> end
  subtract_working_hours(end, hours, calendar) -> start

Mặc định: Mon–Fri, 08:00–17:00 (1h nghỉ trưa → 8h/ngày).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta


@dataclass
class CalendarSpec:
    """Mô tả calendar đơn giản (in-memory).

    weekday_work[i] = list[(start_time, end_time)] cho thứ i (0=Mon..6=Sun).
    exceptions: dict[date, list[(start, end)] | None] (None = nghỉ).
    """
    weekday_work: dict[int, list[tuple[time, time]]] = field(default_factory=dict)
    exceptions: dict[date, list[tuple[time, time]] | None] = field(default_factory=dict)

    @staticmethod
    def standard() -> "CalendarSpec":
        """Mon–Fri, 08:00–12:00 + 13:00–17:00 (8h)."""
        spec = CalendarSpec()
        for d in range(0, 5):
            spec.weekday_work[d] = [
                (time(8, 0), time(12, 0)),
                (time(13, 0), time(17, 0)),
            ]
        spec.weekday_work[5] = []  # Sat
        spec.weekday_work[6] = []  # Sun
        return spec

    @staticmethod
    def hours24() -> "CalendarSpec":
        """24/7."""
        spec = CalendarSpec()
        for d in range(7):
            spec.weekday_work[d] = [(time(0, 0), time(23, 59, 59))]
        return spec

    def windows_for(self, d: date) -> list[tuple[time, time]]:
        """Khung giờ làm việc cho 1 ngày cụ thể."""
        if d in self.exceptions:
            ex = self.exceptions[d]
            return ex or []
        return self.weekday_work.get(d.weekday(), [])

    def is_working_day(self, d: date) -> bool:
        return bool(self.windows_for(d))


def _day_windows(spec: CalendarSpec, d: date) -> list[tuple[datetime, datetime]]:
    """Khung giờ làm việc dạng datetime cho 1 ngày."""
    return [
        (datetime.combine(d, s), datetime.combine(d, e))
        for s, e in spec.windows_for(d)
    ]


def _seconds_in_windows(start: datetime, end: datetime,
                         windows: list[tuple[datetime, datetime]]) -> float:
    """Số giây làm việc trong khoảng [start, end] giao với các window."""
    total = 0.0
    for ws, we in windows:
        a = max(start, ws)
        b = min(end, we)
        if b > a:
            total += (b - a).total_seconds()
    return total


def snap_to_working(dt: datetime, spec: CalendarSpec,
                     forward: bool = True) -> datetime:
    """Đưa dt về thời điểm working time hợp lệ.

    Nếu dt rơi ngoài giờ làm: forward=True → đẩy tới đầu window kế tiếp;
                              forward=False → lùi về cuối window trước.
    """
    cur = dt
    safety = 0
    while safety < 365 * 4:
        safety += 1
        windows = _day_windows(spec, cur.date())
        if forward:
            for ws, we in windows:
                if cur < ws:
                    return ws
                if ws <= cur < we:
                    return cur
            # qua hết window trong ngày → sang ngày sau
            cur = datetime.combine(cur.date() + timedelta(days=1), time(0, 0))
        else:
            for ws, we in reversed(windows):
                if cur > we:
                    return we
                if ws < cur <= we:
                    return cur
            cur = datetime.combine(cur.date() - timedelta(days=1), time(23, 59, 59))
    return dt  # fallback


def add_working_hours(start: datetime, hours: float,
                       spec: CalendarSpec | None = None) -> datetime:
    """Cộng `hours` giờ làm việc kể từ `start`. Bỏ qua thời gian ngoài giờ."""
    spec = spec or CalendarSpec.standard()
    if hours <= 0:
        return snap_to_working(start, spec, forward=True)

    cur = snap_to_working(start, spec, forward=True)
    remaining = hours * 3600.0
    safety = 0
    while remaining > 1e-6 and safety < 365 * 4:
        safety += 1
        windows = _day_windows(spec, cur.date())
        # tìm window đang chứa cur
        progressed = False
        for ws, we in windows:
            if ws <= cur < we:
                slot = (we - cur).total_seconds()
                if slot >= remaining:
                    cur = cur + timedelta(seconds=remaining)
                    return cur
                else:
                    remaining -= slot
                    cur = we
                    progressed = True
                    continue
            if cur < ws:
                # đẩy tới đầu window
                cur = ws
                progressed = True
                break
        if not progressed:
            # đã qua hết window → sang ngày mới
            cur = datetime.combine(cur.date() + timedelta(days=1), time(0, 0))
            cur = snap_to_working(cur, spec, forward=True)
    return cur


def subtract_working_hours(end: datetime, hours: float,
                            spec: CalendarSpec | None = None) -> datetime:
    """Trừ `hours` giờ làm việc trước `end`."""
    spec = spec or CalendarSpec.standard()
    if hours <= 0:
        return snap_to_working(end, spec, forward=False)

    cur = snap_to_working(end, spec, forward=False)
    remaining = hours * 3600.0
    safety = 0
    while remaining > 1e-6 and safety < 365 * 4:
        safety += 1
        windows = _day_windows(spec, cur.date())
        progressed = False
        for ws, we in reversed(windows):
            if ws < cur <= we:
                slot = (cur - ws).total_seconds()
                if slot >= remaining:
                    cur = cur - timedelta(seconds=remaining)
                    return cur
                else:
                    remaining -= slot
                    cur = ws
                    progressed = True
                    continue
            if cur > we:
                cur = we
                progressed = True
                break
        if not progressed:
            cur = datetime.combine(cur.date() - timedelta(days=1), time(23, 59, 59))
            cur = snap_to_working(cur, spec, forward=False)
    return cur


def working_hours_between(start: datetime, end: datetime,
                           spec: CalendarSpec | None = None) -> float:
    """Đếm số giờ làm việc trong [start, end]."""
    spec = spec or CalendarSpec.standard()
    if end <= start:
        return 0.0
    total = 0.0
    cur = start.date()
    while cur <= end.date():
        windows = _day_windows(spec, cur)
        total += _seconds_in_windows(start, end, windows)
        cur += timedelta(days=1)
    return total / 3600.0
