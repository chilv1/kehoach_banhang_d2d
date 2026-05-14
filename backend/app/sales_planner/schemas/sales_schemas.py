"""Pydantic IO contracts for the sales planner.

These types are the API surface — they are intentionally narrower
than the ORM models so we don't accidentally leak internal fields.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Master data ----------

class BranchOut(ORMBase):
    id: int
    code: str
    name: str | None
    country: str


class BusinessCenterOut(ORMBase):
    id: int
    code: str
    branch_id: int
    name: str | None


class LocationOut(ORMBase):
    id: int
    code: str
    branch_id: int
    business_center_id: int
    departamento: str | None
    distrito: str | None
    tipo_df_cp: str | None
    horario_traffico: str | None
    fecha_alta_traffico: str | None
    prioridad: int
    latitud: float | None
    longitud: float | None
    nota: str | None
    is_active: bool


class PRGroupOut(ORMBase):
    id: int
    code: str
    business_center_id: int | None
    leader_pr_code: str | None
    member_count: int


class PRStaffOut(ORMBase):
    id: int
    pr_code: str
    owner_code: str | None
    branch_id: int
    business_center_id: int
    group_id: int | None
    tipo_pr: str | None
    leader: str | None
    kpi_trabajo: int
    cantidad_dia_trabajo: int
    estado: str
    is_active: bool


# ---------- Campaign + task ----------

CampaignStatus = Literal[
    "PLANNED", "IN_PROGRESS", "COMPLETED", "DELAYED",
    "NO_OK", "OK", "AT_RISK", "CANCELLED", "MILESTONE",
]


class CampaignOut(ORMBase):
    id: int
    name: str
    description: str | None
    branch_id: int | None
    start_date: date
    end_date: date | None
    status_date: date | None
    horizon_days: int


class TaskOut(ORMBase):
    id: int
    campaign_id: int
    parent_task_id: int | None
    wbs_code: str | None
    outline_level: int
    sort_order: int
    task_name: str
    location_id: int | None
    business_center_id: int | None
    distrito: str | None
    tipo_df_cp: str | None
    horario_traffico: str | None
    fecha_alta_traffico: str | None
    people_in_charge: str | None
    group_id: int | None
    pr_staff_id: int | None
    start_date: date | None
    end_date: date | None
    duration_days: int | None
    progress: float
    status: str
    priority: int
    risk_level: str
    risk_reason: str | None
    is_milestone: bool
    is_summary: bool
    is_critical: bool
    notes: str | None
    df_bts_code: str | None
    cumple_activaciones: bool | None
    cumple_digital: bool | None
    campana_ok: str | None


class TaskUpdate(BaseModel):
    task_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_days: int | None = None
    progress: float | None = Field(default=None, ge=0, le=100)
    status: CampaignStatus | None = None
    priority: int | None = None
    risk_level: Literal["low", "medium", "high"] | None = None
    risk_reason: str | None = None
    notes: str | None = None
    pr_staff_id: int | None = None
    group_id: int | None = None


# ---------- Import flow ----------

class ImportPreview(BaseModel):
    file_id: int
    filename: str
    sheets_detected: list[str]
    rows_per_sheet: dict[str, int]
    column_mapping_suggestion: dict[str, dict[str, str]]
    sample_rows: dict[str, list[dict]]
    warnings: list[str] = []


# ---------- AI ----------

class AICommandPayload(BaseModel):
    command: Literal[
        "goal", "optimize", "risk", "recover", "simulate", "explain", "daily",
    ]
    prompt: str = Field(..., max_length=4000)
    campaign_id: int | None = None
    scenario: dict | None = None
    provider: str | None = None


class AIMerch(BaseModel):
    boligrafo: int = 0
    taza: int = 0
    llavero: int = 0
    papin: int = 0
    sombrero: int = 0


class AIPlanItem(BaseModel):
    task_name: str = Field(min_length=3)
    code_ubicacion: str = Field(pattern=r"^CP\d+$")
    br: str
    bc: str
    distrito: str | None = None
    tipo_df_cp: str | None = None
    people_in_charge: str | None = None
    grupo_code_pr: str | None = None
    start_date: date
    end_date: date
    duration_days: int = Field(ge=1, le=365)
    priority: int = Field(ge=1, le=10)
    target_activation: int = 0
    target_mnp: int = 0
    target_tv360: int = 0
    target_bipay: int = 0
    planned_cost: float = 0
    merchandising: AIMerch = AIMerch()
    risk_level: Literal["low", "medium", "high"] = "low"
    risk_reason: str | None = None
    checklist: list[str] = []
    reasoning: str | None = None


class AIResourceAlloc(BaseModel):
    pr_code: str
    days: int = Field(ge=0)
    tasks: list[int] = []


class AIPlanResponse(BaseModel):
    session_id: int
    summary: str
    planning_assumptions: list[str] = []
    campaign_plan: list[AIPlanItem]
    resource_allocation: list[AIResourceAlloc] = []
    risks: list[dict] = []
    warnings: list[str] = []
    recommendations: list[str] = []
    changes_preview: list[dict] = []
    requires_user_approval: bool = True
    provider: str
    duration_ms: int


# ---------- Dashboard ----------

class BCPerformance(BaseModel):
    bc_code: str
    meta_campana: int = 0
    resultado_campana: int = 0
    meta_activation: int = 0
    result_activation: int = 0
    meta_mnp: int = 0
    result_mnp: int = 0
    meta_bipay: int = 0
    result_bipay: int = 0
    meta_tv360: int = 0
    result_tv360: int = 0


class DashboardSummary(BaseModel):
    bc_performance: list[BCPerformance]
    total_meta: int
    total_result: int
    total_pct: float
    campaigns_total: int
    campaigns_ok: int
    campaigns_no_ok: int
    budget_planned: float
    budget_actual: float
