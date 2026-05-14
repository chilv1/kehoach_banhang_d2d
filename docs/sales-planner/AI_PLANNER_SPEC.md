# AI Planner — Specification

## 1. Slash command surface

| Command | Inputs (NL + structured) | Output |
|---|---|---|
| `/goal` | objective text + optional `{region, days, budget, weight_*}` | Full draft plan |
| `/optimize` | existing plan id | Reshuffled plan, deltas highlighted |
| `/risk` | plan id, status_date | Risk list with severity + cause |
| `/recover` | plan id, BC id, target % | Catch-up plan |
| `/simulate` | plan id + scenario dict (vd. `{add_pr: 5}`) | Projected KPIs |
| `/explain` | task id | Reasoning trace |
| `/daily` | date | Today's recommendation per group |

## 2. JSON Schema (strict, validated server-side)

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AISalesPlan",
  "type": "object",
  "required": ["summary", "campaign_plan", "requires_user_approval"],
  "properties": {
    "summary":            { "type": "string", "maxLength": 4000 },
    "planning_assumptions": { "type": "array", "items": { "type": "string" } },
    "campaign_plan": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["task_name", "code_ubicacion", "br", "bc",
                     "start_date", "end_date", "duration_days", "priority"],
        "properties": {
          "task_name":          { "type": "string", "minLength": 3 },
          "code_ubicacion":     { "type": "string", "pattern": "^CP\\d+$" },
          "br":                 { "type": "string" },
          "bc":                 { "type": "string" },
          "distrito":           { "type": "string" },
          "tipo_df_cp":         { "type": "string" },
          "people_in_charge":   { "type": "string" },
          "grupo_code_pr":      { "type": "string" },
          "start_date":         { "type": "string", "format": "date" },
          "end_date":           { "type": "string", "format": "date" },
          "duration_days":      { "type": "integer", "minimum": 1, "maximum": 365 },
          "priority":           { "type": "integer", "minimum": 1, "maximum": 10 },
          "target_activation":  { "type": "integer", "minimum": 0 },
          "target_mnp":         { "type": "integer", "minimum": 0 },
          "target_tv360":       { "type": "integer", "minimum": 0 },
          "target_bipay":       { "type": "integer", "minimum": 0 },
          "planned_cost":       { "type": "number", "minimum": 0 },
          "merchandising": {
            "type": "object",
            "properties": {
              "boligrafo": { "type": "integer", "minimum": 0 },
              "taza":      { "type": "integer", "minimum": 0 },
              "llavero":   { "type": "integer", "minimum": 0 },
              "papin":     { "type": "integer", "minimum": 0 },
              "sombrero":  { "type": "integer", "minimum": 0 }
            }
          },
          "risk_level":  { "type": "string", "enum": ["low", "medium", "high"] },
          "risk_reason": { "type": "string" },
          "checklist":   { "type": "array", "items": { "type": "string" } },
          "reasoning":   { "type": "string" }
        }
      }
    },
    "resource_allocation": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["pr_code", "days"],
        "properties": {
          "pr_code": { "type": "string" },
          "days":    { "type": "integer", "minimum": 0 },
          "tasks":   { "type": "array", "items": { "type": "integer" } }
        }
      }
    },
    "risks":           { "type": "array", "items": { "type": "object" } },
    "warnings":        { "type": "array", "items": { "type": "string" } },
    "recommendations": { "type": "array", "items": { "type": "string" } },
    "changes_preview": { "type": "array", "items": { "type": "object" } },
    "requires_user_approval": { "type": "const": true }
  }
}
```

## 3. Constraint set (hard)

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

## 4. Prompt skeleton (LLM)

```
SYSTEM:
You are an AI sales-campaign planner for a telecom operator.
You receive (a) a goal text from the user, (b) master data describing locations,
PR staff, business centers, current plan, and history. Produce ONLY valid JSON
matching the AISalesPlan schema below. Do not add prose, markdown, or comments.
Constraints C1..C10 are hard; objective terms guide trade-offs.

USER:
{{goal_text}}

CONTEXT (compact JSON):
- horizon_start / horizon_end
- branches[], business_centers[], locations[], pr_staff[], pr_groups[]
- existing_plan[]
- recent_results[]
```

The provider abstraction supports OpenAI, Anthropic, Gemini, and local stubs.
The first deliverable ships with a deterministic **rules-based stub planner**
that yields valid JSON, allowing the rest of the pipeline (validation, diff,
apply) to be exercised without LLM bills.

## 5. Lifecycle of an AI session

```
1. POST /api/ai/{command}             → AIPlanningSession created (status=running)
2. Worker invokes provider            (async)
3. Validator checks JSON schema       → status=validated | rejected
4. Constraint checker                 → status=constraint_ok | violations
5. Diff vs current plan               → changes_preview filled in
6. Response served, awaits user       → status=awaiting_approval
7. POST /api/ai/apply-plan/{id}       → status=applied | declined
8. Audit log written                  every step
```

## 6. UI surfaces

- **AI Command Bar** (top toolbar): textarea + send; slash-command suggestions.
- **AI Reasoning Panel** (right-side drawer): summary + reasoning per task.
- **Diff modal**: list of added/changed/removed tasks; Apply / Discard buttons.
- **Toast**: non-blocking notifications when async session finishes.

## 7. Failure modes

| Failure | Behaviour |
|---|---|
| LLM returns invalid JSON | Retry x2; if still bad → return validator error to UI; status=rejected |
| Constraint violation | Show list with task ids + rule code; offer Auto-fix or Discard |
| LLM times out | Background job continues; UI polls every 2s; cancel button |
| User declines plan | Session archived; no DB write; audit log entry |
