"""CPM Scheduling Engine — forward/backward pass đầy đủ.

Hỗ trợ:
- 4 link type: FS / SS / FF / SF
- Lag/Lead (lag_hours dương = delay, âm = lead/overlap)
- 8 constraint type: ASAP, ALAP, MSO, MFO, SNET, SNLT, FNET, FNLT
- Calendar-aware (giờ làm việc)
- Cycle detection
- Critical path
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.task import Task, TaskConstraint
from app.models.dependency import TaskDependency, LinkType
from app.models.project import Project
from .working_time import (
    CalendarSpec, add_working_hours, subtract_working_hours,
    snap_to_working, working_hours_between,
)


class SchedulingError(Exception):
    pass


@dataclass(eq=False)
class _Node:
    task: Task
    duration_h: float
    preds: list[tuple["_Node", LinkType, float]] = field(default_factory=list)
    succs: list[tuple["_Node", LinkType, float]] = field(default_factory=list)
    # Tính toán
    es: datetime | None = None
    ef: datetime | None = None
    ls: datetime | None = None
    lf: datetime | None = None


def topo_sort(nodes: list[_Node]) -> list[_Node]:
    """Topological sort. Raise SchedulingError nếu có cycle."""
    in_deg = {n: len(n.preds) for n in nodes}
    queue = [n for n in nodes if in_deg[n] == 0]
    order: list[_Node] = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for s, _, _ in n.succs:
            in_deg[s] -= 1
            if in_deg[s] == 0:
                queue.append(s)
    if len(order) != len(nodes):
        cycled = [n.task.name for n in nodes if in_deg[n] > 0]
        raise SchedulingError(
            f"Phát hiện vòng lặp (cycle) trong dependency: {cycled}"
        )
    return order


def _earliest_start_from_pred(pred: _Node, link: LinkType,
                                lag_h: float, dur_h: float,
                                cal: CalendarSpec) -> datetime:
    """Theo link_type, tính early_start tối thiểu của successor."""
    if link == LinkType.FS:
        base = pred.ef
        return add_working_hours(base, lag_h, cal) if lag_h >= 0 else \
            subtract_working_hours(base, -lag_h, cal)
    if link == LinkType.SS:
        base = pred.es
        return add_working_hours(base, lag_h, cal) if lag_h >= 0 else \
            subtract_working_hours(base, -lag_h, cal)
    if link == LinkType.FF:
        # succ.EF >= pred.EF + lag → succ.ES = succ.EF - dur
        target_ef = add_working_hours(pred.ef, lag_h, cal) if lag_h >= 0 else \
            subtract_working_hours(pred.ef, -lag_h, cal)
        return subtract_working_hours(target_ef, dur_h, cal)
    if link == LinkType.SF:
        # succ.EF >= pred.ES + lag
        target_ef = add_working_hours(pred.es, lag_h, cal) if lag_h >= 0 else \
            subtract_working_hours(pred.es, -lag_h, cal)
        return subtract_working_hours(target_ef, dur_h, cal)
    raise ValueError(f"Link type không hỗ trợ: {link}")


def _latest_finish_from_succ(succ: _Node, link: LinkType,
                              lag_h: float, dur_h: float,
                              cal: CalendarSpec) -> datetime:
    """Theo link_type, tính late_finish tối đa của predecessor."""
    if link == LinkType.FS:
        # pred.EF + lag <= succ.LS → pred.LF = succ.LS - lag
        base = succ.ls
        return subtract_working_hours(base, lag_h, cal) if lag_h >= 0 else \
            add_working_hours(base, -lag_h, cal)
    if link == LinkType.SS:
        # pred.ES + lag <= succ.LS → pred.LS = succ.LS - lag → pred.LF = LS + dur
        target_ls = subtract_working_hours(succ.ls, lag_h, cal) if lag_h >= 0 else \
            add_working_hours(succ.ls, -lag_h, cal)
        return add_working_hours(target_ls, dur_h, cal)
    if link == LinkType.FF:
        return subtract_working_hours(succ.lf, lag_h, cal) if lag_h >= 0 else \
            add_working_hours(succ.lf, -lag_h, cal)
    if link == LinkType.SF:
        # pred.ES + lag <= succ.LF → pred.LF = (succ.LF - lag) + dur
        target_ls = subtract_working_hours(succ.lf, lag_h, cal) if lag_h >= 0 else \
            add_working_hours(succ.lf, -lag_h, cal)
        return add_working_hours(target_ls, dur_h, cal)
    raise ValueError(f"Link type không hỗ trợ: {link}")


def _apply_constraint_to_es(node: _Node, es: datetime,
                              cal: CalendarSpec) -> datetime:
    """Điều chỉnh ES theo constraint (forward pass)."""
    t = node.task
    cd = t.constraint_date
    ct = t.constraint_type
    if ct == TaskConstraint.MSO and cd:
        return cd
    if ct == TaskConstraint.MFO and cd:
        return subtract_working_hours(cd, node.duration_h, cal)
    if ct == TaskConstraint.SNET and cd and es < cd:
        return cd
    if ct == TaskConstraint.SNLT and cd and es > cd:
        return cd
    if ct == TaskConstraint.FNET and cd:
        proposed_ef = add_working_hours(es, node.duration_h, cal)
        if proposed_ef < cd:
            return subtract_working_hours(cd, node.duration_h, cal)
    if ct == TaskConstraint.FNLT and cd:
        proposed_ef = add_working_hours(es, node.duration_h, cal)
        if proposed_ef > cd:
            return subtract_working_hours(cd, node.duration_h, cal)
    return es


def _apply_constraint_to_lf(node: _Node, lf: datetime,
                              cal: CalendarSpec) -> datetime:
    """Điều chỉnh LF theo constraint (backward pass)."""
    t = node.task
    cd = t.constraint_date
    ct = t.constraint_type
    if ct == TaskConstraint.MSO and cd:
        # LS phải = cd → LF = cd + duration
        return add_working_hours(cd, node.duration_h, cal)
    if ct == TaskConstraint.MFO and cd:
        return cd
    if ct == TaskConstraint.ALAP:
        # ALAP cố định LF ở mức late finish hiện tại — không can thiệp
        return lf
    if ct == TaskConstraint.FNLT and cd and lf > cd:
        return cd
    if ct == TaskConstraint.FNET and cd and lf < cd:
        return cd
    return lf


def schedule_project(db: Session, project_id: int) -> dict:
    """Chạy CPM cho 1 project. Cập nhật trực tiếp vào DB.

    Trả về dict thống kê: {n_tasks, n_critical, project_finish, ...}
    """
    project = db.get(Project, project_id)
    if not project:
        raise SchedulingError(f"Project {project_id} không tồn tại")

    tasks: list[Task] = (
        db.query(Task).filter(Task.project_id == project_id).all()
    )
    # Loại bỏ summary tasks khỏi CPM (sẽ tính rollup riêng)
    leaf_tasks = [t for t in tasks if not t.is_summary]
    if not leaf_tasks:
        return {"n_tasks": 0, "n_critical": 0, "project_finish": None}

    deps: list[TaskDependency] = (
        db.query(TaskDependency)
        .filter(TaskDependency.predecessor_id.in_([t.id for t in leaf_tasks]))
        .all()
    )

    cal = CalendarSpec.standard()
    project_start = project.start_date

    nodes_by_id: dict[int, _Node] = {
        t.id: _Node(
            task=t,
            duration_h=max(t.duration_hours or 0.0, 0.0),
        )
        for t in leaf_tasks
    }
    for d in deps:
        p = nodes_by_id.get(d.predecessor_id)
        s = nodes_by_id.get(d.successor_id)
        if not p or not s:
            continue
        p.succs.append((s, d.link_type, d.lag_hours or 0.0))
        s.preds.append((p, d.link_type, d.lag_hours or 0.0))

    nodes = list(nodes_by_id.values())
    order = topo_sort(nodes)

    # ============ FORWARD PASS ============
    for n in order:
        if not n.preds:
            es = project_start
        else:
            candidates = [
                _earliest_start_from_pred(p, lt, lag, n.duration_h, cal)
                for (p, lt, lag) in n.preds
            ]
            es = max(candidates)
        # snap to working time và áp constraint
        es = snap_to_working(es, cal, forward=True)
        es = _apply_constraint_to_es(n, es, cal)
        es = snap_to_working(es, cal, forward=True)
        if n.task.is_milestone:
            n.es = es
            n.ef = es
        else:
            n.es = es
            n.ef = add_working_hours(es, n.duration_h, cal)

    project_finish = max(n.ef for n in nodes)

    # ============ BACKWARD PASS ============
    for n in reversed(order):
        if not n.succs:
            lf = project_finish
        else:
            candidates = [
                _latest_finish_from_succ(s, lt, lag, n.duration_h, cal)
                for (s, lt, lag) in n.succs
            ]
            lf = min(candidates)
        lf = _apply_constraint_to_lf(n, lf, cal)
        n.lf = lf
        if n.task.is_milestone:
            n.ls = lf
        else:
            n.ls = subtract_working_hours(lf, n.duration_h, cal)

    # ============ SLACK + CRITICAL ============
    n_critical = 0
    for n in nodes:
        t = n.task
        t.early_start = n.es
        t.early_finish = n.ef
        t.late_start = n.ls
        t.late_finish = n.lf
        t.start_date = n.es
        t.finish_date = n.ef
        # total slack (giờ làm việc)
        slack_h = working_hours_between(n.es, n.ls, cal)
        if n.ls < n.es:
            slack_h = -working_hours_between(n.ls, n.es, cal)
        t.total_slack_hours = slack_h
        # free slack: min ES của các successor - EF
        if n.succs:
            min_succ_es = min(s.es for s, _, _ in n.succs)
            free = working_hours_between(n.ef, min_succ_es, cal)
            if min_succ_es < n.ef:
                free = -working_hours_between(min_succ_es, n.ef, cal)
            t.free_slack_hours = free
        else:
            t.free_slack_hours = slack_h
        t.is_critical = slack_h <= 0.5  # cho phép ngưỡng 0.5h
        if t.is_critical:
            n_critical += 1

    # ============ ROLLUP SUMMARY TASKS ============
    _rollup_summary(db, tasks, leaf_tasks)

    project.finish_date = project_finish
    db.commit()

    return {
        "n_tasks": len(leaf_tasks),
        "n_critical": n_critical,
        "project_finish": project_finish.isoformat(),
        "project_start": project_start.isoformat(),
    }


def _rollup_summary(db: Session, all_tasks: list[Task],
                     leaf_tasks: list[Task]) -> None:
    """Cập nhật start/finish của summary tasks từ children."""
    by_parent: dict[int, list[Task]] = {}
    for t in all_tasks:
        if t.parent_id:
            by_parent.setdefault(t.parent_id, []).append(t)

    summary_tasks = [t for t in all_tasks if t.is_summary]
    # process theo outline_level desc (sâu trước)
    summary_tasks.sort(key=lambda t: -t.outline_level)

    for sum_t in summary_tasks:
        children = by_parent.get(sum_t.id, [])
        if not children:
            continue
        starts = [c.start_date for c in children if c.start_date]
        finishes = [c.finish_date for c in children if c.finish_date]
        if starts:
            sum_t.start_date = min(starts)
            sum_t.early_start = sum_t.start_date
        if finishes:
            sum_t.finish_date = max(finishes)
            sum_t.early_finish = sum_t.finish_date
        # progress weighted
        total_dur = sum(c.duration_hours for c in children)
        if total_dur > 0:
            sum_t.percent_complete = sum(
                c.duration_hours * c.percent_complete for c in children
            ) / total_dur
