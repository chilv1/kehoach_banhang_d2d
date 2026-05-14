# AI Sales Campaign Planner — Technical Specification

**Version**: 1.0
**Status**: Foundation laid; implementation in progress
**Owner**: Multi-agent product team (PM / SA / BE / FE / Data / AI / QA / UX)

## 1. Product Overview

Web application that ingests a `Campana Plan.xlsx` file, normalises it into a relational
database, and presents an MS-Project-style Gantt board enriched with sales KPIs.
An **AI Planner** module consumes business goals (vd. `/goal …`) and produces a
constraint-checked plan that can be reviewed, edited and applied.

### 1.1 Primary users

| Role | Responsibility |
|---|---|
| **Admin** | Configure branches, BCs, master data, user accounts |
| **Planner** | Run `/goal`, create campaigns, edit Gantt, approve AI plans |
| **Supervisor** | Approve/decline plans, manage PR allocation, monitor risk |
| **Viewer** | Read-only dashboard, Gantt, map |

### 1.2 Primary use cases

1. Upload Excel `Campana Plan.xlsx` → preview → commit.
2. Generate a 30-day campaign plan with `/goal …` and apply to the Gantt.
3. Drag-drop & resize tasks on the Gantt; updates persisted with audit log.
4. Drill into a BC, watch Meta vs Resultado per metric.
5. View campaign sites on map; AI suggests geographic routing.
6. Export back to Excel matching the original column layout.

## 2. Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | Next.js 14 + TypeScript + Tailwind + shadcn/ui | RSC-ready, ecosystem mature |
| State | Zustand + TanStack Query | Local UI + server sync |
| Tables | TanStack Table (virtualised) | 10k+ rows performant |
| Gantt | Custom Canvas/SVG (Phase 2); `gantt-task-react` placeholder Phase 1 | MS Project parity requires custom canvas |
| Maps | Leaflet + OpenStreetMap | OSS, no API key needed |
| Charts | Recharts | composable React API |
| Backend | FastAPI (Python 3.11) | reuses existing `backend/app/` foundation |
| ORM | SQLAlchemy 2.0 + Alembic | mature, async-capable |
| Database | PostgreSQL 16 (SQLite in dev/test) | recursive CTEs for WBS, JSONB for AI payloads |
| Queue | Redis + RQ (or Celery) | excel import + AI generation are async |
| Object store | MinIO (S3-compatible) | raw Excel uploads + exports |
| AI provider | LLM-agnostic abstraction (OpenAI / Anthropic / Local) | swap models, retry, fallback |
| Optimizer | Google OR-Tools CP-SAT | constraint-based scheduling |
| Auth | JWT HS256 (existing) | inherits `backend/app/services/auth.py` |
| Container | Docker Compose | local dev, single-node deploy |

## 3. Module Boundaries

```
backend/app/
├── sales_planner/                    ← NEW MODULE
│   ├── models/                       SQLAlchemy ORM (18 entities)
│   ├── schemas/                      Pydantic IO contracts
│   ├── services/
│   │   ├── excel_import.py           Parses Campana Plan.xlsx (4 sheets)
│   │   ├── ai_planner.py             /goal /optimize /risk /recover /simulate /explain /daily
│   │   ├── constraint_solver.py      C1..C10 validation + haversine
│   │   └── audit.py                  Audit log writes
│   └── routers/
│       ├── imports_router.py
│       ├── sales_router.py
│       ├── ai_router.py
│       ├── dashboard_router.py
│       ├── map_router.py
│       └── exports_router.py

frontend/src/
├── pages/SalesPlannerPage.tsx
├── components/
│   ├── SalesGantt/                   Canvas/SVG Gantt (Phase 2 custom)
│   ├── AICommandBar/                 Copilot-style /goal command bar
│   ├── SalesFilterBar/               BR / BC / Distrito / Tipo / Status / Priority filters
│   ├── MapView/                      Leaflet
│   └── DashboardView/                KPI cards + charts
└── lib/
    ├── ai-schema.ts                  TS types matching AI JSON schema
    └── gantt-utils.ts
```

## 4. SLA Targets

| Metric | Target |
|---|---|
| Gantt initial render with 10k tasks | < 1.5s |
| Drag-drop response | < 100ms |
| Excel import 10k rows | < 30s (background) |
| `/goal` AI response | < 8s (P95) |
| API p99 latency | < 500ms |
| Uptime | 99.5% (single-region) |

## 5. Phase Gate Summary

| Phase | Output | Owner | Eta |
|---|---|---|---|
| 1 | Excel import + DB schema + basic Gantt | BE + Data | 2 wk |
| 2 | Custom MS-Project-like Gantt (Canvas) | FE + UX | 3-4 wk |
| 3 | AI Planner (6 modes) + LLM integration | AI | 3 wk |
| 4 | Dashboard + Map + Export | FE + BE | 2 wk |
| 5 | OR-Tools constraint solver + What-if | AI + BE | 2 wk |
| 6 | QA, perf, security, Docker, CI/CD | QA + DevOps | 2 wk |
| **Total** | — | — | **~3-4 months full-time** |

See also: `docs/sales-planner/BACKLOG.md` (87 user stories) and
`docs/sales-planner/AI_PLANNER_SPEC.md` (JSON schema + hard constraints).
