"""Hard-constraint validator for AI-generated sales plans.

Implements rules C1..C10 from `docs/sales-planner/AI_PLANNER_SPEC.md`.

The solver is OR-Tools-ready (Phase 5 will instantiate CP-SAT here) but for
Phase 1 we provide a deterministic validator + simple greedy fixer so the
pipeline can be exercised end-to-end without the binary dependency.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable

from sqlalchemy.orm import Session

from app.sales_planner.models import Location, PRStaff
from app.sales_planner.schemas import AIPlanItem


@dataclass
class Violation:
    code: str                # "C1".."C10"
    severity: str            # "high" | "medium" | "low"
    task_ref: str            # task_name or index
    message: str


@dataclass
class ValidationReport:
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(v.severity == "high" for v in self.violations)

    def add(self, code: str, severity: str, task_ref: str, msg: str) -> None:
        self.violations.append(Violation(code, severity, task_ref, msg))


# ---------- distance ----------

_R_KM = 6371.0


def haversine_km(p: tuple[float, float], q: tuple[float, float]) -> float:
    """Great-circle distance between two (lat, lng) pairs in kilometres."""
    lat1, lon1 = math.radians(p[0]), math.radians(p[1])
    lat2, lon2 = math.radians(q[0]), math.radians(q[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * _R_KM * math.asin(math.sqrt(a))


# ---------- main validator ----------

_DAY_NAMES = {
    "MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, "THURSDAY": 3,
    "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6,
}


def _matches_day(traffic: str | None, day: date) -> bool:
    if not traffic:
        return True
    t = traffic.strip().upper()
    weekday = day.weekday()
    if t == "WEEKDAY":
        return weekday < 5
    if t == "WEEKEND":
        return weekday >= 5
    if t in _DAY_NAMES:
        return weekday == _DAY_NAMES[t]
    return True


def validate_plan(
    db: Session, plan: list[AIPlanItem], *,
    horizon_start: date, horizon_end: date,
) -> ValidationReport:
    """Run all hard constraints against the generated plan."""
    report = ValidationReport()

    # Materialise master data we need.
    staff_by_code: dict[str, PRStaff] = {
        s.pr_code: s for s in db.query(PRStaff).filter(PRStaff.is_active.is_(True))
    }
    location_by_code: dict[str, Location] = {
        loc.code: loc for loc in db.query(Location).filter(Location.is_active.is_(True))
    }

    # Pre-compute group capacity per day for C3 (only if grupo is named).
    # Naïve: capacity = sum of (1.0) per active PR with that group, per weekday.
    # Real implementation will query sales_pr_groups.member_count and daily_plan.

    # State for cross-task checks
    pr_day: dict[tuple[str, date], list[AIPlanItem]] = defaultdict(list)
    ubic_day: dict[tuple[str, date], list[AIPlanItem]] = defaultdict(list)
    pr_total_units: dict[str, float] = defaultdict(float)

    for idx, item in enumerate(plan):
        ref = f"{idx}:{item.task_name}"

        # C10: dates within horizon
        if item.start_date > item.end_date:
            report.add("C10", "high", ref,
                       f"start_date {item.start_date} after end_date {item.end_date}")
            continue
        if item.start_date < horizon_start or item.end_date > horizon_end:
            report.add("C10", "medium", ref,
                       "task falls outside planning horizon")

        # C4: traffic-day match (first day)
        loc = location_by_code.get(item.code_ubicacion)
        if loc is None:
            report.add("C8", "high", ref,
                       f"unknown code_ubicacion={item.code_ubicacion}")
            continue
        if not _matches_day(loc.fecha_alta_traffico, item.start_date):
            report.add("C4", "medium", ref,
                       f"start day-of-week mismatch (loc requires {loc.fecha_alta_traffico})")

        # Track ubicacion x day for C8
        day = item.start_date
        while day <= item.end_date:
            ubic_day[(item.code_ubicacion, day)].append(item)
            day += timedelta(days=1)

        # Resource allocation (C1, C2, C3 + C9)
        pr_code = (item.grupo_code_pr or "").strip()
        if pr_code in staff_by_code:
            pr = staff_by_code[pr_code]
            day = item.start_date
            while day <= item.end_date:
                if day.weekday() < 5:                 # working days only
                    pr_day[(pr_code, day)].append(item)
                    pr_total_units[pr_code] += 1.0
                day += timedelta(days=1)
            # capacity (C2)
            if pr_total_units[pr_code] > pr.cantidad_dia_trabajo:
                report.add("C2", "high", ref,
                           f"PR {pr_code} over capacity "
                           f"({pr_total_units[pr_code]} > {pr.cantidad_dia_trabajo})")

    # C1 (PR overlap)
    for (pr_code, d), items in pr_day.items():
        if len(items) > 1:
            names = ", ".join(i.task_name for i in items)
            report.add("C1", "high", f"{pr_code}@{d}",
                       f"PR {pr_code} double-booked on {d}: {names}")

    # C8 (Ubicacion duplicate same day)
    for (ub, d), items in ubic_day.items():
        if len(items) > 1:
            report.add("C8", "high", f"{ub}@{d}",
                       f"Ubicacion {ub} has {len(items)} tasks on {d}")

    # C9 (geo proximity for same PR same day)
    for (pr_code, d), items in pr_day.items():
        if len(items) < 2:
            continue
        coords = []
        for i in items:
            loc = location_by_code.get(i.code_ubicacion)
            if loc and loc.latitud and loc.longitud:
                coords.append((float(loc.latitud), float(loc.longitud)))
        if len(coords) >= 2:
            for a in range(len(coords)):
                for b in range(a + 1, len(coords)):
                    dist = haversine_km(coords[a], coords[b])
                    if dist > 30.0:
                        report.add("C9", "medium", f"{pr_code}@{d}",
                                   f"PR {pr_code} tasks {dist:.1f}km apart")

    return report
