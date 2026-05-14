"""POST /api/imports/excel  +  preview / commit."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.sales_planner.services.excel_import import CampanaPlanImporter

router = APIRouter(prefix="/imports", tags=["sales-imports"])


@router.post("/excel")
async def upload_excel(
    file: UploadFile = File(...), commit: bool = True,
    db: Session = Depends(get_db),
):
    payload = await file.read()
    importer = CampanaPlanImporter(db)
    try:
        result = importer.import_bytes(
            payload, filename=file.filename or "campaign.xlsx", commit=commit,
        )
    except Exception as exc:                                # noqa: BLE001
        raise HTTPException(400, f"Import failed: {exc}")
    return {
        "file_id": result.file_id,
        "sheets_detected": result.sheets_detected,
        "rows_per_sheet": result.rows_per_sheet,
        "inserted": result.inserted,
        "warnings": result.warnings,
        "errors": result.errors,
    }
