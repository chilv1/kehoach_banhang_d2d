"""Export endpoints — Excel / CSV / JSON (PDF/PNG handled by frontend html2canvas + server post)."""
from __future__ import annotations

import io
import json

import openpyxl
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.sales_planner.models import CampaignTask, SalesCampaign

router = APIRouter(prefix="/exports", tags=["sales-exports"])


@router.get("/{campaign_id}/excel")
def export_excel(campaign_id: int, db: Session = Depends(get_db)):
    camp = db.get(SalesCampaign, campaign_id)
    if not camp: raise HTTPException(404, "Campaign not found")
    tasks = (
        db.query(CampaignTask)
        .filter(CampaignTask.campaign_id == campaign_id)
        .order_by(CampaignTask.sort_order, CampaignTask.id)
        .all()
    )
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plan CP"
    ws.append([
        "WBS", "Task", "BC", "Distrito", "Tipo DF/CP", "People InCharge",
        "Start Date", "End Date", "Duration", "Status", "Priority",
        "Risk", "Progress %", "Note",
    ])
    for t in tasks:
        ws.append([
            t.wbs_code, t.task_name,
            t.business_center.code if t.business_center else None,
            t.distrito, t.tipo_df_cp, t.people_in_charge,
            t.start_date.isoformat() if t.start_date else None,
            t.end_date.isoformat() if t.end_date else None,
            t.duration_days, t.status, t.priority,
            t.risk_level, float(t.progress or 0), t.notes,
        ])
    buf = io.BytesIO()
    wb.save(buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="campaign_{campaign_id}.xlsx"'},
    )


@router.get("/{campaign_id}/json")
def export_json(campaign_id: int, db: Session = Depends(get_db)):
    camp = db.get(SalesCampaign, campaign_id)
    if not camp: raise HTTPException(404, "Campaign not found")
    tasks = db.query(CampaignTask).filter(CampaignTask.campaign_id == campaign_id).all()
    return {
        "campaign": {"id": camp.id, "name": camp.name},
        "tasks": [
            {
                "id": t.id, "name": t.task_name, "start": t.start_date.isoformat() if t.start_date else None,
                "end": t.end_date.isoformat() if t.end_date else None,
                "status": t.status, "priority": t.priority,
            }
            for t in tasks
        ],
    }
