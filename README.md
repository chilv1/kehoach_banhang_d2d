# ProjectWeb — MS Project clone (web app)

Web-based clone của Microsoft Project, mục tiêu **90% parity** với MS Project Desktop.

```
[ React + DHTMLX/gantt-task-react ]  ←→  [ FastAPI + SQLAlchemy + SQLite/Postgres ]
                                            ↕
                                       [ CPM Scheduling Engine ]
```

## ✅ Đã làm (v0.1)

### Backend
- 7 SQLAlchemy models: `Project`, `Task` (đầy đủ ES/EF/LS/LF/slack/critical/constraint/% complete), `TaskDependency` (4 link type FS/SS/FF/SF + lag/lead), `Resource` (Work/Material/Cost), `Assignment`, `Calendar` + `WorkingTime`, `Baseline` + `BaselineTask`.
- **CPM Scheduling Engine** (`app/services/scheduler.py`):
  - Forward pass (Early Start / Early Finish)
  - Backward pass (Late Start / Late Finish)
  - Total slack + Free slack
  - Critical path detection
  - 4 link types (FS/SS/FF/SF) với lag/lead
  - 8 constraint types (ASAP, ALAP, MSO, MFO, SNET, SNLT, FNET, FNLT)
  - Calendar-aware working time (`app/services/working_time.py`)
  - Cycle detection
  - Summary task rollup
- 24 REST API endpoints (FastAPI): CRUD đầy đủ + `/schedule` để chạy CPM.
- Seed demo "Xây nhà" với 8 task + 9 dep + 4 resource → verified scheduler đúng.

### Frontend
- Vite + React 18 + TypeScript + React Query + React Router.
- Trang `ProjectListPage`: tạo / xoá / mở project.
- Trang `ProjectViewPage`: tab **Gantt** (gantt-task-react với drag/drop ngày + dependency arrows + critical path đỏ) và tab **Grid** (MS Project-style task list với inline edit).
- Trang `ResourcesPage`: CRUD resource (Work/Material/Cost).
- API client (`src/api/client.ts`) gọi backend qua axios + Vite proxy.

## 🚀 Setup

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m app.seed.demo                  # tạo project demo
uvicorn app.main:app --reload --port 8500
```
→ Swagger: http://127.0.0.1:8500/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
→ http://localhost:5173

## 🗺️ Roadmap

| Phase | Tính năng | Trạng thái |
|---|---|---|
| **0** | Foundation: schema + skeleton FE/BE | ✅ DONE |
| **1** | MVP Gantt: hierarchy + FS dep + drag/drop + auto reschedule | 🟡 ~70% (chưa hierarchy drag) |
| **2** | CPM engine: 4 link types + lag + constraints + critical path | ✅ DONE |
| **3** | Resources: WORK/MATERIAL/COST + assignment + cost calc | 🟡 ~50% (chưa cost rollup) |
| **4** | Tracking: baseline + % complete + Tracking Gantt + variance | 🟡 ~30% (model có, UI chưa) |
| **5** | Resource leveling: auto-resolve over-allocation | ❌ chưa |
| **6** | EVM: BCWS/BCWP/ACWP + CPI/SPI + reports | ❌ chưa |
| **7** | Import/Export: Project XML | ❌ chưa |
| **8** | Polish: auth, comments, permissions, multi-project | ❌ chưa |

## 🏗️ Kiến trúc

```
kehoach_banhang_d2d/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry
│   │   ├── config.py
│   │   ├── db/session.py        # SQLAlchemy + Base
│   │   ├── models/              # 7 ORM models
│   │   │   ├── project.py
│   │   │   ├── task.py          # ES/EF/LS/LF/slack/critical/8 constraints
│   │   │   ├── dependency.py    # FS/SS/FF/SF + lag
│   │   │   ├── resource.py      # WORK/MATERIAL/COST
│   │   │   ├── assignment.py
│   │   │   ├── calendar.py
│   │   │   └── baseline.py
│   │   ├── schemas/common.py    # Pydantic
│   │   ├── services/
│   │   │   ├── working_time.py  # Calendar math
│   │   │   └── scheduler.py     # CPM engine
│   │   ├── routers/projects.py  # 24 endpoints
│   │   └── seed/demo.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── api/client.ts        # axios wrapper
│   │   ├── types/index.ts       # TypeScript types
│   │   ├── pages/
│   │   │   ├── ProjectListPage.tsx
│   │   │   ├── ProjectViewPage.tsx
│   │   │   └── ResourcesPage.tsx
│   │   ├── components/
│   │   │   └── TaskGrid/        # MS Project-style grid
│   │   └── styles/app.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── index.html
├── legacy/streamlit/            # phiên bản cũ (Streamlit campaign mgmt)
└── mockup/                       # static HTML mockup
```

## 📐 Quy ước scheduler

- **Duration đơn vị giờ làm việc** (1 ngày = 8h theo Standard Calendar). Lag cũng tính bằng giờ.
- Lag dương = delay, âm = lead (overlap).
- Calendar Standard: Mon–Fri, 08:00–12:00 + 13:00–17:00.
- Summary task có flag `is_summary=true` → loại khỏi CPM, rollup từ children.
- Milestone (`is_milestone=true`) → duration coerce về 0, start = finish.
- Critical task ngưỡng slack ≤ 0.5h.

## 🧪 Test

```bash
# Backend
cd backend
rm -f projectweb.db
python3 -m app.seed.demo
python3 -c "
import sys; sys.path.insert(0,'.')
from app.db.session import SessionLocal
from app.models import Project
from app.services.scheduler import schedule_project
db = SessionLocal()
res = schedule_project(db, db.query(Project).first().id)
print(res)
"
```

Expected output:
```
{'n_tasks': 8, 'n_critical': 6, 'project_finish': '2026-06-25T08:00:00', ...}
```

## 📚 Legacy

Phiên bản Streamlit cũ (quản lý campaign D2D) đã chuyển vào `legacy/streamlit/`. Vẫn chạy được:
```bash
cd legacy/streamlit
pip install -r requirements.txt
streamlit run app.py
```
