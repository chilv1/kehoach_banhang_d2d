"""Phase 1 — Quản lý outline / WBS / hierarchy.

Cung cấp:
  - indent(task_id)         : chuyển task thành con của sibling kế trước
  - outdent(task_id)        : nâng task lên 1 cấp
  - move(task_id, sort)     : đổi thứ tự
  - recompute_wbs(project)  : sinh lại WBS code (1, 1.1, 1.1.1, ...)
  - recompute_summary(project): tự bật is_summary cho task có con
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.task import Task


def _siblings_ordered(db: Session, project_id: int,
                       parent_id: int | None) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.project_id == project_id, Task.parent_id == parent_id)
        .order_by(Task.sort_order, Task.id)
        .all()
    )


def indent(db: Session, task_id: int) -> Task:
    t = db.get(Task, task_id)
    if not t:
        raise ValueError(f"Task {task_id} không tồn tại")
    sibs = _siblings_ordered(db, t.project_id, t.parent_id)
    idx = next((i for i, x in enumerate(sibs) if x.id == t.id), 0)
    if idx == 0:
        raise ValueError("Không có sibling phía trước để indent")
    new_parent = sibs[idx - 1]
    t.parent_id = new_parent.id
    t.outline_level = new_parent.outline_level + 1
    new_parent.is_summary = True
    db.commit()
    recompute_wbs(db, t.project_id)
    return t


def outdent(db: Session, task_id: int) -> Task:
    t = db.get(Task, task_id)
    if not t:
        raise ValueError(f"Task {task_id} không tồn tại")
    if t.parent_id is None:
        raise ValueError("Đã ở top level")
    parent = db.get(Task, t.parent_id)
    t.parent_id = parent.parent_id if parent else None
    t.outline_level = max(1, t.outline_level - 1)
    db.commit()
    recompute_summary(db, t.project_id)
    recompute_wbs(db, t.project_id)
    return t


def move(db: Session, task_id: int, new_sort_order: int) -> Task:
    t = db.get(Task, task_id)
    if not t:
        raise ValueError(f"Task {task_id} không tồn tại")
    t.sort_order = new_sort_order
    db.commit()
    recompute_wbs(db, t.project_id)
    return t


def recompute_summary(db: Session, project_id: int) -> None:
    """Đặt is_summary=True cho mọi task có ít nhất 1 con."""
    parents = {
        t.parent_id for t in db.query(Task).filter(
            Task.project_id == project_id, Task.parent_id.isnot(None)
        )
    }
    for t in db.query(Task).filter(Task.project_id == project_id):
        t.is_summary = t.id in parents
    db.commit()


def recompute_wbs(db: Session, project_id: int) -> None:
    """Sinh lại WBS code (1, 1.1, 1.1.1, ...) theo thứ tự sort_order."""
    def _assign(parent_id: int | None, prefix: str) -> None:
        kids = _siblings_ordered(db, project_id, parent_id)
        for i, k in enumerate(kids, start=1):
            k.wbs = f"{prefix}{i}" if not prefix else f"{prefix}.{i}"
            _assign(k.id, k.wbs)

    _assign(None, "")
    db.commit()
