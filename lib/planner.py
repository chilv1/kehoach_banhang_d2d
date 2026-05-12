"""Thuật toán sinh kế hoạch bán hàng theo ưu tiên + traffic + nguồn lực.

Quy tắc:
- `prioridad` thấp = ưu tiên cao (1 trước 2).
- Vị trí có `fecha_alta_traffico` xác định ngày phù hợp:
    * WEEKDAY -> thứ 2-6
    * WEEKEND -> thứ 7, CN
    * MONDAY..SUNDAY -> đúng thứ đó
    * '' / None -> bất kỳ ngày nào
- Mỗi vị trí cần `cantidad_dia` lượt campaign trong tháng.
- PR chỉ phục vụ vị trí cùng BC (Business Center).
- Mỗi PR không vượt `cantidad_dia_trabajo` lượt làm/tháng.
- Mỗi (PR, ngày) tối đa 1 ca; mỗi (vị trí, ngày) tối đa 1 ca.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable

import pandas as pd

WEEKDAY_NAMES = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY",
                 "SATURDAY", "SUNDAY"]
WEEKDAY_SHORT = {0: "MONDAY", 1: "TUESDAY", 2: "WEDNESDAY",
                 3: "THURSDAY", 4: "FRIDAY", 5: "SATURDAY", 6: "SUNDAY"}


def _normalize_traffic(value) -> str:
    if value is None:
        return ""
    s = str(value).strip().upper()
    # accept short forms
    aliases = {
        "MON": "MONDAY", "TUE": "TUESDAY", "WED": "WEDNESDAY", "THU": "THURSDAY",
        "FRI": "FRIDAY", "SAT": "SATURDAY", "SUN": "SUNDAY",
    }
    return aliases.get(s, s)


def is_day_match(traffic: str, day: date) -> bool:
    """Vị trí có lịch `traffic` có khớp với `day` không."""
    t = _normalize_traffic(traffic)
    weekday = WEEKDAY_SHORT[day.weekday()]
    if not t:
        return True
    if t == "WEEKDAY":
        return day.weekday() < 5
    if t == "WEEKEND":
        return day.weekday() >= 5
    if t in WEEKDAY_NAMES:
        return t == weekday
    return True


def month_days(year: int, month: int) -> list[date]:
    n = calendar.monthrange(year, month)[1]
    return [date(year, month, d) for d in range(1, n + 1)]


@dataclass
class PRState:
    pr_code: str
    bc: str
    grupo: str
    capacity: int  # số ngày còn lại
    busy_days: set[date] = field(default_factory=set)

    def can_take(self, day: date) -> bool:
        return self.capacity > 0 and day not in self.busy_days

    def assign(self, day: date) -> None:
        self.busy_days.add(day)
        self.capacity -= 1


@dataclass
class UbicNeed:
    code: str
    bc: str
    prioridad: int
    traffic: str
    remaining: int  # số lượt campaign còn cần


def generate_plan(
    ubicaciones: pd.DataFrame,
    promoters: pd.DataFrame,
    year: int,
    month: int,
) -> tuple[list[dict], list[dict]]:
    """Sinh lịch tháng. Trả về (rows_plan, warnings).

    rows_plan: list dict {fecha, ubicacion_code, pr_code, bc, grupo, notas}
    warnings: list dict {tipo, mensaje, code}
    """
    warnings: list[dict] = []
    plan_rows: list[dict] = []

    if ubicaciones.empty:
        warnings.append({"tipo": "info", "mensaje": "Chưa có Ubicacion nào.", "code": ""})
        return plan_rows, warnings

    # Filter active
    ubic = ubicaciones[ubicaciones.get("activo", 1) == 1].copy()
    prs = promoters[promoters.get("activo", 1) == 1].copy() if not promoters.empty else promoters

    # State
    pr_states: dict[str, PRState] = {}
    for _, r in prs.iterrows():
        pr_states[r["pr_code"]] = PRState(
            pr_code=r["pr_code"],
            bc=r["bc"],
            grupo=r.get("grupo") or "",
            capacity=int(r.get("cantidad_dia_trabajo") or 0),
        )

    needs: list[UbicNeed] = []
    for _, r in ubic.iterrows():
        needs.append(UbicNeed(
            code=r["code"],
            bc=r["bc"],
            prioridad=int(r.get("prioridad") or 1),
            traffic=r.get("fecha_alta_traffico") or "",
            remaining=max(int(r.get("cantidad_dia") or 1), 1),
        ))

    # Sort by priority ascending (1 first), then code
    needs.sort(key=lambda x: (x.prioridad, x.code))

    days = month_days(year, month)
    busy_ubic: dict[date, set[str]] = {d: set() for d in days}

    # Pass 1: chính (đúng ngày traffic + đúng BC)
    for need in needs:
        for day in days:
            if need.remaining <= 0:
                break
            if not is_day_match(need.traffic, day):
                continue
            if need.code in busy_ubic[day]:
                continue
            pr = _pick_pr(pr_states, day, need.bc)
            if pr is None:
                continue
            plan_rows.append({
                "fecha": day.isoformat(),
                "ubicacion_code": need.code,
                "pr_code": pr.pr_code,
                "bc": need.bc,
                "grupo": pr.grupo,
                "notas": "",
            })
            pr.assign(day)
            busy_ubic[day].add(need.code)
            need.remaining -= 1

    # Pass 2: linh hoạt (chấp nhận PR khác BC nếu vẫn thiếu)
    for need in needs:
        if need.remaining <= 0:
            continue
        for day in days:
            if need.remaining <= 0:
                break
            if not is_day_match(need.traffic, day):
                continue
            if need.code in busy_ubic[day]:
                continue
            pr = _pick_pr(pr_states, day, bc=None)
            if pr is None:
                continue
            plan_rows.append({
                "fecha": day.isoformat(),
                "ubicacion_code": need.code,
                "pr_code": pr.pr_code,
                "bc": need.bc,
                "grupo": pr.grupo,
                "notas": f"PR khác BC ({pr.bc})",
            })
            pr.assign(day)
            busy_ubic[day].add(need.code)
            need.remaining -= 1

    # Pass 3: chấp nhận ngày không khớp traffic (vẫn cần đáp ứng cantidad_dia)
    for need in needs:
        if need.remaining <= 0:
            continue
        for day in days:
            if need.remaining <= 0:
                break
            if need.code in busy_ubic[day]:
                continue
            pr = _pick_pr(pr_states, day, bc=need.bc)
            if pr is None:
                continue
            plan_rows.append({
                "fecha": day.isoformat(),
                "ubicacion_code": need.code,
                "pr_code": pr.pr_code,
                "bc": need.bc,
                "grupo": pr.grupo,
                "notas": "Ngoài lịch traffic",
            })
            pr.assign(day)
            busy_ubic[day].add(need.code)
            need.remaining -= 1

    # Pass 4: không có PR phù hợp -> giữ slot chưa gán
    for need in needs:
        if need.remaining <= 0:
            continue
        for day in days:
            if need.remaining <= 0:
                break
            if not is_day_match(need.traffic, day):
                continue
            if need.code in busy_ubic[day]:
                continue
            plan_rows.append({
                "fecha": day.isoformat(),
                "ubicacion_code": need.code,
                "pr_code": None,
                "bc": need.bc,
                "grupo": "",
                "notas": "Chưa có PR",
            })
            busy_ubic[day].add(need.code)
            need.remaining -= 1

    # Warnings
    for need in needs:
        if need.remaining > 0:
            warnings.append({
                "tipo": "warning",
                "code": need.code,
                "mensaje": f"Thiếu {need.remaining} ngày campaign cho {need.code} (BC {need.bc})",
            })
    for pr in pr_states.values():
        if pr.capacity > 0:
            warnings.append({
                "tipo": "info",
                "code": pr.pr_code,
                "mensaje": f"PR {pr.pr_code} còn dư {pr.capacity} ngày",
            })

    return plan_rows, warnings


def _pick_pr(
    pr_states: dict[str, PRState], day: date, bc: str | None
) -> PRState | None:
    """Chọn PR còn capacity, ưu tiên capacity cao (cân bằng tải)."""
    candidates = [
        p for p in pr_states.values()
        if p.can_take(day) and (bc is None or p.bc == bc)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda p: -p.capacity)
    return candidates[0]


def plan_summary(plan_df: pd.DataFrame) -> dict:
    if plan_df.empty:
        return {"total": 0, "assigned": 0, "unassigned": 0, "by_bc": {}}
    total = len(plan_df)
    assigned = int(plan_df["pr_code"].notna().sum())
    by_bc = plan_df.groupby("bc").size().to_dict()
    return {
        "total": total,
        "assigned": assigned,
        "unassigned": total - assigned,
        "by_bc": by_bc,
    }
