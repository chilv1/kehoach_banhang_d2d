"""AI Planner router: /goal /optimize /risk /recover /simulate /explain /daily."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.sales_planner.schemas import AICommandPayload, AIPlanResponse
from app.sales_planner.services.ai_planner import AIPlannerService, get_provider

router = APIRouter(prefix="/ai", tags=["sales-ai"])


def _service(db: Session) -> AIPlannerService:
    return AIPlannerService(db, provider=get_provider())


@router.post("/goal", response_model=AIPlanResponse)
def cmd_goal(payload: AICommandPayload, db: Session = Depends(get_db)):
    payload.command = "goal"
    try:
        return _service(db).run_command(payload)
    except Exception as exc:                                # noqa: BLE001
        raise HTTPException(400, str(exc))


@router.post("/optimize", response_model=AIPlanResponse)
def cmd_optimize(payload: AICommandPayload, db: Session = Depends(get_db)):
    payload.command = "optimize"
    return _service(db).run_command(payload)


@router.post("/risk", response_model=AIPlanResponse)
def cmd_risk(payload: AICommandPayload, db: Session = Depends(get_db)):
    payload.command = "risk"
    return _service(db).run_command(payload)


@router.post("/recover", response_model=AIPlanResponse)
def cmd_recover(payload: AICommandPayload, db: Session = Depends(get_db)):
    payload.command = "recover"
    return _service(db).run_command(payload)


@router.post("/simulate", response_model=AIPlanResponse)
def cmd_simulate(payload: AICommandPayload, db: Session = Depends(get_db)):
    payload.command = "simulate"
    return _service(db).run_command(payload)


@router.post("/explain", response_model=AIPlanResponse)
def cmd_explain(payload: AICommandPayload, db: Session = Depends(get_db)):
    payload.command = "explain"
    return _service(db).run_command(payload)


@router.post("/daily", response_model=AIPlanResponse)
def cmd_daily(payload: AICommandPayload, db: Session = Depends(get_db)):
    payload.command = "daily"
    return _service(db).run_command(payload)


@router.post("/apply-plan/{session_id}")
def apply_plan(session_id: int, db: Session = Depends(get_db)):
    try:
        n = _service(db).apply_plan(session_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"status": "applied", "tasks_created": n}
