# AI Planner — Specification

## 1. Slash commands

| Command | Inputs | Output |
|---|---|---|
| `/goal` | objective text + optional `{region, days, budget, weight_*}` | Full draft plan |
| `/optimize` | existing plan id | Reshuffled plan |
| `/risk` | plan id, status_date | Risk list with severity |
| `/recover` | plan id, BC id, target % | Catch-up plan |
| `/simulate` | plan id + scenario dict | Projected KPIs |
| `/explain` | task id | Reasoning trace |
| `/daily` | date | Today's recommendation per group |

## 2. Constraint set

| Code | Rule |
|---|---|
| C1 | A PR cannot be assigned to 2+ tasks on the same calendar day. |
| C2 | Sum of PR-day units per resource ≤ `cantidad_dia_trabajo`. |
| C3 | A Grupo cannot exceed its member count for the day. |
| C4 | Task day-of-week must match `fecha_alta_traffico` unless flagged `relaxed`. |
| C5 | Task duration in working days ≥ ceil(Meta / per-day capacity). |
| C6 | Budget per task ≤ resource_cost + merchandising_cost + travel_cost + 20% buffer. |
| C7 | Priority 1 tasks scheduled before priority 2+. |
| C8 | If two tasks share `code_ubicacion` and date → conflict. |
| C9 | Locations > 30 km apart cannot be assigned to same PR on same day. |
| C10 | LLM-generated dates must satisfy `start_date ≤ end_date` and end ≤ horizon. |

Soft constraints become objective terms:

```
minimize  α·unmet_meta + β·overallocation + γ·travel_km + δ·priority_violations
where α=10  β=5  γ=1  δ=8  (defaults; tunable)
```

## 3. JSON Schema (strict, validated server-side)

Schema is implemented as the Pydantic class `AIPlanResponse` in
`backend/app/sales_planner/schemas/sales_schemas.py`.  See that file for the
strictly-typed source of truth.

## 4. Lifecycle of an AI session

```
1. POST /api/ai/{command}          → AIPlanningSession created (status=running)
2. Worker invokes provider         (async)
3. Validator checks JSON schema    → status=validated | rejected
4. Constraint checker              → status=constraint_ok | violations
5. Diff vs current plan            → changes_preview filled in
6. Response served, awaits user    → status=awaiting_approval
7. POST /api/ai/apply-plan/{id}    → status=applied | declined
8. Audit log written               every step
```

## 5. Failure modes

| Failure | Behaviour |
|---|---|
| LLM returns invalid JSON | Retry x2; if still bad → return validator error to UI; status=rejected |
| Constraint violation | Show list with task ids + rule code; offer Auto-fix or Discard |
| LLM times out | Background job continues; UI polls every 2s; cancel button |
| User declines plan | Session archived; no DB write; audit log entry |
