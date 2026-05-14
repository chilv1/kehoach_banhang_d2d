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

## 3. Data Domain Glossary

| Term | Meaning |
|---|---|
| **BR** | Branch (vd. LI3BR = Lima zona 3) |
| **BC** | Business Center (vd. LI3BC12) |
| **Distrito** | District inside Lima |
| **Code Ubicacion** | Sale point code (CP01, CP82…) |
| **Tipo DF/CP** | Type of sales spot (DF Fijo, BTS Upgrade, Mercado, Rural, …) |
| **Horario traffico** | Traffic time window (vd. 08:00-16:00) |
| **Fecha Alta Traffico** | Day-of-week or category when traffic peaks |
| **Prioridad** | 1 = highest, 4 = lowest |
| **PR Code** | Promoter staff identifier (vd. LI3PR10116) |
| **Grupo** | Team of PRs (Grupo 1, Grupo 2, …) |
| **KPI Trabajo** | Contracted minimum work days/month per PR |
| **Cantidad Día Trabajo** | Allocated/available work days |
| **Meta Activation** | Activation target |
| **Meta MNP** | Mobile Number Portability target |
| **Meta TV360** | TV360 target |
| **Bipay** | Digital wallet metric |
| **Campaña OK** | Final review status (OK / NO OK) |

## 4. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Browser (Next.js SPA)                           │
│   ┌───────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────────┐  │
│   │ SalesGantt    │  │ FilterBar     │  │ AI Command   │  │ MapView  │  │
│   │ (Canvas/SVG)  │  │ Grouping      │  │ Bar (Copilot)│  │ (Leaflet)│  │
│   └───────┬───────┘  └───────┬───────┘  └──────┬───────┘  └────┬─────┘  │
│           └──────────────────┴──────────────────┴───────────────┘        │
│                                       │                                   │
│                              TanStack Query / Zustand                     │
└────────────────────────────────────────┬─────────────────────────────────┘
                                         │ HTTPS / JSON
┌────────────────────────────────────────┴─────────────────────────────────┐
│                          FastAPI Backend                                  │
│   ┌────────────┐  ┌────────────┐  ┌─────────────┐  ┌──────────────┐     │
│   │ /imports/* │  │ /campaigns │  │ /tasks/*    │  │ /ai/*        │     │
│   │ /gantt/*   │  │ /dashboard │  │ /map/*      │  │ /exports/*   │     │
│   └─────┬──────┘  └─────┬──────┘  └──────┬──────┘  └──────┬───────┘     │
│         └────────────────┴───────────────┴────────────────┘              │
│                          │                                                │
│   ┌──────────────────────┼───────────────────────────────────────┐       │
│   │ services/            │                                       │       │
│   │  excel_import.py     │  ai_planner.py        scheduler.py    │       │
│   │  validator.py        │  constraint_solver.py  cost.py        │       │
│   │  route_optimizer.py  │  audit.py              variance.py    │       │
│   └──────────────────────┼───────────────────────────────────────┘       │
└────────────────────────────────────────┬─────────────────────────────────┘
                                         │
       ┌─────────────────┬───────────────┼──────────────────┬──────────┐
       │                 │               │                  │          │
   ┌───┴──────┐    ┌─────┴────┐   ┌──────┴──────┐    ┌──────┴────┐  ┌──┴─────┐
   │ Postgres │    │ Redis    │   │ MinIO       │    │ RQ Worker │  │ LLM    │
   │ (data)   │    │ (queue+  │   │ (raw xlsx)  │    │ (import+  │  │ (OAI/  │
   │          │    │  cache)  │   │             │    │  ai jobs) │  │ Claude)│
   └──────────┘    └──────────┘   └─────────────┘    └───────────┘  └────────┘
```

## 5. Module Boundaries

```
backend/app/
├── sales_planner/                    ← NEW MODULE (this turn)
│   ├── models/                       SQLAlchemy ORM
│   ├── schemas/                      Pydantic IO contracts
│   ├── services/
│   │   ├── excel_import.py           Parses Campana Plan.xlsx (4 sheets)
│   │   ├── validator.py              Business-rule validation
│   │   ├── ai_planner.py             /goal /optimize /risk /recover /simulate /explain
│   │   ├── constraint_solver.py      OR-Tools CP-SAT wrapper
│   │   ├── route_optimizer.py        Lat/Lng cluster for daily route
│   │   ├── audit.py                  Audit log writes
│   │   └── permission.py             RBAC checks
│   └── routers/
│       ├── imports_router.py
│       ├── sales_router.py
│       ├── ai_router.py
│       ├── dashboard_router.py
│       ├── map_router.py
│       └── exports_router.py
├── services/                         (existing — CPM, EVM, leveling reused)
└── routers/                          (existing — auth reused)

frontend/src/
├── pages/SalesPlannerPage.tsx        ← NEW (this turn)
├── components/
│   ├── SalesGantt/                   Canvas/SVG Gantt (Phase 2 custom)
│   ├── AICommandBar/                 Copilot-style /goal command bar
│   ├── SalesFilterBar/               BR / BC / Distrito / Tipo / Status / Priority filters
│   ├── MapView/                      Leaflet
│   ├── DashboardView/                KPI cards + charts
│   ├── KPIPanel/
│   └── AIReasoningPanel/
└── lib/
    ├── ai-schema.ts                  TS types matching AI JSON schema
    └── gantt-utils.ts
```

## 6. Out-of-scope for this iteration

- Real LLM integration (stub returns deterministic plan; provider abstraction in place).
- Full OR-Tools CP-SAT (skeleton + simple greedy heuristic; CP-SAT in Phase 5).
- Custom Canvas/SVG Gantt (uses `gantt-task-react` adapter as Phase 1; custom in Phase 2).
- Mobile responsive design (desktop-first; mobile in Phase 6).
- Multi-tenant SaaS (single-tenant only; multi-tenant in Phase 7).

## 7. SLA Targets

| Metric | Target |
|---|---|
| Gantt initial render with 10k tasks | < 1.5s |
| Drag-drop response | < 100ms |
| Excel import 10k rows | < 30s (background) |
| `/goal` AI response | < 8s (P95) |
| API p99 latency | < 500ms |
| Uptime | 99.5% (single-region) |

## 8. Phase Gate Summary

| Phase | Output | Owner | Eta |
|---|---|---|---|
| 1 | Excel import + DB schema + basic Gantt | BE + Data | 2 wk |
| 2 | Custom MS-Project-like Gantt (Canvas) | FE + UX | 3-4 wk |
| 3 | AI Planner (6 modes) + LLM integration | AI | 3 wk |
| 4 | Dashboard + Map + Export | FE + BE | 2 wk |
| 5 | OR-Tools constraint solver + What-if | AI + BE | 2 wk |
| 6 | QA, perf, security, Docker, CI/CD | QA + DevOps | 2 wk |
| **Total** | — | — | **~3-4 months full-time** |
