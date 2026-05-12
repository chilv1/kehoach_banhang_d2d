"""Plan Generator — sinh hàng loạt Campaign DRAFT cho tháng.

Quy tắc:
- `prioridad` thấp = ưu tiên cao (1 trước 2).
- Vị trí có `fecha_alta_traffico` xác định ngày phù hợp:
    * WEEKDAY -> thứ 2-6
    * WEEKEND -> thứ 7, CN
    * MONDAY..SUNDAY -> đúng thứ đó
- Mỗi vị trí cần `cantidad_dia` lượt campaign trong tháng.
- Ưu tiên PR cùng BC; không vượt `cantidad_dia_trabajo`.
- Mỗi (PR, ngày) tối đa 1 ca; mỗi (vị trí, ngày) tối đa 1 ca.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

WEEKDAY_NAMES = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY",
                 "SATURDAY", "SUNDAY"]
WEEKDAY_SHORT = {0: "MONDAY", 1: "TUESDAY", 2: "WEDNESDAY",
                 3: "THURSDAY", 4: "FRIDAY", 5: "SATURDAY", 6: "SUNDAY"}


def _normalize_traffic(value) -> str:
    if value is None:
        return ""
    s = str(value).strip().upper()
    aliases = {
        "MON": "MONDAY", "TUE": "TUESDAY", "WED": "WEDNESDAY", "THU": "THURSDAY",
        "FRI": "FRIDAY", "SAT": "SATURDAY", "SUN": "SUNDAY",
    }
    return aliases.get(s, s)


def is_day_match(traffic: str, day: date) -> bool:
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
    leader: str | None
    capacity: int
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
    remaining: int


def generate_draft_campaigns(
    ubicaciones: pd.DataFrame,
    promoters: pd.DataFrame,
    year: int,
    month: int,
) -> tuple[list[dict], list[dict]]:
    """Sinh draft campaign cho tháng. Trả về (rows, warnings).

    Mỗi row là dict gọn để gọi `campaign.create_campaign`:
      {ubicacion_code, fecha, pr_code, bc, grupo, leader, notas, status='DRAFT'}
    """
    warnings: list[dict] = []
    rows: list[dict] = []

    if ubicaciones.empty:
        warnings.append({"tipo": "info", "code": "",
                         "mensaje": "Chưa có Ubicacion."})
        return rows, warnings

    ubic = ubicaciones[ubicaciones.get("activo", 1) == 1].copy()
    if not promoters.empty:
        prs = promoters[promoters.get("activo", 1) == 1].copy()
    else:
        prs = promoters

    pr_states: dict[str, PRState] = {
        r["pr_code"]: PRState(
            pr_code=r["pr_code"],
            bc=r["bc"],
            grupo=r.get("grupo") or "",
            leader=r.get("leader"),
            capacity=int(r.get("cantidad_dia_trabajo") or 0),
        )
        for _, r in prs.iterrows()
    }

    needs = [
        UbicNeed(
            code=r["code"], bc=r["bc"],
            prioridad=int(r.get("prioridad") or 1),
            traffic=r.get("fecha_alta_traffico") or "",
            remaining=max(int(r.get("cantidad_dia") or 1), 1),
        )
        for _, r in ubic.iterrows()
    ]
    needs.sort(key=lambda x: (x.prioridad, x.code))

    days = month_days(year, month)
    busy_ubic: dict[date, set[str]] = {d: set() for d in days}

    def _pick(day, bc=None):
        cands = [p for p in pr_states.values()
                 if p.can_take(day) and (bc is None or p.bc == bc)]
        if not cands:
            return None
        cands.sort(key=lambda p: -p.capacity)
        return cands[0]

    def _emit(need, day, pr, nota=""):
        rows.append({
            "ubicacion_code": need.code,
            "fecha": day.isoformat(),
            "pr_code": pr.pr_code if pr else None,
            "bc": need.bc,
            "grupo": pr.grupo if pr else "",
            "leader": pr.leader if pr else None,
            "notas": nota,
            "status": "DRAFT",
        })
        if pr:
            pr.assign(day)
        busy_ubic[day].add(need.code)
        need.remaining -= 1

    # Pass 1: cùng BC + đúng lịch traffic
    for need in needs:
        for day in days:
            if need.remaining <= 0:
                break
            if not is_day_match(need.traffic, day) or need.code in busy_ubic[day]:
                continue
            pr = _pick(day, bc=need.bc)
            if pr:
                _emit(need, day, pr)

    # Pass 2: khác BC + đúng lịch traffic
    for need in needs:
        if need.remaining <= 0:
            continue
        for day in days:
            if need.remaining <= 0:
                break
            if not is_day_match(need.traffic, day) or need.code in busy_ubic[day]:
                continue
            pr = _pick(day)
            if pr:
                _emit(need, day, pr, nota=f"PR khác BC ({pr.bc})")

    # Pass 3: cùng BC + ngoài lịch traffic
    for need in needs:
        if need.remaining <= 0:
            continue
        for day in days:
            if need.remaining <= 0:
                break
            if need.code in busy_ubic[day]:
                continue
            pr = _pick(day, bc=need.bc)
            if pr:
                _emit(need, day, pr, nota="Ngoài lịch traffic")

    # Pass 4: chưa có PR (slot trống) — vẫn tạo campaign DRAFT để team biết
    for need in needs:
        if need.remaining <= 0:
            continue
        for day in days:
            if need.remaining <= 0:
                break
            if not is_day_match(need.traffic, day) or need.code in busy_ubic[day]:
                continue
            _emit(need, day, None, nota="Chưa có PR — cần phân công thủ công")

    # Warnings
    for need in needs:
        if need.remaining > 0:
            warnings.append({
                "tipo": "warning", "code": need.code,
                "mensaje": f"Thiếu {need.remaining} ngày campaign cho {need.code} (BC {need.bc})",
            })
    for pr in pr_states.values():
        if pr.capacity > 0:
            warnings.append({
                "tipo": "info", "code": pr.pr_code,
                "mensaje": f"PR {pr.pr_code} còn dư {pr.capacity} ngày",
            })

    return rows, warnings
