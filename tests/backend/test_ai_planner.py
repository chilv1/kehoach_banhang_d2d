"""Tests for the AI Planner (stub provider) + constraint solver."""
from datetime import date, timedelta

from app.sales_planner.schemas import AICommandPayload, AIPlanItem, AIMerch
from app.sales_planner.services.ai_planner import AIPlannerService, StubProvider
from app.sales_planner.services.constraint_solver import validate_plan
from app.sales_planner.services.excel_import import CampanaPlanImporter
from app.sales_planner.models import SalesCampaign


def _seed(db, excel_bytes):
    CampanaPlanImporter(db).import_bytes(excel_bytes, filename="campaign.xlsx")
    return db.query(SalesCampaign).first()


def test_stub_provider_returns_valid_plan(db, excel_bytes):
    campaign = _seed(db, excel_bytes)
    svc = AIPlannerService(db, provider=StubProvider())
    resp = svc.run_command(AICommandPayload(
        command="goal", prompt="Generate plan", campaign_id=campaign.id,
    ))
    assert resp.session_id > 0
    assert resp.provider == "stub"
    assert len(resp.campaign_plan) >= 1
    assert resp.duration_ms >= 0
    assert resp.requires_user_approval is True


def test_constraint_pr_overlap_detected(db, excel_bytes):
    _seed(db, excel_bytes)
    horizon = date.today()
    same_day = horizon + timedelta(days=1)
    # Build two items reusing same PR same day; locations must exist in seed.
    plan = [
        AIPlanItem(
            task_name="Task A", code_ubicacion="CP01", br="LI3BR", bc="LI3BC12",
            start_date=same_day, end_date=same_day, duration_days=1, priority=1,
            grupo_code_pr="LI3PR10116", merchandising=AIMerch(),
        ),
        AIPlanItem(
            task_name="Task B", code_ubicacion="CP02", br="LI3BR", bc="LI3BC11",
            start_date=same_day, end_date=same_day, duration_days=1, priority=1,
            grupo_code_pr="LI3PR10116", merchandising=AIMerch(),
        ),
    ]
    report = validate_plan(
        db, plan, horizon_start=horizon, horizon_end=horizon + timedelta(days=10),
    )
    codes = [v.code for v in report.violations]
    assert "C1" in codes  # PR double-booked
