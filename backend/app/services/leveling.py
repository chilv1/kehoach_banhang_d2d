"""Phase 5 — Resource leveling.

Phát hiện và auto-delay các task để giải quyết over-allocation.

Thuật toán (greedy, priority-based):
  1. Tính daily load cho mỗi resource = Σ(assignment.units) cho các task chạy ngày đó.
  2. Nếu vượt resource.max_units → tìm ngày sớm nhất bị overallocated.
  3. Trên ngày đó, chọn task có priority THẤP nhất (slack lớn nhất tie-break).
  4. Đặt constraint SNET = next working day, reschedule.
  5. Lặp tới khi hết overallocation hoặc đạt max_iter.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.resource import Resource, ResourceType
from app.models.task import Task, TaskConstraint
from .scheduler import schedule_project
from .working_time import CalendarSpec


def _task_dates(t: Task) -> tuple[date, date] | None:
    if not t.start_date or not t.finish_date:
        return None
    return t.start_date.date(), t.finish_date.date()


def compute_daily_load(db: Session, project_id: int) -> dict:
    """Trả về { resource_id: { date: total_units } }."""
    tasks = (
        db.query(Task)
        .filter(Task.project_id == project_id, Task.is_summary == False)  # noqa: E712
        .all()
    )
    assigns = (
        db.query(Assignment)
        .filter(Assignment.task_id.in_([t.id for t in tasks]))
        .all()
    )
    by_task: dict[int, Task] = {t.id: t for t in tasks}

    load: dict[int, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for a in assigns:
        t = by_task.get(a.task_id)
        if not t:
            continue
        rng = _task_dates(t)
        if not rng:
            continue
        s, e = rng
        d = s
        while d <= e:
            if d.weekday() < 5:  # only weekdays (assume Standard cal)
                load[a.resource_id][d] += a.units or 0
            d += timedelta(days=1)
    return load


def find_overallocations(db: Session, project_id: int) -> list[dict]:
    """Trả về list { resource_id, date, used_units, max_units, over }."""
    load = compute_daily_load(db, project_id)
    resources = {
        r.id: r for r in db.query(Resource).filter(
            Resource.project_id == project_id,
            Resource.type == ResourceType.WORK,
        )
    }
    issues: list[dict] = []
    for rid, by_day in load.items():
        r = resources.get(rid)
        if not r:
            continue
        for d, used in by_day.items():
            if used > r.max_units + 1e-6:
                issues.append({
                    "resource_id": rid,
                    "resource_name": r.name,
                    "date": d.isoformat(),
                    "used_units": round(used, 2),
                    "max_units": r.max_units,
                    "over": round(used - r.max_units, 2),
                })
    return sorted(issues, key=lambda x: (x["date"], -x["over"]))


def level_resources(db: Session, project_id: int,
                     max_iterations: int = 50) -> dict:
    """Auto-delay các task để giải quyết overallocation."""
    delays: list[dict] = []
    iterations = 0

    while iterations < max_iterations:
        iterations += 1
        issues = find_overallocations(db, project_id)
        if not issues:
            break

        worst = issues[0]
        bad_day = date.fromisoformat(worst["date"])
        rid = worst["resource_id"]

        # Tasks chạy ngày này dùng resource rid
        assigns = (
            db.query(Assignment)
            .filter(Assignment.resource_id == rid)
            .all()
        )
        candidates: list[Task] = []
        for a in assigns:
            t = db.get(Task, a.task_id)
            if not t or t.is_summary:
                continue
            rng = _task_dates(t)
            if not rng:
                continue
            if rng[0] <= bad_day <= rng[1]:
                candidates.append(t)

        if not candidates:
            break

        # Sort: priority thấp trước → slack cao trước
        candidates.sort(key=lambda t: (t.priority, -t.total_slack_hours))
        victim = candidates[0]

        # Đẩy victim sang ngày làm việc kế tiếp
        next_day = bad_day + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)

        victim.constraint_type = TaskConstraint.SNET
        victim.constraint_date = datetime.combine(next_day, datetime.min.time()).replace(hour=8)
        db.commit()

        delays.append({
            "task_id": victim.id,
            "task_name": victim.name,
            "from_date": (victim.start_date.date().isoformat()
                          if victim.start_date else None),
            "new_constraint_date": victim.constraint_date.isoformat(),
            "reason": f"Overallocation of {worst['resource_name']} on {worst['date']}",
        })

        # Re-run scheduler
        try:
            schedule_project(db, project_id)
        except Exception:
            break

    final_issues = find_overallocations(db, project_id)
    return {
        "iterations": iterations,
        "delays": delays,
        "converged": len(final_issues) == 0,
        "remaining_overallocations": len(final_issues),
    }
