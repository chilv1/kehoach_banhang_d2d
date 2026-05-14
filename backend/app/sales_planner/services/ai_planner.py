"""AI Planner module — 6 modes (goal / optimize / risk / recover / simulate / explain / daily).

The module is provider-agnostic:

    +-------------+         +-------------------------+
    | UI command  | ---->   | router.ai_router        |
    +-------------+         +-----+-----------+-------+
                                  |           |
                                  v           v
                       +----------+-+      +--+-------------+
                       | LLMProvider|      | ConstraintSolver|
                       | (OpenAI /  |      | (validator +    |
                       |  Anthropic |      |  greedy fixer)  |
                       |  / stub)   |      +-----------------+
                       +------------+
                                  |
                                  v
                              JSON plan
                                  |
                                  v
                            schema validation
                                  |
                                  v
                          diff vs current plan
                                  |
                                  v
                            user approval flow

Phase 1 ships a deterministic **rules-based stub** as the default provider so
the rest of the pipeline (validate, diff, apply, audit) is end-to-end testable
without an LLM bill.
"""
from __future__ import annotations

import abc
import json
import os
import time
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.sales_planner.models import (
    AIPlanningSession, CampaignTask, Location, PRStaff, SalesCampaign,
)
from app.sales_planner.schemas import (
    AIPlanItem, AIPlanResponse, AIResourceAlloc, AICommandPayload, AIMerch,
)
from .constraint_solver import validate_plan


# ============================================================
# Provider abstraction
# ============================================================

class LLMProvider(abc.ABC):
    name: str = "abstract"

    @abc.abstractmethod
    def generate_plan(self, *, command: str, prompt: str,
                       context: dict, scenario: dict | None) -> dict:
        """Return a dict matching the AISalesPlan schema."""

    def health(self) -> bool:
        return True


class StubProvider(LLMProvider):
    """Deterministic planner used by default and in tests.

    Picks locations from context['locations'] sorted by (prioridad, code) and
    assigns them to PR staff in round-robin, honouring fecha_alta_traffico
    where possible.
    """

    name = "stub"

    def generate_plan(self, *, command, prompt, context, scenario):
        locations: list[dict] = context.get("locations", [])
        pr_staff: list[dict] = context.get("pr_staff", [])
        horizon_start: date = context["horizon_start"]
        horizon_end: date = context["horizon_end"]

        # Sort high priority first
        sorted_locs = sorted(locations, key=lambda l: (l["prioridad"], l["code"]))
        pr_cycle = [p for p in pr_staff if p["is_active"]] or [{"pr_code": "UNASSIGNED"}]

        plan_items: list[dict] = []
        cur_day = horizon_start
        i = 0
        while cur_day <= horizon_end and i < len(sorted_locs):
            loc = sorted_locs[i]
            # advance day if doesn't match traffic
            if not _matches_traffic(loc.get("fecha_alta_traffico"), cur_day):
                cur_day += timedelta(days=1)
                continue
            pr = pr_cycle[i % len(pr_cycle)]
            plan_items.append({
                "task_name": f"{loc.get('distrito') or loc['code']} — {loc.get('tipo_df_cp') or 'Campaign'}",
                "code_ubicacion": loc["code"],
                "br": loc["br"],
                "bc": loc["bc"],
                "distrito": loc.get("distrito"),
                "tipo_df_cp": loc.get("tipo_df_cp"),
                "people_in_charge": pr.get("pr_code"),
                "grupo_code_pr": pr.get("pr_code"),
                "start_date": cur_day.isoformat(),
                "end_date": cur_day.isoformat(),
                "duration_days": 1,
                "priority": loc["prioridad"],
                "target_activation": int(loc.get("meta_prepago", 0) + loc.get("meta_postpago", 0)),
                "target_mnp": int(loc.get("meta_mnp", 0)),
                "target_tv360": int(loc.get("meta_tv360", 0)),
                "target_bipay": int(loc.get("meta_bipay", 0)),
                "planned_cost": float(
                    loc.get("gasto_comida", 0) + loc.get("gasto_hotel", 0)
                    + loc.get("gasto_movilidad", 0) + loc.get("gasto_renta_local", 0)
                ),
                "merchandising": {
                    "boligrafo": int(loc.get("merch_boligrafo", 0)),
                    "taza": int(loc.get("merch_taza", 0)),
                    "llavero": int(loc.get("merch_llavero", 0)),
                    "papin": int(loc.get("merch_papin", 0)),
                    "sombrero": int(loc.get("merch_sombrero", 0)),
                },
                "risk_level": "high" if loc["prioridad"] == 1 else "low",
                "risk_reason": "High-priority location" if loc["prioridad"] == 1 else None,
                "checklist": ["Set up booth", "Activate metrics", "Capture evidencia"],
                "reasoning": f"Stub planner — priority {loc['prioridad']} ordered first; PR {pr.get('pr_code')} assigned by round-robin.",
            })
            cur_day += timedelta(days=1)
            i += 1

        return {
            "summary": (
                f"Generated stub plan for command `{command}` with {len(plan_items)} tasks "
                f"from {horizon_start} to {horizon_end}."
            ),
            "planning_assumptions": [
                "Priority 1 locations scheduled first",
                "PR assigned round-robin",
                "Fecha Alta Traffico honoured when possible",
            ],
            "campaign_plan": plan_items,
            "resource_allocation": _summarise_alloc(plan_items),
            "risks": [],
            "warnings": [],
            "recommendations": [],
            "changes_preview": [],
            "requires_user_approval": True,
        }


