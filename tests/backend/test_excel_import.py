"""Smoke tests for the Excel importer."""
from app.sales_planner.models import (
    BusinessCenter, CampaignTask, DailyPlan, Location, PRGroup, PRStaff,
    SalesCampaign,
)
from app.sales_planner.services.excel_import import CampanaPlanImporter


def test_import_campana_plan(db, excel_bytes):
    result = CampanaPlanImporter(db).import_bytes(
        excel_bytes, filename="Campana Plan.xlsx",
    )
    assert "Plan CP" in result.sheets_detected
    assert "Ubicacion" in result.sheets_detected
    assert "PR Grupo" in result.sheets_detected
    assert result.inserted["locations"] == 81
    assert result.inserted["pr_staff"] == 68
    assert result.inserted["campaign_tasks"] == 81

    assert db.query(Location).count() == 81
    assert db.query(PRStaff).count() == 68
    assert db.query(BusinessCenter).count() == 9
    assert db.query(SalesCampaign).count() == 1
    assert db.query(CampaignTask).count() == 81
    assert db.query(PRGroup).count() > 0
    assert db.query(DailyPlan).count() > 0


def test_excel_serial_date_conversion():
    from app.sales_planner.services.excel_import import excel_serial_to_date
    from datetime import date

    assert excel_serial_to_date(45748) == date(2025, 4, 1)  # arbitrary value
    assert excel_serial_to_date(None) is None
    assert excel_serial_to_date("") is None
    assert excel_serial_to_date("2026-05-01") == date(2026, 5, 1)
