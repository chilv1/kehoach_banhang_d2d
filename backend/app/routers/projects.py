"""Routers cho Projects + tasks + dependencies + resources + assignments + baselines."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.baseline import Baseline, BaselineTask
from app.models.dependency import TaskDependency
from app.models.project import Project
from app.models.resource import Resource
from app.models.task import Task
from app.schemas.common import (
    AssignmentCreate, AssignmentOut, AssignmentUpdate,
    BaselineCreate, BaselineOut,
    DependencyCreate, DependencyOut, DependencyUpdate,
    ProjectCreate, ProjectOut, ProjectUpdate,
    ResourceCreate, ResourceOut, ResourceUpdate,
    ScheduleResult,
    TaskCreate, TaskOut, TaskUpdate,
)
from app.services.scheduler import schedule_project, SchedulingError

router = APIRouter()


# ============ Projects ============
@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    obj = Project(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id).all()


@router.get("/projects/{pid}", response_model=ProjectOut)
def get_project(pid: int, db: Session = Depends(get_db)):
    p = db.get(Project, pid)
    if not p:
        raise HTTPException(404, "Project not found")
    return p


@router.patch("/projects/{pid}", response_model=ProjectOut)
def update_project(pid: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    p = db.get(Project, pid)
    if not p:
        raise HTTPException(404, "Project not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/projects/{pid}", status_code=204)
def delete_project(pid: int, db: Session = Depends(get_db)):
    p = db.get(Project, pid)
    if not p:
        raise HTTPException(404, "Project not found")
    db.delete(p)
    db.commit()


@router.post("/projects/{pid}/schedule", response_model=ScheduleResult)
def run_schedule(pid: int, db: Session = Depends(get_db)):
    """Chạy CPM forward/backward pass + critical path."""
    try:
        res = schedule_project(db, pid)
    except SchedulingError as e:
        raise HTTPException(400, str(e))
    return ScheduleResult(**res)


# ============ Tasks ============
@router.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    obj = Task(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/projects/{pid}/tasks", response_model=list[TaskOut])
def list_tasks(pid: int, db: Session = Depends(get_db)):
    return (
        db.query(Task)
        .filter(Task.project_id == pid)
        .order_by(Task.sort_order, Task.id)
        .all()
    )


@router.get("/tasks/{tid}", response_model=TaskOut)
def get_task(tid: int, db: Session = Depends(get_db)):
    t = db.get(Task, tid)
    if not t:
        raise HTTPException(404, "Task not found")
    return t


@router.patch("/tasks/{tid}", response_model=TaskOut)
def update_task(tid: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    t = db.get(Task, tid)
    if not t:
        raise HTTPException(404, "Task not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/tasks/{tid}", status_code=204)
def delete_task(tid: int, db: Session = Depends(get_db)):
    t = db.get(Task, tid)
    if not t:
        raise HTTPException(404, "Task not found")
    db.delete(t)
    db.commit()


# ============ Dependencies ============
@router.post("/dependencies", response_model=DependencyOut, status_code=201)
def create_dependency(payload: DependencyCreate, db: Session = Depends(get_db)):
    pred = db.get(Task, payload.predecessor_id)
    succ = db.get(Task, payload.successor_id)
    if not pred or not succ:
        raise HTTPException(404, "Task not found")
    if pred.project_id != succ.project_id:
        raise HTTPException(400, "Predecessor and successor must be in same project")
    if pred.id == succ.id:
        raise HTTPException(400, "Task cannot depend on itself")
    obj = TaskDependency(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/projects/{pid}/dependencies", response_model=list[DependencyOut])
def list_dependencies(pid: int, db: Session = Depends(get_db)):
    task_ids = [t.id for t in db.query(Task).filter(Task.project_id == pid)]
    return (
        db.query(TaskDependency)
        .filter(TaskDependency.predecessor_id.in_(task_ids))
        .all()
    )


@router.patch("/dependencies/{did}", response_model=DependencyOut)
def update_dependency(did: int, payload: DependencyUpdate,
                       db: Session = Depends(get_db)):
    d = db.get(TaskDependency, did)
    if not d:
        raise HTTPException(404, "Dependency not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/dependencies/{did}", status_code=204)
def delete_dependency(did: int, db: Session = Depends(get_db)):
    d = db.get(TaskDependency, did)
    if not d:
        raise HTTPException(404, "Dependency not found")
    db.delete(d)
    db.commit()


# ============ Resources ============
@router.post("/resources", response_model=ResourceOut, status_code=201)
def create_resource(payload: ResourceCreate, db: Session = Depends(get_db)):
    obj = Resource(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/projects/{pid}/resources", response_model=list[ResourceOut])
def list_resources(pid: int, db: Session = Depends(get_db)):
    return db.query(Resource).filter(Resource.project_id == pid).all()


@router.patch("/resources/{rid}", response_model=ResourceOut)
def update_resource(rid: int, payload: ResourceUpdate,
                     db: Session = Depends(get_db)):
    r = db.get(Resource, rid)
    if not r:
        raise HTTPException(404, "Resource not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/resources/{rid}", status_code=204)
def delete_resource(rid: int, db: Session = Depends(get_db)):
    r = db.get(Resource, rid)
    if not r:
        raise HTTPException(404, "Resource not found")
    db.delete(r)
    db.commit()


# ============ Assignments ============
@router.post("/assignments", response_model=AssignmentOut, status_code=201)
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db)):
    obj = Assignment(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/tasks/{tid}/assignments", response_model=list[AssignmentOut])
def list_task_assignments(tid: int, db: Session = Depends(get_db)):
    return db.query(Assignment).filter(Assignment.task_id == tid).all()


@router.patch("/assignments/{aid}", response_model=AssignmentOut)
def update_assignment(aid: int, payload: AssignmentUpdate,
                       db: Session = Depends(get_db)):
    a = db.get(Assignment, aid)
    if not a:
        raise HTTPException(404, "Assignment not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/assignments/{aid}", status_code=204)
def delete_assignment(aid: int, db: Session = Depends(get_db)):
    a = db.get(Assignment, aid)
    if not a:
        raise HTTPException(404, "Assignment not found")
    db.delete(a)
    db.commit()


# ============ Baselines ============
@router.post("/baselines", response_model=BaselineOut, status_code=201)
def create_baseline(payload: BaselineCreate, db: Session = Depends(get_db)):
    """Snapshot toàn bộ task của project vào baseline."""
    # delete cũ nếu trùng (project, number)
    existing = (
        db.query(Baseline)
        .filter(Baseline.project_id == payload.project_id,
                Baseline.number == payload.number)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()

    obj = Baseline(
        project_id=payload.project_id,
        number=payload.number,
        name=payload.name or f"Baseline {payload.number}",
    )
    db.add(obj)
    db.flush()

    # snapshot tasks
    tasks = db.query(Task).filter(Task.project_id == payload.project_id).all()
    for t in tasks:
        snap = BaselineTask(
            baseline_id=obj.id,
            task_id=t.id,
            baseline_start=t.start_date,
            baseline_finish=t.finish_date,
            baseline_duration_hours=t.duration_hours,
            baseline_work_hours=t.actual_work_hours,
            baseline_cost=t.fixed_cost,
        )
        db.add(snap)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/projects/{pid}/baselines", response_model=list[BaselineOut])
def list_baselines(pid: int, db: Session = Depends(get_db)):
    return db.query(Baseline).filter(Baseline.project_id == pid).all()


@router.delete("/baselines/{bid}", status_code=204)
def delete_baseline(bid: int, db: Session = Depends(get_db)):
    b = db.get(Baseline, bid)
    if not b:
        raise HTTPException(404, "Baseline not found")
    db.delete(b)
    db.commit()
