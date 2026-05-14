"""SQLAlchemy ORM models for the sales planner domain.

Tables mirror `backend/migrations/001_sales_planner.sql`.
The module re-uses the existing `app.db.session.Base` declarative base,
so creating these tables alongside the MS-Project entities is automatic
via `Base.metadata.create_all`.
"""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, CHAR, Date, DateTime, Float, ForeignKey, Integer,
    Numeric, SmallInteger, String, Text, UniqueConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ---------- Reference / master data ----------

class Branch(Base):
    __tablename__ = "sales_branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(60), default="PE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BusinessCenter(Base):
    __tablename__ = "sales_business_centers"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("sales_branches.id", ondelete="CASCADE"))
    name: Mapped[Optional[str]] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    branch: Mapped[Branch] = relationship()


class Location(Base):
    __tablename__ = "sales_locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("sales_branches.id"))
    business_center_id: Mapped[int] = mapped_column(ForeignKey("sales_business_centers.id"))
    departamento: Mapped[Optional[str]] = mapped_column(String(60))
    distrito: Mapped[Optional[str]] = mapped_column(String(120))
    tipo_df_cp: Mapped[Optional[str]] = mapped_column(String(40))
    horario_traffico: Mapped[Optional[str]] = mapped_column(String(40))
    fecha_alta_traffico: Mapped[Optional[str]] = mapped_column(String(15))
    prioridad: Mapped[int] = mapped_column(SmallInteger, default=1)
    latitud: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    longitud: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    nota: Mapped[Optional[str]] = mapped_column(Text)
    meta_prepago: Mapped[int] = mapped_column(Integer, default=0)
    meta_postpago: Mapped[int] = mapped_column(Integer, default=0)
    meta_bipay: Mapped[int] = mapped_column(Integer, default=0)
    meta_tv360: Mapped[int] = mapped_column(Integer, default=0)
    meta_mnp: Mapped[int] = mapped_column(Integer, default=0)
    meta_agentes: Mapped[int] = mapped_column(Integer, default=0)
    meta_usuarios_bipay: Mapped[int] = mapped_column(Integer, default=0)
    meta_pago_servicios: Mapped[int] = mapped_column(Integer, default=0)
    meta_tusami: Mapped[int] = mapped_column(Integer, default=0)
    gasto_comida: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    gasto_hotel: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    gasto_movilidad: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    gasto_renta_local: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    merch_boligrafo: Mapped[int] = mapped_column(Integer, default=0)
    merch_taza: Mapped[int] = mapped_column(Integer, default=0)
    merch_llavero: Mapped[int] = mapped_column(Integer, default=0)
    merch_papin: Mapped[int] = mapped_column(Integer, default=0)
    merch_sombrero: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
    )

    branch: Mapped[Branch] = relationship()
    business_center: Mapped[BusinessCenter] = relationship()


# ---------- PR staff & groups ----------

class PRGroup(Base):
    __tablename__ = "sales_pr_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    business_center_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_business_centers.id", ondelete="SET NULL"),
    )
    leader_pr_code: Mapped[Optional[str]] = mapped_column(String(40))
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PRStaff(Base):
    __tablename__ = "sales_pr_staff"

    id: Mapped[int] = mapped_column(primary_key=True)
    pr_code: Mapped[str] = mapped_column(String(40), unique=True)
    owner_code: Mapped[Optional[str]] = mapped_column(String(60))
    branch_id: Mapped[int] = mapped_column(ForeignKey("sales_branches.id"))
    business_center_id: Mapped[int] = mapped_column(ForeignKey("sales_business_centers.id"))
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_pr_groups.id", ondelete="SET NULL"),
    )
    tipo_pr: Mapped[Optional[str]] = mapped_column(String(30))
    leader: Mapped[Optional[str]] = mapped_column(String(60))
    kpi_trabajo: Mapped[int] = mapped_column(Integer, default=0)
    cantidad_dia_trabajo: Mapped[int] = mapped_column(Integer, default=18)
    estado: Mapped[str] = mapped_column(String(10), default="OK")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    branch: Mapped[Branch] = relationship()
    business_center: Mapped[BusinessCenter] = relationship()
    group: Mapped[Optional[PRGroup]] = relationship()


# ---------- Campaign + Tasks ----------

