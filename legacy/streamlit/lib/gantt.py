"""Logic phụ trợ cho Project Gantt:
  - Build danh sách "task" từ campaign (mỗi Ubicacion = 1 task)
  - Detect conflict: PR overlap, PR over capacity, slot trống, ngoài lịch traffic
"""
from __future__ import annotations

import pandas as pd

from .planner import is_day_match


def build_tasks(camps: pd.DataFrame, ubic: pd.DataFrame) -> pd.DataFrame:
    """Mỗi Ubicacion trong campaign tháng này = 1 task.

    Trả về DataFrame với:
      ubicacion_code, bc, distrito, prioridad, task_start, task_end,
      duration_days, total_camps, done_camps, running_camps,
      cancelled_camps, draft_camps, planned_camps, progress_pct,
      resources, n_resources
    """
    if camps.empty:
        return pd.DataFrame()

    df = camps.copy()
    df["fecha_dt"] = pd.to_datetime(df["fecha"])

    def _agg(g: pd.DataFrame) -> pd.Series:
        return pd.Series({
            "task_start": g["fecha_dt"].min(),
            "task_end": g["fecha_dt"].max(),
            "total_camps": len(g),
            "done_camps": int((g["status"] == "DONE").sum()),
            "running_camps": int((g["status"] == "RUNNING").sum()),
            "cancelled_camps": int((g["status"] == "CANCELLED").sum()),
            "draft_camps": int((g["status"] == "DRAFT").sum()),
            "planned_camps": int((g["status"] == "PLANNED").sum()),
            "bc": g["bc"].iloc[0],
            "distrito": g.get("distrito", pd.Series([""])).iloc[0] if "distrito" in g else "",
            "prioridad": int(g["prioridad"].iloc[0]) if "prioridad" in g.columns else 1,
            "resources": ", ".join(sorted(g["pr_code"].dropna().unique())) or "—",
            "n_resources": g["pr_code"].dropna().nunique(),
        })

    tasks = df.groupby("ubicacion_code").apply(_agg, include_groups=False).reset_index()
    tasks["duration_days"] = (tasks["task_end"] - tasks["task_start"]).dt.days + 1
    completed = tasks["done_camps"] + tasks["cancelled_camps"]
    tasks["progress_pct"] = (completed / tasks["total_camps"] * 100).round(0)
    return tasks.sort_values(["bc", "prioridad", "ubicacion_code"])


def detect_conflicts(camps: pd.DataFrame, prs: pd.DataFrame,
                      ubic: pd.DataFrame) -> pd.DataFrame:
    """Phát hiện xung đột:
      - PR overlap: cùng PR có 2+ campaign cùng ngày
      - PR over capacity: tổng ngày làm > cantidad_dia_trabajo
      - Ubicacion overlap: cùng vị trí 2+ campaign cùng ngày
      - Chưa có PR: campaign chưa được phân
      - Ngoài lịch traffic: ngày không khớp Fecha Alta Traffico
    """
    out: list[dict] = []
    if camps.empty:
        return pd.DataFrame(out)

    # 1) PR overlap
    have_pr = camps.dropna(subset=["pr_code"])
    pr_day = have_pr.groupby(["pr_code", "fecha"]).size().reset_index(name="n")
    for _, r in pr_day[pr_day["n"] > 1].iterrows():
        codes = ", ".join(
            have_pr[(have_pr["pr_code"] == r["pr_code"])
                    & (have_pr["fecha"] == r["fecha"])]["ubicacion_code"]
        )
        out.append({
            "severity": "🔴 HIGH",
            "tipo": "PR overlap",
            "fecha": r["fecha"],
            "subject": r["pr_code"],
            "detail": f"{r['pr_code']} có {r['n']} campaign cùng ngày tại {codes}",
        })

    # 2) Ubicacion overlap (về lý thuyết DB unique nhưng vẫn check)
    ub_day = camps.groupby(["ubicacion_code", "fecha"]).size().reset_index(name="n")
    for _, r in ub_day[ub_day["n"] > 1].iterrows():
        out.append({
            "severity": "🔴 HIGH",
            "tipo": "Vị trí trùng",
            "fecha": r["fecha"],
            "subject": r["ubicacion_code"],
            "detail": f"{r['ubicacion_code']} có {r['n']} campaign cùng ngày",
        })

    # 3) PR over capacity
    if not prs.empty:
        load = have_pr.groupby("pr_code").size().reset_index(name="days_planned")
        load = load.merge(
            prs[["pr_code", "cantidad_dia_trabajo"]], on="pr_code", how="left"
        )
        load["cantidad_dia_trabajo"] = load["cantidad_dia_trabajo"].fillna(0)
        load["over"] = load["days_planned"] - load["cantidad_dia_trabajo"]
        for _, r in load[load["over"] > 0].iterrows():
            out.append({
                "severity": "🟠 MED",
                "tipo": "Vượt capacity",
                "fecha": "",
                "subject": r["pr_code"],
                "detail": f"{r['pr_code']}: {int(r['days_planned'])} ca > "
                          f"capacity {int(r['cantidad_dia_trabajo'])} (vượt {int(r['over'])})",
            })

    # 4) Chưa có PR
    no_pr = camps[camps["pr_code"].isna()]
    for _, r in no_pr.iterrows():
        out.append({
            "severity": "🟡 LOW",
            "tipo": "Chưa phân PR",
            "fecha": r["fecha"],
            "subject": r["ubicacion_code"],
            "detail": f"{r['codigo']} chưa có PR",
        })

    # 5) Ngoài lịch traffic
    if not ubic.empty:
        traffic_map = ubic.set_index("code")["fecha_alta_traffico"].to_dict()
        for _, c in camps.iterrows():
            traffic = traffic_map.get(c["ubicacion_code"], "")
            if not traffic:
                continue
            day = pd.to_datetime(c["fecha"]).date()
            if not is_day_match(traffic, day):
                out.append({
                    "severity": "🟡 LOW",
                    "tipo": "Ngoài lịch traffic",
                    "fecha": c["fecha"],
                    "subject": c["ubicacion_code"],
                    "detail": f"{c['codigo']}: lịch yêu cầu {traffic}, "
                              f"nhưng xếp ngày {c['fecha']} ({_weekday(day)})",
                })

    return pd.DataFrame(out)


def _weekday(d) -> str:
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d.weekday()]


def resource_load(camps: pd.DataFrame, prs: pd.DataFrame) -> pd.DataFrame:
    """Tải nguồn lực: cho mỗi PR, số ca / capacity / utilization%."""
    if camps.empty:
        return pd.DataFrame()
    load = camps.dropna(subset=["pr_code"]).groupby("pr_code").agg(
        days_planned=("id", "count"),
        bc=("bc", "first"),
    ).reset_index()
    if not prs.empty:
        load = load.merge(
            prs[["pr_code", "grupo", "cantidad_dia_trabajo", "tipo"]],
            on="pr_code", how="left"
        )
        load["utilization_pct"] = (
            load["days_planned"] / load["cantidad_dia_trabajo"].replace(0, 1) * 100
        ).round(1)
        load["over"] = load["days_planned"] > load["cantidad_dia_trabajo"]
    return load.sort_values("utilization_pct", ascending=False)
