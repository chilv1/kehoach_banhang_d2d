"""Endpoints mới cho Phase 1, 3, 4, 5, 6, 7."""
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.task import Task
from app.services.cost import recompute_costs
from app.services.evm import compute_evm
from app.services.leveling import (
    compute_daily_load, find_overallocations, level_resources,
)
from app.services.outline import indent, outdent, move, recompute_wbs
from app.services.variance import project_variance
from app.services.xml_io import export_project_xml, import_project_xml

router = APIRouter()


# ============ Phase 1: Outline ============
@router.post("/tasks/{tid}/indent")
def task_indent(tid: int, db: Session = Depends(get_db)):
    try:
        t = indent(db, tid)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"id": t.id, "outline_level": t.outline_level,
            "parent_id": t.parent_id, "wbs": t.wbs}


@router.post("/tasks/{tid}/outdent")
def task_outdent(tid: int, db: Session = Depends(get_db)):
    try:
        t = outdent(db, tid)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"id": t.id, "outline_level": t.outline_level,
            "parent_id": t.parent_id, "wbs": t.wbs}


class MovePayload(BaseModel):
    sort_order: int


@router.post("/tasks/{tid}/move")
def task_move(tid: int, payload: MovePayload, db: Session = Depends(get_db)):
    try:
        t = move(db, tid, payload.sort_order)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"id": t.id, "sort_order": t.sort_order, "wbs": t.wbs}


@router.post("/projects/{pid}/wbs/recompute")
def wbs_recompute(pid: int, db: Session = Depends(get_db)):
    recompute_wbs(db, pid)
    return {"ok": True}


# ============ Phase 3: Costs ============
@router.post("/projects/{pid}/costs/recompute")
def costs_recompute(pid: int, db: Session = Depends(get_db)):
    return recompute_costs(db, pid)


# ============ Phase 4: Tracking ============
@router.get("/projects/{pid}/variance")
def get_variance(pid: int, baseline_number: int = 0,
                  db: Session = Depends(get_db)):
    return {"baseline_number": baseline_number,
            "tasks": project_variance(db, pid, baseline_number)}


# ============ Phase 5: Leveling ============
@router.get("/projects/{pid}/overallocations")
def get_overallocations(pid: int, db: Session = Depends(get_db)):
    return find_overallocations(db, pid)


@router.get("/projects/{pid}/resource-load")
def get_resource_load(pid: int, db: Session = Depends(get_db)):
    load = compute_daily_load(db, pid)
    return {
        str(rid): {d.isoformat(): round(u, 2) for d, u in by_day.items()}
        for rid, by_day in load.items()
    }


@router.post("/projects/{pid}/level")
def post_level(pid: int, db: Session = Depends(get_db)):
    return level_resources(db, pid)


# ============ Phase 6: EVM ============
@router.get("/projects/{pid}/evm")
def get_evm(pid: int, status_date: datetime | None = None,
             db: Session = Depends(get_db)):
    try:
        return compute_evm(db, pid, status_date)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ============ Phase 7: XML ============
@router.get("/projects/{pid}/export-xml")
def get_export_xml(pid: int, db: Session = Depends(get_db)):
    try:
        xml = export_project_xml(db, pid)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return Response(
        content=xml,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="project_{pid}.xml"',
        },
    )


@router.post("/projects/import-xml")
async def post_import_xml(
    file: UploadFile = File(...), db: Session = Depends(get_db),
):
    data = await file.read()
    try:
        pid = import_project_xml(db, data)
    except Exception as e:
        raise HTTPException(400, f"Lỗi parse XML: {e}")
    return {"project_id": pid, "status": "imported"}