class SalesCampaign(Base):
    __tablename__ = "sales_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    branch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sales_branches.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    status_date: Mapped[Optional[date]] = mapped_column(Date)
    horizon_days: Mapped[int] = mapped_column(Integer, default=30)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
    )

    branch: Mapped[Optional[Branch]] = relationship()
    tasks: Mapped[list["CampaignTask"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan",
    )


class CampaignTask(Base):
    __tablename__ = "sales_campaign_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("sales_campaigns.id", ondelete="CASCADE"),
    )
    parent_task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_campaign_tasks.id", ondelete="CASCADE"),
    )
    wbs_code: Mapped[Optional[str]] = mapped_column(String(40))
    outline_level: Mapped[int] = mapped_column(SmallInteger, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    task_name: Mapped[str] = mapped_column(String(300))
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sales_locations.id"))
    business_center_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_business_centers.id"),
    )
    distrito: Mapped[Optional[str]] = mapped_column(String(120))
    tipo_df_cp: Mapped[Optional[str]] = mapped_column(String(40))
    horario_traffico: Mapped[Optional[str]] = mapped_column(String(40))
    fecha_alta_traffico: Mapped[Optional[str]] = mapped_column(String(15))
    people_in_charge: Mapped[Optional[str]] = mapped_column(String(120))
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_pr_groups.id", ondelete="SET NULL"),
    )
    pr_staff_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_pr_staff.id", ondelete="SET NULL"),
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    duration_days: Mapped[Optional[int]] = mapped_column(Integer)
    progress: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="PLANNED")
    priority: Mapped[int] = mapped_column(SmallInteger, default=500)
    risk_level: Mapped[str] = mapped_column(String(10), default="low")
    risk_reason: Mapped[Optional[str]] = mapped_column(Text)
    is_milestone: Mapped[bool] = mapped_column(Boolean, default=False)
    is_summary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    df_bts_code: Mapped[Optional[str]] = mapped_column(String(60))
    cumple_activaciones: Mapped[Optional[bool]] = mapped_column(Boolean)
    cumple_digital: Mapped[Optional[bool]] = mapped_column(Boolean)
    campana_ok: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
    )

    campaign: Mapped[SalesCampaign] = relationship(back_populates="tasks")
    location: Mapped[Optional[Location]] = relationship()
    business_center: Mapped[Optional[BusinessCenter]] = relationship()
    pr_staff: Mapped[Optional[PRStaff]] = relationship()
    group: Mapped[Optional[PRGroup]] = relationship()


class SalesTaskDependency(Base):
    __tablename__ = "sales_task_dependencies"
    __table_args__ = (
        UniqueConstraint("predecessor_id", "successor_id", name="uq_sales_dep"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    predecessor_id: Mapped[int] = mapped_column(
        ForeignKey("sales_campaign_tasks.id", ondelete="CASCADE"),
    )
    successor_id: Mapped[int] = mapped_column(
        ForeignKey("sales_campaign_tasks.id", ondelete="CASCADE"),
    )
    link_type: Mapped[str] = mapped_column(String(2), default="FS")
    lag_hours: Mapped[float] = mapped_column(Numeric(8, 2), default=0)


# ---------- Targets / Results / Expenses ----------

class CampaignTarget(Base):
    __tablename__ = "sales_campaign_targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("sales_campaign_tasks.id", ondelete="CASCADE"), unique=True,
    )
    prepago: Mapped[int] = mapped_column(Integer, default=0)
    postpago: Mapped[int] = mapped_column(Integer, default=0)
    bipay: Mapped[int] = mapped_column(Integer, default=0)
    tv360: Mapped[int] = mapped_column(Integer, default=0)
    mnp: Mapped[int] = mapped_column(Integer, default=0)
    agentes: Mapped[int] = mapped_column(Integer, default=0)
    usuarios_bipay: Mapped[int] = mapped_column(Integer, default=0)
    pago_servicios: Mapped[int] = mapped_column(Integer, default=0)
    tusami: Mapped[int] = mapped_column(Integer, default=0)


class CampaignResult(Base):
    __tablename__ = "sales_campaign_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("sales_campaign_tasks.id", ondelete="CASCADE"), unique=True,
    )
    prepago: Mapped[int] = mapped_column(Integer, default=0)
    postpago: Mapped[int] = mapped_column(Integer, default=0)
    bipay: Mapped[int] = mapped_column(Integer, default=0)
    tv360: Mapped[int] = mapped_column(Integer, default=0)
    mnp: Mapped[int] = mapped_column(Integer, default=0)
    agentes: Mapped[int] = mapped_column(Integer, default=0)
    usuarios_bipay: Mapped[int] = mapped_column(Integer, default=0)
    pago_servicios: Mapped[int] = mapped_column(Integer, default=0)
    tusami: Mapped[int] = mapped_column(Integer, default=0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CampaignExpense(Base):
    __tablename__ = "sales_campaign_expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("sales_campaign_tasks.id", ondelete="CASCADE"),
    )
    pago_comida: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    pago_hotel: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    pago_movilidad: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    pago_renta_local: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    gasto_total_planned: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    gasto_total_actual: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    evidencia_pago: Mapped[bool] = mapped_column(Boolean, default=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Merchandising(Base):
    __tablename__ = "sales_merchandising"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("sales_campaign_tasks.id", ondelete="CASCADE"), unique=True,
    )
    boligrafo: Mapped[int] = mapped_column(Integer, default=0)
    taza: Mapped[int] = mapped_column(Integer, default=0)
    llavero: Mapped[int] = mapped_column(Integer, default=0)
    papin: Mapped[int] = mapped_column(Integer, default=0)
    sombrero: Mapped[int] = mapped_column(Integer, default=0)
    entregado: Mapped[bool] = mapped_column(Boolean, default=False)