def _matches_traffic(traffic: str | None, day: date) -> bool:
    if not traffic:
        return True
    t = traffic.strip().upper()
    wd = day.weekday()
    table = {"MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, "THURSDAY": 3,
             "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6}
    if t == "WEEKDAY":
        return wd < 5
    if t == "WEEKEND":
        return wd >= 5
    if t in table:
        return wd == table[t]
    return True


def _summarise_alloc(items: list[dict]) -> list[dict]:
    bucket: dict[str, int] = {}
    for it in items:
        pr = it.get("grupo_code_pr") or "UNASSIGNED"
        bucket[pr] = bucket.get(pr, 0) + 1
    return [{"pr_code": k, "days": v, "tasks": []} for k, v in bucket.items()]


# Future: real OpenAI/Anthropic providers go here. They share the same interface.


# ============================================================
# Service entry
# ============================================================

class AIPlannerService:
    def __init__(self, db: Session, provider: LLMProvider | None = None):
        self.db = db
        self.provider = provider or StubProvider()

    def run_command(self, payload: AICommandPayload) -> AIPlanResponse:
        started = time.time()
        campaign = (
            self.db.get(SalesCampaign, payload.campaign_id)
            if payload.campaign_id else None
        )
        context = self._build_context(campaign)

        session = AIPlanningSession(
            campaign_id=campaign.id if campaign else None,
            command=payload.command,
            user_prompt=payload.prompt,
            scenario=json.dumps(payload.scenario or {}),
            provider=self.provider.name,
            status="running",
        )
        self.db.add(session)
        self.db.flush()

        try:
            raw = self.provider.generate_plan(
                command=payload.command, prompt=payload.prompt,
                context=context, scenario=payload.scenario,
            )
        except Exception as exc:                                # noqa: BLE001
            session.status = "rejected"
            session.raw_response = json.dumps({"error": str(exc)})
            self.db.commit()
            raise

        session.raw_response = json.dumps(raw, default=str)

        # ---- Schema validation ----
        try:
            plan_items = [AIPlanItem.model_validate(p) for p in raw["campaign_plan"]]
        except Exception as exc:                                # noqa: BLE001
            session.status = "rejected"
            session.constraint_violations = json.dumps([{"schema_error": str(exc)}])
            self.db.commit()
            raise

        session.schema_ok = True

        # ---- Hard-constraint validation ----
        horizon_start = campaign.start_date if campaign else context["horizon_start"]
        horizon_end = campaign.end_date if campaign and campaign.end_date else context["horizon_end"]
        report = validate_plan(self.db, plan_items,
                                horizon_start=horizon_start,
                                horizon_end=horizon_end)
        if not report.ok:
            session.status = "rejected"
        else:
            session.status = "awaiting_approval"
        session.constraint_violations = json.dumps(
            [v.__dict__ for v in report.violations], default=str
        )
        session.validated_plan = json.dumps([p.model_dump(mode="json") for p in plan_items], default=str)
        session.duration_ms = int((time.time() - started) * 1000)
        self.db.commit()

        return AIPlanResponse(
            session_id=session.id,
            summary=raw["summary"],
            planning_assumptions=raw.get("planning_assumptions", []),
            campaign_plan=plan_items,
            resource_allocation=[AIResourceAlloc(**a) for a in raw.get("resource_allocation", [])],
            risks=raw.get("risks", []),
            warnings=raw.get("warnings", []) + [v.message for v in report.violations],
            recommendations=raw.get("recommendations", []),
            changes_preview=raw.get("changes_preview", []),
            requires_user_approval=True,
            provider=self.provider.name,
            duration_ms=session.duration_ms,
        )

    def apply_plan(self, session_id: int, *, user_id: int | None = None) -> int:
        """Materialise an approved plan into `sales_campaign_tasks`."""
        session = self.db.get(AIPlanningSession, session_id)
        if not session or session.status != "awaiting_approval":
            raise ValueError("AI session not ready to apply")

        validated = json.loads(session.validated_plan or "[]")
        camp = self.db.get(SalesCampaign, session.campaign_id) if session.campaign_id else None
        if not camp:
            # Create new campaign
            ds = [date.fromisoformat(p["start_date"]) for p in validated]
            de = [date.fromisoformat(p["end_date"]) for p in validated]
            camp = SalesCampaign(
                name=f"AI Plan — {datetime.utcnow().isoformat(timespec='seconds')}",
                start_date=min(ds) if ds else date.today(),
                end_date=max(de) if de else date.today(),
            )
            self.db.add(camp)
            self.db.flush()
            session.campaign_id = camp.id

        # Insert tasks (idempotent by task_name + start_date within campaign)
        inserted = 0
        for p in validated:
            task = CampaignTask(
                campaign_id=camp.id,
                task_name=p["task_name"],
                start_date=date.fromisoformat(p["start_date"]),
                end_date=date.fromisoformat(p["end_date"]),
                duration_days=p["duration_days"],
                priority=p["priority"],
                risk_level=p.get("risk_level", "low"),
                risk_reason=p.get("risk_reason"),
                people_in_charge=p.get("people_in_charge"),
                notes=p.get("reasoning"),
                distrito=p.get("distrito"),
                tipo_df_cp=p.get("tipo_df_cp"),
            )
            self.db.add(task)
            inserted += 1

        session.status = "applied"
        session.applied_at = datetime.utcnow()
        self.db.commit()
        return inserted

    # ----------------- helpers -----------------

    def _build_context(self, campaign: SalesCampaign | None) -> dict[str, Any]:
        locations = self.db.query(Location).filter(Location.is_active.is_(True)).all()
        pr_staff = self.db.query(PRStaff).filter(PRStaff.is_active.is_(True)).all()
        today = date.today()
        return {
            "horizon_start": campaign.start_date if campaign else today,
            "horizon_end": (
                campaign.end_date if campaign and campaign.end_date else today + timedelta(days=30)
            ),
            "locations": [
                {
                    "code": l.code, "br": l.branch.code if l.branch else "",
                    "bc": l.business_center.code if l.business_center else "",
                    "distrito": l.distrito, "tipo_df_cp": l.tipo_df_cp,
                    "fecha_alta_traffico": l.fecha_alta_traffico,
                    "prioridad": l.prioridad,
                    "latitud": float(l.latitud) if l.latitud else None,
                    "longitud": float(l.longitud) if l.longitud else None,
                    "meta_prepago": l.meta_prepago, "meta_postpago": l.meta_postpago,
                    "meta_bipay": l.meta_bipay, "meta_tv360": l.meta_tv360,
                    "meta_mnp": l.meta_mnp,
                    "gasto_comida": float(l.gasto_comida or 0),
                    "gasto_hotel": float(l.gasto_hotel or 0),
                    "gasto_movilidad": float(l.gasto_movilidad or 0),
                    "gasto_renta_local": float(l.gasto_renta_local or 0),
                    "merch_boligrafo": l.merch_boligrafo, "merch_taza": l.merch_taza,
                    "merch_llavero": l.merch_llavero, "merch_papin": l.merch_papin,
                    "merch_sombrero": l.merch_sombrero,
                }
                for l in locations
            ],
            "pr_staff": [
                {
                    "pr_code": p.pr_code,
                    "bc": p.business_center.code if p.business_center else "",
                    "br": p.branch.code if p.branch else "",
                    "tipo_pr": p.tipo_pr, "kpi_trabajo": p.kpi_trabajo,
                    "cantidad_dia_trabajo": p.cantidad_dia_trabajo,
                    "is_active": p.is_active,
                }
                for p in pr_staff
            ],
        }


# ============================================================
# Factory
# ============================================================

def get_provider() -> LLMProvider:
    name = os.environ.get("LLM_PROVIDER", "stub").lower()
    if name == "stub":
        return StubProvider()
    # Future: OpenAIProvider(), AnthropicProvider() if env keys present
    return StubProvider()
