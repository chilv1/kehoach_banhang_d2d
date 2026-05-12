"""Phase 3 — Tính chi phí (cost rollup).

assignment.cost = work_hours × resource.standard_rate + resource.cost_per_use
task.total_cost = fixed_cost + sum(assignment.cost) (cộng dồn cho summary)
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.resource import Resource, ResourceType
from app.models.task import Task


def compute_assignment_cost(a: Assignment, r: Resource) -> float:
    if r.type == ResourceType.WORK:
        return (a.work_hours or 0) * (r.standard_rate or 0) + (r.cost_per_use or 0)
    if r.type == ResourceType.MATERIAL:
        return (a.work_hours or 0) * (r.standard_rate or 0) + (r.cost_per_use or 0)
    if r.type == ResourceType.COST:
        return r.cost_per_use or 0
    return 0.0


def recompute_costs(db: Session, project_id: int) -> dict:
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    assigns = (
        db.query(Assignment)
        .filter(Assignment.task_id.in_([t.id for t in tasks]))
        .all()
    )
    res_by_id: dict[int, Resource] = {
        r.id: r for r in db.query(Resource).filter(Resource.project_id == project_id)
    }
    leaf_cost: dict[int, float] = {}
    for a in assigns:
        r = res_by_id.get(a.resource_id)
        if not r:
            continue
        a.cost = compute_assignment_cost(a, r)
        leaf_cost[a.task_id] = leaf_cost.get(a.task_id, 0.0) + a.cost
    leaf_total: dict[int, float] = {}
    for t in tasks:
        if t.is_summary:
            continue
        leaf_total[t.id] = (t.fixed_cost or 0) + leaf_cost.get(t.id, 0.0)
    summaries = sorted([t for t in tasks if t.is_summary], key=lambda t: -t.outline_level)
    by_parent: dict[int, list[Task]] = {}
    for t in tasks:
        if t.parent_id:
            by_parent.setdefault(t.parent_id, []).append(t)
    rolled: dict[int, float] = dict(leaf_total)
    for s in summaries:
        kids = by_parent.get(s.id, [])
        rolled[s.id] = (s.fixed_cost or 0) + sum(rolled.get(k.id, 0) for k in kids)
    for t in tasks:
        if t.actual_cost == 0.0:
            t.actual_cost = rolled.get(t.id, 0.0)
    db.commit()
    project_total = sum(rolled.get(t.id, 0) for t in tasks if t.parent_id is None)
    return {
        "project_total_cost": round(project_total, 2),
        "n_assignments": len(assigns),
        "n_tasks": len(tasks),
    }
