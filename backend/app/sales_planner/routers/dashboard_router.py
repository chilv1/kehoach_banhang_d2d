"""Dashboard endpoints — mirrors Sheet 'General' style."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.sales_planner.models import (
    BusinessCenter, CampaignResult, CampaignTarget, CampaignTask,
)
from app.sales_planner.schemas import BCPerformance, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["sales-dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    bcs = db.query(BusinessCenter).all()
    rows: list[BCPerformance] = []
    total_meta = total_result = 0

    for bc in bcs:
        # Aggregate per BC
        targets = (
            db.query(
                func.coalesce(func.sum(CampaignTarget.prepago + CampaignTarget.postpago), 0).label("act"),
                func.coalesce(func.sum(CampaignTarget.mnp), 0).label("mnp"),
                func.coalesce(func.sum(CampaignTarget.bipay), 0).label("bipay"),
                func.coalesce(func.sum(CampaignTarget.tv360), 0).label("tv360"),
            )
            .join(CampaignTask, CampaignTask.id == CampaignTarget.task_id)
            .filter(CampaignTask.business_center_id == bc.id)
            .one()
        )
        results = (
            db.query(
                func.coalesce(func.sum(CampaignResult.prepago + CampaignResult.postpago), 0).label("act"),
                func.coalesce(func.sum(CampaignResult.mnp), 0).label("mnp"),
                func.coalesce(func.sum(CampaignResult.bipay), 0).label("bipay"),
                func.coalesce(func.sum(CampaignResult.tv360), 0).label("tv360"),
            )
            .join(CampaignTask, CampaignTask.id == CampaignResult.task_id)
            .filter(CampaignTask.business_center_id == bc.id)
            .one()
        )
        rows.append(BCPerformance(
            bc_code=bc.code,
            meta_activation=int(targets.act or 0),
            result_activation=int(results.act or 0),
            meta_mnp=int(targets.mnp or 0),
            result_mnp=int(results.mnp or 0),
            meta_bipay=int(targets.bipay or 0),
            result_bipay=int(results.bipay or 0),
            meta_tv360=int(targets.tv360 or 0),
            result_tv360=int(results.tv360 or 0),
        ))
        total_meta += int(targets.act or 0) + int(targets.mnp or 0)
        total_result += int(results.act or 0) + int(results.mnp or 0)

    total_pct = (total_result / total_meta * 100) if total_meta > 0 else 0.0
    n = db.query(CampaignTask).count()
    n_ok = db.query(CampaignTask).filter(CampaignTask.campana_ok == "OK").count()
    n_no_ok = db.query(CampaignTask).filter(CampaignTask.campana_ok == "NO OK").count()

    return DashboardSummary(
        bc_performance=rows,
        total_meta=total_meta, total_result=total_result, total_pct=round(total_pct, 2),
        campaigns_total=n, campaigns_ok=n_ok, campaigns_no_ok=n_no_ok,
        budget_planned=0.0, budget_actual=0.0,
    )
