"""Phase 6 — Earned Value Management."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.project import Project
from app.models.resource import Resource
from app.models.task import Task
from .working_time import CalendarSpec, working_hours_between


def _task_planned_cost(t, assigns, res_map):
    total = t.fixed_cost or 0.0
    for a in assigns:
        if a.task_id != t.id: continue
        r = res_map.get(a.resource_id)
        if not r: continue
        total += (a.work_hours or 0) * (r.standard_rate or 0) + (r.cost_per_use or 0)
    return total


def compute_evm(db: Session, project_id: int, status_date: datetime | None = None) -> dict:
    project = db.get(Project, project_id)
    if not project: raise ValueError(f"Project {project_id}")
    sd = status_date or project.status_date or datetime.utcnow()
    cal = CalendarSpec.standard()
    tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_summary == False).all()
    assigns = db.query(Assignment).filter(Assignment.task_id.in_([t.id for t in tasks])).all()
    res_map = {r.id: r for r in db.query(Resource).filter(Resource.project_id == project_id)}
    bcws = bcwp = acwp = bac = 0.0
    task_rows = []
    for t in tasks:
        planned = _task_planned_cost(t, assigns, res_map)
        bac += planned
        if not t.start_date or not t.finish_date:
            task_rows.append({"task_id": t.id, "name": t.name, "planned_cost": round(planned, 2),
                              "bcws": 0, "bcwp": 0, "acwp": 0, "percent_complete": t.percent_complete})
            continue
        if sd >= t.finish_date: scheduled_frac = 1.0
        elif sd <= t.start_date: scheduled_frac = 0.0
        else:
            full = working_hours_between(t.start_date, t.finish_date, cal)
            done = working_hours_between(t.start_date, sd, cal)
            scheduled_frac = (done / full) if full > 0 else 0.0
        t_bcws = planned * scheduled_frac
        t_bcwp = planned * (t.percent_complete or 0) / 100.0
        t_acwp = t.actual_cost or 0.0
        bcws += t_bcws; bcwp += t_bcwp; acwp += t_acwp
        task_rows.append({"task_id": t.id, "name": t.name,
                          "planned_cost": round(planned, 2),
                          "bcws": round(t_bcws, 2), "bcwp": round(t_bcwp, 2),
                          "acwp": round(t_acwp, 2),
                          "percent_complete": t.percent_complete})
    cv = bcwp - acwp; sv = bcwp - bcws
    cpi = (bcwp / acwp) if acwp > 0 else None
    spi = (bcwp / bcws) if bcws > 0 else None
    eac = (bac / cpi) if cpi and cpi > 0 else None
    etc = (eac - acwp) if eac is not None else None
    vac = (bac - eac) if eac is not None else None
    tcpi = ((bac - bcwp) / (bac - acwp)) if (bac - acwp) > 0 else None
    return {"status_date": sd.isoformat(),
            "bcws": round(bcws, 2), "bcwp": round(bcwp, 2), "acwp": round(acwp, 2), "bac": round(bac, 2),
            "cv": round(cv, 2), "sv": round(sv, 2),
            "cpi": round(cpi, 3) if cpi else None, "spi": round(spi, 3) if spi else None,
            "eac": round(eac, 2) if eac else None, "etc": round(etc, 2) if etc else None,
            "vac": round(vac, 2) if vac else None, "tcpi": round(tcpi, 3) if tcpi else None,
            "tasks": task_rows}
