"""CRUD endpoints for sales planner core entities."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.sales_planner.models import (
    Branch, BusinessCenter, CampaignTask, Location, PRGroup, PRStaff,
    SalesCampaign,
)
from app.sales_planner.schemas import (
    BranchOut, BusinessCenterOut, CampaignOut, LocationOut, PRGroupOut,
    PRStaffOut, TaskOut, TaskUpdate,
)

router = APIRouter(prefix="/sales", tags=["sales-core"])


# ----- Branches / BCs / Locations -----

@router.get("/branches", response_model=list[BranchOut])
def list_branches(db: Session = Depends(get_db)):
    return db.query(Branch).order_by(Branch.code).all()


@router.get("/business-centers", response_model=list[BusinessCenterOut])
def list_business_centers(db: Session = Depends(get_db)):
    return db.query(BusinessCenter).order_by(BusinessCenter.code).all()


@router.get("/locations", response_model=list[LocationOut])
def list_locations(db: Session = Depends(get_db)):
    return db.query(Location).order_by(Location.code).all()


@router.get("/pr-groups", response_model=list[PRGroupOut])
def list_pr_groups(db: Session = Depends(get_db)):
    return db.query(PRGroup).order_by(PRGroup.code).all()


@router.get("/pr-staff", response_model=list[PRStaffOut])
def list_pr_staff(db: Session = Depends(get_db)):
    return db.query(PRStaff).order_by(PRStaff.pr_code).all()


# ----- Campaigns -----

@router.get("/campaigns", response_model=list[CampaignOut])
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(SalesCampaign).order_by(SalesCampaign.id.desc()).all()


@router.get("/campaigns/{cid}", response_model=CampaignOut)
def get_campaign(cid: int, db: Session = Depends(get_db)):
    c = db.get(SalesCampaign, cid)
    if not c: raise HTTPException(404, "Campaign not found")
    return c


# ----- Tasks -----

@router.get("/campaigns/{cid}/tasks", response_model=list[TaskOut])
def list_tasks(cid: int, db: Session = Depends(get_db)):
    return (
        db.query(CampaignTask)
        .filter(CampaignTask.campaign_id == cid)
        .order_by(CampaignTask.sort_order, CampaignTask.id)
        .all()
    )


@router.patch("/tasks/{tid}", response_model=TaskOut)
def update_task(tid: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    t = db.get(CampaignTask, tid)
    if not t: raise HTTPException(404, "Task not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(t, k, v)
    if "start_date" in data and "end_date" in data and t.start_date and t.end_date:
        t.duration_days = (t.end_date - t.start_date).days + 1
    db.commit(); db.refresh(t)
    return t


@router.delete("/tasks/{tid}", status_code=204)
def delete_task(tid: int, db: Session = Depends(get_db)):
    t = db.get(CampaignTask, tid)
    if not t: raise HTTPException(404, "Task not found")
    db.delete(t); db.commit()


# ----- Gantt-shaped read endpoint -----

@router.get("/campaigns/{cid}/gantt")
def gantt_payload(cid: int, db: Session = Depends(get_db)):
    """Return a Gantt-friendly payload: tasks + dependencies + grouping hints."""
    c = db.get(SalesCampaign, cid)
    if not c: raise HTTPException(404, "Campaign not found")
    tasks = (
        db.query(CampaignTask)
        .filter(CampaignTask.campaign_id == cid)
        .order_by(CampaignTask.sort_order, CampaignTask.id)
        .all()
    )
    return {
        "campaign": {
            "id": c.id, "name": c.name,
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat() if c.end_date else None,
        },
        "tasks": [
            {
                "id": t.id, "wbs": t.wbs_code, "name": t.task_name,
                "start": t.start_date.isoformat() if t.start_date else None,
                "end": t.end_date.isoformat() if t.end_date else None,
                "duration_days": t.duration_days,
                "progress": float(t.progress or 0),
                "status": t.status, "priority": t.priority,
                "risk_level": t.risk_level, "is_milestone": t.is_milestone,
                "is_summary": t.is_summary, "is_critical": t.is_critical,
                "parent_id": t.parent_task_id,
                "bc_id": t.business_center_id,
                "location_id": t.location_id,
                "distrito": t.distrito, "tipo_df_cp": t.tipo_df_cp,
                "pr_staff_id": t.pr_staff_id, "group_id": t.group_id,
                "people_in_charge": t.people_in_charge,
                "campana_ok": t.campana_ok,
            }
            for t in tasks
        ],
    }
