# ProjectWeb — MS Project clone (web app)

Web-based clone of Microsoft Project Desktop, targeting ~90% feature parity.

```
[ React + gantt-task-react ]  ↔  [ FastAPI + SQLAlchemy + SQLite ]
                                  ↕
                             [ CPM Scheduling Engine ]
```

## ✅ 8 Phases complete

| Phase | Feature | Status |
|---|---|---|
| **0** | Foundation: FastAPI + React + SQLAlchemy skeleton | ✅ DONE |
| **1** | Hierarchy: WBS + indent/outdent + auto rollup | ✅ DONE |
| **2** | CPM engine: 4 link types + lag + 8 constraints + critical path | ✅ DONE |
| **3** | Resources: WORK/MATERIAL/COST + assignment + cost rollup | ✅ DONE |
| **4** | Baseline + Variance tracking | ✅ DONE |
| **5** | Resource leveling: auto-resolve over-allocation | ✅ DONE |
| **6** | EVM: BCWS/BCWP/ACWP + CV/SV + CPI/SPI + EAC/ETC/VAC/TCPI | ✅ DONE |
| **7** | Project XML import/export | ✅ DONE |
| **8** | Auth: JWT (HS256 stdlib) + pbkdf2 password hashing | ✅ DONE |

**47 API endpoints**. **Full UI** for all 8 phases.

## 🚀 Setup

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m app.seed.demo                  # creates demo project
uvicorn app.main:app --reload --port 8500
# Swagger: http://127.0.0.1:8500/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

## 🏗️ Architecture

```
backend/app/
  main.py             FastAPI entry
  config.py           Settings (DB URL, CORS, work hours)
  db/session.py       SQLAlchemy + Base
  models/             8 ORM models (Project, Task, Dependency, Resource,
                       Assignment, Calendar, Baseline, User)
  schemas/common.py   Pydantic schemas
  services/
    working_time.py   Calendar-aware datetime math
    scheduler.py      CPM forward/backward pass + critical path
    cost.py           Cost rollup
    outline.py        WBS / indent / outdent
    variance.py       Baseline variance
    leveling.py       Resource leveling (greedy)
    evm.py            Earned Value Management
    xml_io.py         Project XML import/export
    auth.py           JWT (stdlib HS256) + pbkdf2
  routers/
    projects.py       CRUD + schedule
    advanced.py       Phase 1, 3, 4, 5, 6, 7 endpoints
    auth.py           Phase 8 register/login/me
  seed/demo.py        Sample project (Xây nhà)

frontend/src/
  App.tsx             React Router + AuthGuard
  api/client.ts       Axios client
  pages/
    LoginPage.tsx
    ProjectListPage.tsx
    ProjectViewPage.tsx (Gantt + Grid)
    ResourcesPage.tsx
    TrackingPage.tsx
    LevelingPage.tsx
    EvmPage.tsx
  components/TaskGrid/TaskGrid.tsx
```

## 📐 Scheduler conventions

- Duration unit: **working hours** (1 day = 8h with Standard Calendar).
- Standard Calendar: Mon–Fri, 08:00–12:00 + 13:00–17:00.
- Lag: positive = delay, negative = lead (overlap).
- Summary tasks excluded from CPM; their dates are rolled up from children.
- Milestones: duration = 0; start = finish.
- Critical threshold: total_slack ≤ 0.5h.

## 🧪 Verified on demo project ("Xây nhà")

8 tasks, 9 dependencies (FS + SS with lag), 4 resources, 7 assignments.

```
Schedule result:
  project_start  = 2026-05-04 08:00
  project_finish = 2026-06-25 08:00
  n_critical     = 6 / 8 tasks
  Total cost     = $17,360
```

All 8 phases verified via Python script and HTTP curl tests.

## 📁 Legacy

Previous Streamlit campaign manager preserved under `legacy/streamlit/`.
Mockups under `mockup/` show static HTML walkthroughs for both:
- `mockup/index.html` — campaign manager (D2D sales planning)
- `mockup/projectweb/index.html` — ProjectWeb (MS Project clone)
