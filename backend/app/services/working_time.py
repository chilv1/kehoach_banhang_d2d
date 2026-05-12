"""Working time math (calendar-aware).

Mon–Fri, 08:00–12:00 + 13:00–17:00 (8h/dích standard).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta


@dataclass
class CalendarSpec:
    weekday_work: dict[int, list[tuple[time, time]]] = field(default_factory=dict)
    exceptions: dict[date, list[tuple[time, time]] | None] = field(default_factory=dict)

    @staticmethod
    def standard() -> "CalendarSpec":
        spec = CalendarSpec()
        for d in range(0, 5):
            spec.weekday_work[d] = [
                (time(8, 0), time(12, 0)),
                (time(13, 0), time(17, 0)),
            ]
        spec.weekday_work[5] = []
        spec.weekday_work[6] = []
        return spec

    @staticmethod
    def hours24() -> "CalendarSpec":
        spec = CalendarSpec()
        for d in range(7):
            spec.weekday_work[d] = [(time(0, 0), time(23, 59, 59))]
        return spec

    def windows_for(self, d: date) -> list[tuple[time, time]]:
        if d in self.exceptions:
            ex = self.exceptions[d]
            return ex or []
        return self.weekday_work.get(d.weekday(), [])

    def is_working_day(self, d: date) -> bool:
        return bool(self.windows_for(d))


def _day_windows(spec, d):
    return [(datetime.combine(d, s), datetime.combine(d, e)) for s, e in spec.windows_for(d)]


def _seconds_in_windows(start, end, windows):
    total = 0.0
    for ws, we in windows:
        a = max(start, ws); b = min(end, we)
        if b > a:
            total += (b - a).total_seconds()
    return total


def snap_to_working(dt, spec, forward=True):
    cur = dt; safety = 0
    while safety < 365 * 4:
        safety += 1
        windows = _day_windows(spec, cur.date())
        if forward:
            for ws, we in windows:
                if cur < ws: return ws
                if ws <= cur < we: return cur
            cur = datetime.combine(cur.date() + timedelta(days=1), time(0, 0))
        else:
            for ws, we in reversed(windows):
                if cur > we: return we
                if ws < cur <= we: return cur
            cur = datetime.combine(cur.date() - timedelta(days=1), time(23, 59, 59))
    return dt


def add_working_hours(start, hours, spec=None):
    spec = spec or CalendarSpec.standard()
    if hours <= 0: return snap_to_working(start, spec, forward=True)
    cur = snap_to_working(start, spec, forward=True)
    remaining = hours * 3600.0; safety = 0
    while remaining > 1e-6 and safety < 365 * 4:
        safety += 1
        windows = _day_windows(spec, cur.date()); progressed = False
        for ws, we in windows:
            if ws <= cur < we:
                slot = (we - cur).total_seconds()
                if slot >= remaining:
                    return cur + timedelta(seconds=remaining)
                remaining -= slot; cur = we; progressed = True; continue
            if cur < ws:
                cur = ws; progressed = True; break
        if not progressed:
            cur = datetime.combine(cur.date() + timedelta(days=1), time(0, 0))
            cur = snap_to_working(cur, spec, forward=True)
    return cur


def subtract_working_hours(end, hours, spec=None):
    spec = spec or CalendarSpec.standard()
    if hours <= 0: return snap_to_working(end, spec, forward=False)
    cur = snap_to_working(end, spec, forward=False)
    remaining = hours * 3600.0; safety = 0
    while remaining > 1e-6 and safety < 365 * 4:
        safety += 1
        windows = _day_windows(spec, cur.date()); progressed = False
        for ws, we in reversed(windows):
            if ws < cur <= we:
                slot = (cur - ws).total_seconds()
                if slot >= remaining:
                    return cur - timedelta(seconds=remaining)
                remaining -= slot; cur = ws; progressed = True; continue
            if cur > we:
                cur = we; progressed = True; break
        if not progressed:
            cur = datetime.combine(cur.date() - timedelta(days=1), time(23, 59, 59))
            cur = snap_to_working(cur, spec, forward=False)
    return cur


def working_hours_between(start, end, spec=None):
    spec = spec or CalendarSpec.standard()
    if end <= start: return 0.0
    total = 0.0; cur = start.date()
    while cur <= end.date():
        total += _seconds_in_windows(start, end, _day_windows(spec, cur))
        cur += timedelta(days=1)
    return total / 3600.0
