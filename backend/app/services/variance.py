"""Phase 4 — So sánh baseline vs current (tracking)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session
from app.models.baseline import Baseline, BaselineTask
from app.models.task import Task
from .working_time import CalendarSpec, working_hours_between


def task_variance(t: Task, b: BaselineTask | None, cal: CalendarSpec | None = None) -> dict:
    cal = cal or CalendarSpec.standard()
    out = {
        "task_id": t.id, "name": t.name,
        "current_start": t.start_date.isoformat() if t.start_date else None,
        "current_finish": t.finish_date.isoformat() if t.finish_date else None,
        "baseline_start": None, "baseline_finish": None,
        "start_variance_hours": None, "finish_variance_hours": None,
        "duration_variance_hours": None, "cost_variance": None,
        "work_variance_hours": None, "is_slipping": False,
    }
    if not b: return out
    out["baseline_start"] = b.baseline_start.isoformat() if b.baseline_start else None
    out["baseline_finish"] = b.baseline_finish.isoformat() if b.baseline_finish else None
    def _signed(a, base):
        if a is None or base is None: return None
        diff_h = working_hours_between(min(a, base), max(a, base), cal)
        return diff_h if a >= base else -diff_h
    out["start_variance_hours"] = _signed(t.start_date, b.baseline_start)
    out["finish_variance_hours"] = _signed(t.finish_date, b.baseline_finish)
    out["duration_variance_hours"] = (t.duration_hours or 0) - (b.baseline_duration_hours or 0)
    out["cost_variance"] = (t.actual_cost or 0) - (b.baseline_cost or 0)
    out["work_variance_hours"] = (t.actual_work_hours or 0) - (b.baseline_work_hours or 0)
    out["is_slipping"] = bool(out["finish_variance_hours"] and out["finish_variance_hours"] > 0)
    return out


def project_variance(db: Session, project_id: int, baseline_number: int = 0) -> list[dict]:
    b = db.query(Baseline).filter(Baseline.project_id == project_id,
                                    Baseline.number == baseline_number).first()
    if not b: return []
    bts = {x.task_id: x for x in b.task_snapshots}
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    return [task_variance(t, bts.get(t.id)) for t in tasks]