class CampaignChecklistItem(Base):
    __tablename__ = "sales_campaign_checklists"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("sales_campaign_tasks.id", ondelete="CASCADE"),
    )
    item: Mapped[str] = mapped_column(String(200))
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------- Daily plan / actual ----------

class DailyPlan(Base):
    __tablename__ = "sales_daily_plan"
    __table_args__ = (
        UniqueConstraint("task_id", "pr_staff_id", "plan_date", name="uq_daily_plan"),
        Index("ix_daily_plan_date", "plan_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_campaign_tasks.id", ondelete="CASCADE"),
    )
    pr_staff_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_pr_staff.id", ondelete="CASCADE"),
    )
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_pr_groups.id", ondelete="CASCADE"),
    )
    plan_date: Mapped[date] = mapped_column(Date)
    units: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0)


class DailyActual(Base):
    __tablename__ = "sales_daily_actual"
    __table_args__ = (
        UniqueConstraint("task_id", "pr_staff_id", "actual_date", name="uq_daily_actual"),
        Index("ix_daily_actual_date", "actual_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_campaign_tasks.id", ondelete="CASCADE"),
    )
    pr_staff_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_pr_staff.id", ondelete="CASCADE"),
    )
    actual_date: Mapped[date] = mapped_column(Date)
    units: Mapped[float] = mapped_column(Numeric(4, 2), default=0)
    note: Mapped[Optional[str]] = mapped_column(Text)


# ---------- AI planning ----------

class AIPlanningSession(Base):
    __tablename__ = "sales_ai_planning_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_campaigns.id", ondelete="SET NULL"),
    )
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    command: Mapped[str] = mapped_column(String(20))
    user_prompt: Mapped[Optional[str]] = mapped_column(Text)
    scenario: Mapped[Optional[str]] = mapped_column(Text)
    raw_response: Mapped[Optional[str]] = mapped_column(Text)
    validated_plan: Mapped[Optional[str]] = mapped_column(Text)
    schema_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    constraint_violations: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="running")
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    provider: Mapped[Optional[str]] = mapped_column(String(40))
    model_id: Mapped[Optional[str]] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class AILogRecommendation(Base):
    __tablename__ = "sales_ai_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sales_ai_planning_sessions.id", ondelete="CASCADE"),
    )
    kind: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(10), default="info")
    target_task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_campaign_tasks.id"),
    )
    target_pr_code: Mapped[Optional[str]] = mapped_column(String(40))
    target_bc_code: Mapped[Optional[str]] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[Optional[str]] = mapped_column(Text)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------- File import + audit ----------

class ImportedFile(Base):
    __tablename__ = "sales_imported_files"
    __table_args__ = (
        UniqueConstraint("sha256", name="uq_sales_import_sha"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(300))
    original_name: Mapped[Optional[str]] = mapped_column(String(300))
    sha256: Mapped[str] = mapped_column(CHAR(64))
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    uploaded_by: Mapped[Optional[int]] = mapped_column(Integer)
    storage_uri: Mapped[Optional[str]] = mapped_column(Text)
    sheets_detected: Mapped[int] = mapped_column(Integer, default=0)
    rows_imported: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error_log: Mapped[Optional[str]] = mapped_column(Text)
    column_mapping: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    committed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class SalesAuditLog(Base):
    __tablename__ = "sales_audit_logs"
    __table_args__ = (
        Index("ix_sales_audit_entity", "entity", "entity_id"),
        Index("ix_sales_audit_user", "user_id"),
        Index("ix_sales_audit_time", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    entity: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20))
    before_state: Mapped[Optional[str]] = mapped_column(Text)
    after_state: Mapped[Optional[str]] = mapped_column(Text)
    ip: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
