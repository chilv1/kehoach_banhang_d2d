# AI Sales Campaign Planner — Product Backlog

Notation: `[Pn]` = phase number · `[SP=x]` = story points · `(role)` = owner

## Epic 1 — Excel Import & Master Data  [P1]

| ID | User Story | AC | SP |
|---|---|---|---|
| US-001 | As a Planner, I upload `Campana Plan.xlsx` and see a preview of detected sheets and rows. | (1) 4 sheets detected; (2) preview shows first 50 rows; (3) bad rows highlighted | 5 |
| US-002 | As a Planner, I map ambiguous columns to the canonical schema. | (1) for each unknown column system suggests target; (2) user can override; (3) mapping saved per file | 3 |
| US-003 | As a Planner, I commit the import; data lands in normalised tables. | (1) transactional; (2) duplicate detection on (BR,BC,Code Ubicacion); (3) audit log row created | 5 |
| US-004 | As an Admin, I see the raw uploaded file is retained in object storage. | (1) MinIO bucket; (2) SHA256 of payload stored; (3) downloadable by Admin only | 2 |
| US-005 | Excel serial dates convert correctly to ISO. | (1) day 1 = 1899-12-31 + offset (Excel quirk); (2) Sat/Sun preserved; (3) timezones UTC | 2 |
| US-006 | Daily-allocation columns (one per date) flatten into `sales_daily_plan`. | (1) header parsed as date; (2) value = work units 0–1; (3) preserves grupo | 5 |

## Epic 2 — MS Project Gantt UI  [P2]

| ID | User Story | SP |
|---|---|---|
| US-010 | Left grid columns: WBS, Name, BR, BC, Distrito, Code Ubicacion, People InCharge, Grupo/PR, Start, Finish, Duration, %, Status, Priority, KPI, Budget, Risk, Notes. | 5 |
| US-011 | Right timeline: calendar header day/week/month/quarter; weekend shading; today line. | 5 |
| US-012 | Task bar drag = shift dates; bar resize = duration change; commit via PATCH. | 8 |
| US-013 | Dependency lines (FS/SS/FF/SF) drawn between bars; create by drag-from-edge. | 8 |
| US-014 | Baseline overlay (faded bar) vs current (solid bar); toggle from toolbar. | 5 |
| US-015 | Hierarchy collapse/expand; summary bars roll up children. | 5 |
| US-016 | Multi-select + bulk edit (status, priority, group). | 5 |
| US-017 | Right-click context: Add / Delete / Duplicate / Split / Link / Unlink / Assign. | 5 |
| US-018 | Mini-map timeline overview at bottom of Gantt. | 3 |
| US-019 | Virtualised grid + timeline for 10k tasks (< 1.5s render). | 8 |
| US-020 | Status colors: Planned blue / In Progress amber / Completed green / Delayed red / NO OK red / At Risk orange / Digital purple / High prio yellow. | 2 |
| US-021 | Milestone diamond markers; critical path highlighted red. | 3 |

## Epic 3 — AI Planner  [P3]

| ID | User Story | SP |
|---|---|---|
| US-030 | AI Command Bar accepts `/goal <natural language>` and surfaces structured plan. | 5 |
| US-031 | `/goal` returns plan validated against JSON schema before render. | 3 |
| US-032 | `/optimize` reshuffles existing plan respecting constraints. | 5 |
| US-033 | `/risk` lists campaigns at risk of missing meta with reasoning. | 3 |
| US-034 | `/recover` builds catch-up plan for under-performing BC. | 5 |
| US-035 | `/simulate` what-if (add PR / extend days / change budget) returns delta. | 5 |
| US-036 | `/explain` returns reasoning for why a task was scheduled the way it is. | 3 |
| US-037 | `/daily` lists today's recommended action items per PR/group. | 3 |
| US-038 | Apply Plan button shows diff (changes_preview) before writing to DB. | 5 |
| US-039 | All AI runs persisted in `sales_ai_planning_sessions` for audit. | 3 |
| US-040 | Plan respects: PR capacity, group conflict, prioridad order, fecha alta traffico, horario, budget, daily target attainability. | 8 |

## Epic 4 — Dashboard + Map  [P4]

| ID | User Story | SP |
|---|---|---|
| US-050 | Dashboard summary mirrors Sheet "General" layout. | 5 |
| US-051 | Per-BC table: Meta / Resultado / % Result (Campana, Mobile Activation, MNP, Digital Bipay, TV360). | 5 |
| US-052 | PR utilisation bar chart with overload flag. | 3 |
| US-053 | Budget planned vs actual stacked bar by BC. | 3 |
| US-054 | Risk heatmap (status × BC). | 3 |
| US-055 | Map view shows locations with marker color = status; cluster on zoom-out. | 5 |
| US-056 | Map filter sidebar (BR/BC/Distrito/Status/Priority/Tipo DF/CP). | 3 |
| US-057 | AI route-optimize: cluster nearby CPs for the same day. | 5 |

## Epic 5 — Optimisation Engine  [P5]

| ID | User Story | SP |
|---|---|---|
| US-070 | Constraint solver using OR-Tools CP-SAT models PR ↔ task assignment. | 13 |
| US-071 | Variables: assignment binary, start time int, used PR day units. | 5 |
| US-072 | Objective = α·(unmet meta) + β·(over-allocation) + γ·(travel cost) + δ·(priority skip). | 5 |
| US-073 | Solver runs in worker; result streamed back via websocket. | 5 |
| US-074 | Result hydrated into draft tasks; user approves to commit. | 3 |

## Epic 6 — Export, Tests, DevOps  [P6]

| ID | User Story | SP |
|---|---|---|
| US-080 | Export back to Excel matching original layout. | 5 |
| US-081 | Export PDF / PNG of Gantt. | 5 |
| US-082 | Docker Compose: web + api + postgres + redis + minio + worker. | 3 |
| US-083 | Migrations via Alembic; seed via uploaded file. | 3 |
| US-084 | Pytest backend coverage ≥ 70%. | 5 |
| US-085 | Vitest + Playwright e2e coverage of critical flows. | 5 |
| US-086 | GitHub Actions CI: lint, type-check, test, build. | 3 |
| US-087 | OpenTelemetry instrumentation; logs ship to stdout (loki-ready). | 3 |

## Definition of Done (story-level)

- Code merged to `main` via PR with ≥1 reviewer.
- Pytest + Vitest passing in CI.
- New endpoints documented in OpenAPI auto-spec.
- Audit log entry created for any data mutation.
- Permission check by role on every mutating endpoint.
- Frontend a11y: focusable controls, ARIA labels on Gantt cells.
- Loading + error states for every async UI.
