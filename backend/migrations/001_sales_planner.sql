-- =====================================================================
-- AI Sales Campaign Planner — Schema migration (Phase 1)
-- Target: PostgreSQL 16 (SQLite-compatible fallback for dev/test)
-- Author: Data Engineer (sales-planner team)
-- =====================================================================

-- ---------- Reference / master data ----------

CREATE TABLE IF NOT EXISTS sales_branches (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20)  NOT NULL UNIQUE,           -- vd. LI3BR
    name            VARCHAR(120),
    country         VARCHAR(60)  NOT NULL DEFAULT 'PE',
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_business_centers (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(30)  NOT NULL UNIQUE,           -- vd. LI3BC12
    branch_id       INTEGER      NOT NULL REFERENCES sales_branches(id) ON DELETE CASCADE,
    name            VARCHAR(120),
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_locations (
    id                  SERIAL PRIMARY KEY,
    code                VARCHAR(20) NOT NULL UNIQUE,        -- Code Ubicacion (CP01..)
    branch_id           INTEGER     NOT NULL REFERENCES sales_branches(id),
    business_center_id  INTEGER     NOT NULL REFERENCES sales_business_centers(id),
    departamento        VARCHAR(60),
    distrito            VARCHAR(120),
    tipo_df_cp          VARCHAR(40),                        -- DF Fijo / BTS Upgrade / ...
    horario_traffico    VARCHAR(40),                        -- vd. "08:00 - 16:00"
    fecha_alta_traffico VARCHAR(15),                        -- WEEKDAY / WEEKEND / MONDAY...
    prioridad           SMALLINT    NOT NULL DEFAULT 1,
    latitud             NUMERIC(10, 7),
    longitud            NUMERIC(10, 7),
    nota                TEXT,
    -- Meta defaults
    meta_prepago        INTEGER NOT NULL DEFAULT 0,
    meta_postpago       INTEGER NOT NULL DEFAULT 0,
    meta_bipay          INTEGER NOT NULL DEFAULT 0,
    meta_tv360          INTEGER NOT NULL DEFAULT 0,
    meta_mnp            INTEGER NOT NULL DEFAULT 0,
    meta_agentes        INTEGER NOT NULL DEFAULT 0,
    meta_usuarios_bipay INTEGER NOT NULL DEFAULT 0,
    meta_pago_servicios INTEGER NOT NULL DEFAULT 0,
    meta_tusami         INTEGER NOT NULL DEFAULT 0,
    -- Gasto defaults
    gasto_comida        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    gasto_hotel         NUMERIC(12, 2) NOT NULL DEFAULT 0,
    gasto_movilidad     NUMERIC(12, 2) NOT NULL DEFAULT 0,
    gasto_renta_local   NUMERIC(12, 2) NOT NULL DEFAULT 0,
    -- Merch defaults
    merch_boligrafo     INTEGER NOT NULL DEFAULT 0,
    merch_taza          INTEGER NOT NULL DEFAULT 0,
    merch_llavero       INTEGER NOT NULL DEFAULT 0,
    merch_papin         INTEGER NOT NULL DEFAULT 0,
    merch_sombrero      INTEGER NOT NULL DEFAULT 0,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_loc_bc ON sales_locations(business_center_id);
CREATE INDEX IF NOT EXISTS ix_loc_prio ON sales_locations(prioridad);
CREATE INDEX IF NOT EXISTS ix_loc_geo ON sales_locations(latitud, longitud);

-- ---------- PR (Promoter) staff & groups ----------

CREATE TABLE IF NOT EXISTS sales_pr_groups (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(40) NOT NULL UNIQUE,             -- "Grupo 1" or specific PR code
    business_center_id INTEGER  REFERENCES sales_business_centers(id) ON DELETE SET NULL,
    leader_pr_code  VARCHAR(40),
    member_count    INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_pr_staff (
    id                      SERIAL PRIMARY KEY,
    pr_code                 VARCHAR(40) NOT NULL UNIQUE,    -- vd. LI3PR10116
    owner_code              VARCHAR(60),                    -- vd. AF_ANACC_LI3
    branch_id               INTEGER NOT NULL REFERENCES sales_branches(id),
    business_center_id      INTEGER NOT NULL REFERENCES sales_business_centers(id),
    group_id                INTEGER REFERENCES sales_pr_groups(id) ON DELETE SET NULL,
    tipo_pr                 VARCHAR(30),                    -- Exclusive / Part-time / Nuevo
    leader                  VARCHAR(60),
    kpi_trabajo             INTEGER NOT NULL DEFAULT 0,
    cantidad_dia_trabajo    INTEGER NOT NULL DEFAULT 18,
    estado                  VARCHAR(10) NOT NULL DEFAULT 'OK',
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_pr_bc ON sales_pr_staff(business_center_id);
CREATE INDEX IF NOT EXISTS ix_pr_group ON sales_pr_staff(group_id);

-- ---------- Campaign hierarchy (project ↔ task) ----------

CREATE TABLE IF NOT EXISTS sales_campaigns (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    branch_id       INTEGER REFERENCES sales_branches(id),
    start_date      DATE NOT NULL,
    end_date        DATE,
    status_date     DATE,
    horizon_days    INTEGER NOT NULL DEFAULT 30,
    created_by      INTEGER,                                -- users.id
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_campaign_tasks (
    id                      SERIAL PRIMARY KEY,
    campaign_id             INTEGER NOT NULL REFERENCES sales_campaigns(id) ON DELETE CASCADE,
    parent_task_id          INTEGER REFERENCES sales_campaign_tasks(id) ON DELETE CASCADE,
    wbs_code                VARCHAR(40),
    outline_level           SMALLINT NOT NULL DEFAULT 1,
    sort_order              INTEGER NOT NULL DEFAULT 0,
    task_name               VARCHAR(300) NOT NULL,
    location_id             INTEGER REFERENCES sales_locations(id),
    business_center_id      INTEGER REFERENCES sales_business_centers(id),
    distrito                VARCHAR(120),
    tipo_df_cp              VARCHAR(40),
    horario_traffico        VARCHAR(40),
    fecha_alta_traffico     VARCHAR(15),
    people_in_charge        VARCHAR(120),
    group_id                INTEGER REFERENCES sales_pr_groups(id) ON DELETE SET NULL,
    pr_staff_id             INTEGER REFERENCES sales_pr_staff(id) ON DELETE SET NULL,
    start_date              DATE,
    end_date                DATE,
    duration_days           INTEGER,
    progress                NUMERIC(5,2) NOT NULL DEFAULT 0, -- 0..100
    status                  VARCHAR(20) NOT NULL DEFAULT 'PLANNED',
    -- PLANNED / IN_PROGRESS / COMPLETED / DELAYED / NO_OK / OK / AT_RISK / CANCELLED / MILESTONE
    priority                SMALLINT NOT NULL DEFAULT 500,
    risk_level              VARCHAR(10) NOT NULL DEFAULT 'low',
    risk_reason             TEXT,
    is_milestone            BOOLEAN NOT NULL DEFAULT FALSE,
    is_summary              BOOLEAN NOT NULL DEFAULT FALSE,
    is_critical             BOOLEAN NOT NULL DEFAULT FALSE,
    notes                   TEXT,
    df_bts_code             VARCHAR(60),
    -- Final OK flags (checklist)
    cumple_activaciones     BOOLEAN,
    cumple_digital          BOOLEAN,
    campana_ok              VARCHAR(10),                    -- OK / NO OK
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_task_campaign ON sales_campaign_tasks(campaign_id);
CREATE INDEX IF NOT EXISTS ix_task_loc ON sales_campaign_tasks(location_id);
CREATE INDEX IF NOT EXISTS ix_task_dates ON sales_campaign_tasks(start_date, end_date);
CREATE INDEX IF NOT EXISTS ix_task_status ON sales_campaign_tasks(status);

-- Dependencies between tasks
CREATE TABLE IF NOT EXISTS sales_task_dependencies (
    id              SERIAL PRIMARY KEY,
    predecessor_id  INTEGER NOT NULL REFERENCES sales_campaign_tasks(id) ON DELETE CASCADE,
    successor_id    INTEGER NOT NULL REFERENCES sales_campaign_tasks(id) ON DELETE CASCADE,
    link_type       VARCHAR(2) NOT NULL DEFAULT 'FS',        -- FS/SS/FF/SF
    lag_hours       NUMERIC(8,2) NOT NULL DEFAULT 0,
    CONSTRAINT uq_dep UNIQUE (predecessor_id, successor_id)
);

-- ---------- Targets and Results ----------

CREATE TABLE IF NOT EXISTS sales_campaign_targets (
    id                      SERIAL PRIMARY KEY,
    task_id                 INTEGER NOT NULL REFERENCES sales_campaign_tasks(id) ON DELETE CASCADE UNIQUE,
    prepago                 INTEGER NOT NULL DEFAULT 0,
    postpago                INTEGER NOT NULL DEFAULT 0,
    bipay                   INTEGER NOT NULL DEFAULT 0,
    tv360                   INTEGER NOT NULL DEFAULT 0,
    mnp                     INTEGER NOT NULL DEFAULT 0,
    agentes                 INTEGER NOT NULL DEFAULT 0,
    usuarios_bipay          INTEGER NOT NULL DEFAULT 0,
    pago_servicios          INTEGER NOT NULL DEFAULT 0,
    tusami                  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sales_campaign_results (
    id                      SERIAL PRIMARY KEY,
    task_id                 INTEGER NOT NULL REFERENCES sales_campaign_tasks(id) ON DELETE CASCADE UNIQUE,
    prepago                 INTEGER NOT NULL DEFAULT 0,
    postpago                INTEGER NOT NULL DEFAULT 0,
    bipay                   INTEGER NOT NULL DEFAULT 0,
    tv360                   INTEGER NOT NULL DEFAULT 0,
    mnp                     INTEGER NOT NULL DEFAULT 0,
    agentes                 INTEGER NOT NULL DEFAULT 0,
    usuarios_bipay          INTEGER NOT NULL DEFAULT 0,
    pago_servicios          INTEGER NOT NULL DEFAULT 0,
    tusami                  INTEGER NOT NULL DEFAULT 0,
    recorded_at             TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_campaign_expenses (
    id                      SERIAL PRIMARY KEY,
    task_id                 INTEGER NOT NULL REFERENCES sales_campaign_tasks(id) ON DELETE CASCADE,
    pago_comida             NUMERIC(12,2) NOT NULL DEFAULT 0,
    pago_hotel              NUMERIC(12,2) NOT NULL DEFAULT 0,
    pago_movilidad          NUMERIC(12,2) NOT NULL DEFAULT 0,
    pago_renta_local        NUMERIC(12,2) NOT NULL DEFAULT 0,
    gasto_total_planned     NUMERIC(12,2) NOT NULL DEFAULT 0,
    gasto_total_actual      NUMERIC(12,2) NOT NULL DEFAULT 0,
    evidencia_pago          BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_at             TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_merchandising (
    id                      SERIAL PRIMARY KEY,
    task_id                 INTEGER NOT NULL REFERENCES sales_campaign_tasks(id) ON DELETE CASCADE UNIQUE,
    boligrafo               INTEGER NOT NULL DEFAULT 0,
    taza                    INTEGER NOT NULL DEFAULT 0,
    llavero                 INTEGER NOT NULL DEFAULT 0,
    papin                   INTEGER NOT NULL DEFAULT 0,
    sombrero                INTEGER NOT NULL DEFAULT 0,
    entregado               BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS sales_campaign_checklists (
    id                      SERIAL PRIMARY KEY,
    task_id                 INTEGER NOT NULL REFERENCES sales_campaign_tasks(id) ON DELETE CASCADE,
    item                    VARCHAR(200) NOT NULL,
    is_completed            BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at            TIMESTAMP,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ---------- Daily plan vs actual (timeline pivot) ----------

CREATE TABLE IF NOT EXISTS sales_daily_plan (
    id                      SERIAL PRIMARY KEY,
    task_id                 INTEGER REFERENCES sales_campaign_tasks(id) ON DELETE CASCADE,
    pr_staff_id             INTEGER REFERENCES sales_pr_staff(id) ON DELETE CASCADE,
    group_id                INTEGER REFERENCES sales_pr_groups(id) ON DELETE CASCADE,
    plan_date               DATE NOT NULL,
    units                   NUMERIC(4,2) NOT NULL DEFAULT 1.0, -- 0..1 of PR-day
    CONSTRAINT uq_daily_plan UNIQUE (task_id, pr_staff_id, plan_date)
);

CREATE TABLE IF NOT EXISTS sales_daily_actual (
    id                      SERIAL PRIMARY KEY,
    task_id                 INTEGER REFERENCES sales_campaign_tasks(id) ON DELETE CASCADE,
    pr_staff_id             INTEGER REFERENCES sales_pr_staff(id) ON DELETE CASCADE,
    actual_date             DATE NOT NULL,
    units                   NUMERIC(4,2) NOT NULL DEFAULT 0,
    note                    TEXT,
    CONSTRAINT uq_daily_actual UNIQUE (task_id, pr_staff_id, actual_date)
);
CREATE INDEX IF NOT EXISTS ix_daily_plan_date ON sales_daily_plan(plan_date);
CREATE INDEX IF NOT EXISTS ix_daily_actual_date ON sales_daily_actual(actual_date);

-- ---------- AI planning audit ----------

CREATE TABLE IF NOT EXISTS sales_ai_planning_sessions (
    id              SERIAL PRIMARY KEY,
    campaign_id     INTEGER REFERENCES sales_campaigns(id) ON DELETE SET NULL,
    user_id         INTEGER,
    command         VARCHAR(20) NOT NULL,                   -- /goal /optimize ...
    user_prompt     TEXT,
    scenario        TEXT,                                   -- JSON
    raw_response    TEXT,                                   -- JSON
    validated_plan  TEXT,                                   -- JSON
    schema_ok       BOOLEAN NOT NULL DEFAULT FALSE,
    constraint_violations TEXT,                             -- JSON array
    status          VARCHAR(30) NOT NULL DEFAULT 'running',
    -- running / validated / rejected / constraint_ok / awaiting_approval / applied / declined
    duration_ms     INTEGER,
    provider        VARCHAR(40),                            -- openai|anthropic|stub|local
    model_id        VARCHAR(80),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    applied_at      TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_ai_session_campaign ON sales_ai_planning_sessions(campaign_id);
CREATE INDEX IF NOT EXISTS ix_ai_session_status ON sales_ai_planning_sessions(status);

CREATE TABLE IF NOT EXISTS sales_ai_recommendations (
    id              SERIAL PRIMARY KEY,
    session_id      INTEGER NOT NULL REFERENCES sales_ai_planning_sessions(id) ON DELETE CASCADE,
    kind            VARCHAR(30) NOT NULL,                   -- warning / risk / recommendation / action
    severity        VARCHAR(10) NOT NULL DEFAULT 'info',    -- info / low / medium / high / critical
    target_task_id  INTEGER REFERENCES sales_campaign_tasks(id),
    target_pr_code  VARCHAR(40),
    target_bc_code  VARCHAR(30),
    title           VARCHAR(300) NOT NULL,
    detail          TEXT,
    is_dismissed    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ---------- File imports and audit ----------

CREATE TABLE IF NOT EXISTS sales_imported_files (
    id              SERIAL PRIMARY KEY,
    filename        VARCHAR(300) NOT NULL,
    original_name   VARCHAR(300),
    sha256          CHAR(64) NOT NULL,
    size_bytes      BIGINT,
    uploaded_by     INTEGER,
    storage_uri     TEXT,                                   -- minio://bucket/key
    sheets_detected INTEGER NOT NULL DEFAULT 0,
    rows_imported   INTEGER NOT NULL DEFAULT 0,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending / parsed / mapping / committed / failed
    error_log       TEXT,
    column_mapping  TEXT,                                   -- JSON
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    committed_at    TIMESTAMP,
    CONSTRAINT uq_import_sha UNIQUE (sha256)
);

CREATE TABLE IF NOT EXISTS sales_audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         INTEGER,
    entity          VARCHAR(60) NOT NULL,                   -- task / campaign / pr / location / ai_session ...
    entity_id       INTEGER,
    action          VARCHAR(20) NOT NULL,                   -- create / update / delete / apply / approve
    before_state    TEXT,                                   -- JSON snapshot
    after_state     TEXT,                                   -- JSON snapshot
    ip              VARCHAR(50),
    user_agent      VARCHAR(300),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_audit_entity ON sales_audit_logs(entity, entity_id);
CREATE INDEX IF NOT EXISTS ix_audit_user ON sales_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_audit_time ON sales_audit_logs(created_at);

-- ---------- RBAC (extends users; users table already exists) ----------

CREATE TABLE IF NOT EXISTS sales_roles (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(40) NOT NULL UNIQUE             -- admin / planner / supervisor / viewer
);

CREATE TABLE IF NOT EXISTS sales_user_roles (
    user_id         INTEGER NOT NULL,
    role_id         INTEGER NOT NULL REFERENCES sales_roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

INSERT INTO sales_roles (name) VALUES
    ('admin'), ('planner'), ('supervisor'), ('viewer')
ON CONFLICT (name) DO NOTHING;

-- =====================================================================
-- End of migration 001
-- =====================================================================
