# ProjectWeb + AI Sales Campaign Planner

Monorepo containing two web applications sharing a FastAPI backend and React
frontend:

1. **ProjectWeb** — a Microsoft Project clone with CPM scheduler, resource
   leveling, EVM, XML I/O and JWT auth.
2. **AI Sales Campaign Planner** — a sales-campaign planner specialised for
   telecom field campaigns. Ingests `Campana Plan.xlsx`, normalises into
   PostgreSQL, exposes 25 REST endpoints, and ships an AI Planner with seven
   slash commands (`/goal /optimize /risk /recover /simulate /explain /daily`).

## Repository layout

```
backend/
  app/
    main.py                       FastAPI entry (72 routes)
    config.py db/ models/ schemas/ services/ routers/   ProjectWeb (Phase 0-8)
    sales_planner/                AI Sales Campaign Planner module
      models/        18 ORM models
      schemas/       Pydantic IO
      services/      excel_import, ai_planner, constraint_solver
      routers/       imports, sales, ai, dashboard, map, exports
  migrations/
    001_sales_planner.sql         20-table PostgreSQL DDL
  Dockerfile
  requirements.txt
frontend/
  src/
    pages/SalesPlannerPage.tsx    MS-Project-style sales planner UI
    components/AICommandBar       Copilot-style slash command bar
    components/SalesFilterBar     BR/BC/Distrito/Tipo/Status filters + grouping
    components/SalesGantt         Gantt (Phase 1 adapter; Phase 2 custom Canvas)
    api/sales-client.ts           Axios client
    lib/ai-schema.ts              TS mirror of AISalesPlan JSON schema
  Dockerfile
docs/sales-planner/
  SPEC.md                         Product spec, tech stack, SLAs, phase gates
  BACKLOG.md                      87 user stories across 6 epics
  AI_PLANNER_SPEC.md              JSON schema, hard constraints C1..C10
tests/backend/
  test_excel_import.py            81 locations + 68 PR + 81 tasks parsed
  test_ai_planner.py              stub provider + constraint C1 enforcement
docker-compose.yml                postgres + redis + minio + api + worker + web
Campana Plan.xlsx                 reference workbook
mockup/                           Static HTML walkthroughs (legacy)
legacy/streamlit/                 First-iteration Streamlit app
```

## Quick start (Docker)

```bash
docker compose up -d            # postgres + redis + minio + api + web
# wait ~10s for postgres healthcheck to pass
docker compose exec api python -m app.seed.demo   # MS Project demo project
# Upload Campana Plan.xlsx via http://localhost:5173/sales-planner
```

## Quick start (native)

```bash
cd backend
pip install -r requirements.txt
python -m app.seed.demo                    # creates MS Project demo
uvicorn app.main:app --reload --port 8500  # http://127.0.0.1:8500/docs

cd ../frontend
npm install
npm run dev                                # http://localhost:5173
```

## Sales Planner workflow

1. **Login** — `POST /api/auth/register` then `/login` (JWT HS256 + pbkdf2).
2. **Import Excel** — drag `Campana Plan.xlsx` into `/sales-planner`.
   The importer parses Ubicacion (locations), PR Grupo (staff + daily
   allocations), Plan CP (tasks + targets + merch) and creates a campaign.
3. **AI Planner** — type a slash command in the AI command bar:
   - `/goal Tạo kế hoạch 30 ngày cho LI3BR, ưu tiên CP prio 1`
   - `/optimize` `/risk` `/recover` `/simulate` `/explain` `/daily`
   - Plan returns as JSON, schema-validated, constraint-checked.
   - Click **Apply** to write tasks to the DB.
4. **Gantt** — drag and resize bars; updates persist via `PATCH /sales/tasks/{id}`.
5. **Dashboard** — per-BC Meta vs Resultado matching Sheet "General".
6. **Map** — Leaflet markers with route-optimize endpoint for geographic
   clustering of same-day campaigns.
7. **Export** — download Excel matching the original column layout.

## AI Planner overview

| Command | Purpose |
|---|---|
| `/goal`     | Generate a fresh plan respecting business goal |
| `/optimize` | Reshuffle existing plan minimising conflicts |
| `/risk`     | Detect campaigns at risk of missing Meta |
| `/recover`  | Build catch-up plan for under-performing BC |
| `/simulate` | What-if scenarios (extra PR, longer days, more budget) |
| `/explain`  | Reasoning trace for a single task |
| `/daily`    | Today's action items per group |

Hard constraints (C1..C10) include PR overlap detection, capacity caps,
group conflicts, traffic-day matching, location duplication, geographic
proximity, priority ordering. See `docs/sales-planner/AI_PLANNER_SPEC.md`.

Provider abstraction supports OpenAI / Anthropic / Local LLMs; the default
`StubProvider` produces deterministic, constraint-valid plans without an LLM
bill so the pipeline (schema validation, diff, apply) is end-to-end testable
in CI.

## ProjectWeb (Phase 0-8)

The existing Microsoft Project clone remains operational:

- 8 ORM models (Project, Task, Dependency, Resource, Assignment, Calendar,
  Baseline, User).
- 24 REST endpoints under `/api/projects`, `/api/tasks`, `/api/dependencies`,
  `/api/resources`, `/api/assignments`, `/api/baselines`, `/api/auth`.
- CPM scheduler with forward/backward pass, 4 link types (FS/SS/FF/SF) +
  lag, 8 constraint types (ASAP/ALAP/MSO/MFO/SNET/SNLT/FNET/FNLT),
  calendar-aware working time math, cycle detection, summary task rollup.
- Resource leveling with greedy auto-delay.
- Earned Value (BAC, BCWS, BCWP, ACWP, CV, SV, CPI, SPI, EAC, ETC, VAC, TCPI).
- Project XML import/export.
- JWT HS256 auth with pbkdf2 password hash (stdlib only, no `cryptography`).

Frontend pages: `/` ProjectList, `/projects/{id}` Gantt + Grid,
`/projects/{id}/resources` Resources, `/tracking` Baseline + Variance,
`/leveling` Resource Leveling, `/evm` Earned Value.

## Tests

```bash
cd tests/backend
python -m pytest -v
```

Smoke suite (4 tests passing): Excel import roundtrip (81 locations,
68 PR, 81 tasks, 3,683 daily plans), AI stub provider response,
C1 constraint enforcement, Excel serial-date conversion.

## Phase roadmap

| Phase | Output |
|---|---|
| 0–8 (ProjectWeb) | ✅ Done — CPM, leveling, EVM, XML, auth |
| Sales Planner Phase 1 | ✅ Foundation — import, AI stub, 25 endpoints, scaffold UI |
| Sales Planner Phase 2 | Custom Canvas Gantt for MS-Project parity |
| Sales Planner Phase 3 | Real LLM integration (OpenAI/Anthropic) |
| Sales Planner Phase 4 | Dashboard view + Leaflet map + AI route-optimize |
| Sales Planner Phase 5 | OR-Tools CP-SAT constraint optimiser |
| Sales Planner Phase 6 | QA, perf, security, full CI/CD |

## License

Proprietary — internal project. See repository owner.
