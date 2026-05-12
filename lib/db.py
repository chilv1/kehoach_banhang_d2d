"""SQLite layer cho hệ thống quản lý Campaign (chương trình bán hàng) D2D.

Mô hình:
- `ubicacion` : danh mục điểm bán (master data)
- `promoter`  : danh mục nhân lực (master data)
- `campaign`  : 1 chương trình bán hàng tại 1 điểm vào 1 ngày
- `campaign_log` : nhật ký thay đổi trạng thái
- `campaign_result` : kết quả thực tế + checklist khi đóng campaign

Trạng thái campaign (status):
    DRAFT       — vừa tạo / sinh tự động, chưa duyệt
    PLANNED     — đã duyệt, sẵn sàng chạy
    RUNNING     — đang diễn ra (theo ngày hiện tại)
    DONE        — đã chạy xong, đã có kết quả
    CANCELLED   — huỷ
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

STATUSES = ["DRAFT", "PLANNED", "RUNNING", "DONE", "CANCELLED"]

# Cho phép chuyển trạng thái nào sang trạng thái nào
TRANSITIONS = {
    "DRAFT":     {"PLANNED", "CANCELLED"},
    "PLANNED":   {"RUNNING", "DONE", "CANCELLED", "DRAFT"},
    "RUNNING":   {"DONE", "CANCELLED"},
    "DONE":      {"PLANNED"},          # cho phép mở lại nếu nhập sai
    "CANCELLED": {"DRAFT"},
}


SCHEMA = """
CREATE TABLE IF NOT EXISTS ubicacion (
    code TEXT PRIMARY KEY,
    br TEXT NOT NULL,
    bc TEXT NOT NULL,
    departamento TEXT,
    distrito TEXT,
    tipo_dfcp TEXT,
    horario_traffico TEXT,
    fecha_alta_traffico TEXT,
    prioridad INTEGER DEFAULT 1,
    latitud REAL,
    longitud REAL,
    cantidad_dia INTEGER DEFAULT 1,
    nota TEXT,
    meta_prepago REAL DEFAULT 0,
    meta_postpago REAL DEFAULT 0,
    meta_bipay REAL DEFAULT 0,
    meta_tv360 REAL DEFAULT 0,
    meta_mnp REAL DEFAULT 0,
    meta_agentes REAL DEFAULT 0,
    meta_usuarios_bipay REAL DEFAULT 0,
    meta_pago_servicios REAL DEFAULT 0,
    meta_tusami REAL DEFAULT 0,
    gasto_comida REAL DEFAULT 0,
    gasto_hotel REAL DEFAULT 0,
    gasto_movilidad REAL DEFAULT 0,
    gasto_renta REAL DEFAULT 0,
    merch_boligrafo INTEGER DEFAULT 0,
    merch_taza INTEGER DEFAULT 0,
    merch_llavero INTEGER DEFAULT 0,
    merch_papin INTEGER DEFAULT 0,
    merch_sombrero INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS promoter (
    pr_code TEXT PRIMARY KEY,
    owner_code TEXT,
    br TEXT NOT NULL,
    bc TEXT NOT NULL,
    tipo TEXT,
    leader TEXT,
    grupo TEXT,
    kpi_trabajo REAL DEFAULT 0,
    cantidad_dia_trabajo INTEGER DEFAULT 18,
    estado TEXT DEFAULT 'OK',
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS campaign (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE,                 -- mã campaign tự sinh, vd. CMP-202605-CP01-01
    nombre TEXT,                        -- tên campaign (mô tả ngắn)
    ubicacion_code TEXT NOT NULL,
    fecha TEXT NOT NULL,                -- YYYY-MM-DD
    horario TEXT,                       -- "08:00 - 16:00"
    pr_code TEXT,
    bc TEXT NOT NULL,
    br TEXT,
    grupo TEXT,
    leader TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    prioridad INTEGER DEFAULT 1,
    -- Meta override (mặc định lấy từ ubicacion)
    meta_prepago REAL DEFAULT 0,
    meta_postpago REAL DEFAULT 0,
    meta_bipay REAL DEFAULT 0,
    meta_tv360 REAL DEFAULT 0,
    meta_mnp REAL DEFAULT 0,
    meta_agentes REAL DEFAULT 0,
    meta_usuarios_bipay REAL DEFAULT 0,
    meta_pago_servicios REAL DEFAULT 0,
    meta_tusami REAL DEFAULT 0,
    -- Gasto kế hoạch
    gasto_comida REAL DEFAULT 0,
    gasto_hotel REAL DEFAULT 0,
    gasto_movilidad REAL DEFAULT 0,
    gasto_renta REAL DEFAULT 0,
    -- Merchandising kế hoạch
    merch_boligrafo INTEGER DEFAULT 0,
    merch_taza INTEGER DEFAULT 0,
    merch_llavero INTEGER DEFAULT 0,
    merch_papin INTEGER DEFAULT 0,
    merch_sombrero INTEGER DEFAULT 0,
    notas TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(fecha, ubicacion_code),
    FOREIGN KEY (ubicacion_code) REFERENCES ubicacion(code),
    FOREIGN KEY (pr_code) REFERENCES promoter(pr_code)
);

CREATE TABLE IF NOT EXISTS campaign_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    accion TEXT NOT NULL,               -- CREATED, STATUS, UPDATED
    old_status TEXT,
    new_status TEXT,
    nota TEXT,
    actor TEXT,
    at TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaign(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS campaign_result (
    campaign_id INTEGER PRIMARY KEY,
    res_prepago REAL DEFAULT 0,
    res_postpago REAL DEFAULT 0,
    res_bipay REAL DEFAULT 0,
    res_tv360 REAL DEFAULT 0,
    res_mnp REAL DEFAULT 0,
    res_agentes REAL DEFAULT 0,
    res_usuarios_bipay REAL DEFAULT 0,
    res_pago_servicios REAL DEFAULT 0,
    res_tusami REAL DEFAULT 0,
    gasto_real REAL DEFAULT 0,
    evidencia_pago INTEGER DEFAULT 0,
    merch_entregado INTEGER DEFAULT 0,
    checklist_ok INTEGER DEFAULT 0,
    activaciones_ok INTEGER DEFAULT 0,
    digital_ok INTEGER DEFAULT 0,
    campana_ok INTEGER DEFAULT 0,
    dfcode_btscode TEXT,
    nota TEXT,
    recorded_at TEXT,
    FOREIGN KEY (campaign_id) REFERENCES campaign(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_campaign_fecha ON campaign(fecha);
CREATE INDEX IF NOT EXISTS idx_campaign_status ON campaign(status);
CREATE INDEX IF NOT EXISTS idx_campaign_bc ON campaign(bc);
CREATE INDEX IF NOT EXISTS idx_campaign_ubic ON campaign(ubicacion_code);
CREATE INDEX IF NOT EXISTS idx_log_campaign ON campaign_log(campaign_id);
"""


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def transaction():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ====================== Ubicacion ======================

UBICACION_COLS = [
    "code", "br", "bc", "departamento", "distrito", "tipo_dfcp",
    "horario_traffico", "fecha_alta_traffico", "prioridad",
    "latitud", "longitud", "cantidad_dia", "nota",
    "meta_prepago", "meta_postpago", "meta_bipay", "meta_tv360", "meta_mnp",
    "meta_agentes", "meta_usuarios_bipay", "meta_pago_servicios", "meta_tusami",
    "gasto_comida", "gasto_hotel", "gasto_movilidad", "gasto_renta",
    "merch_boligrafo", "merch_taza", "merch_llavero", "merch_papin", "merch_sombrero",
    "activo",
]


def list_ubicacion() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM ubicacion ORDER BY bc, prioridad, code", conn
        )


def get_ubicacion(code: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM ubicacion WHERE code = ?", (code,)).fetchone()
        return dict(row) if row else None


def upsert_ubicacion(row: dict) -> None:
    cols = [c for c in UBICACION_COLS if c in row]
    placeholders = ",".join(["?"] * len(cols))
    col_list = ",".join(cols)
    updates = ",".join(f"{c}=excluded.{c}" for c in cols if c != "code")
    sql = (
        f"INSERT INTO ubicacion ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT(code) DO UPDATE SET {updates}"
    )
    with transaction() as conn:
        conn.execute(sql, [row[c] for c in cols])


def bulk_upsert_ubicacion(rows: Iterable[dict]) -> int:
    n = 0
    for r in rows:
        upsert_ubicacion(r)
        n += 1
    return n


def delete_ubicacion(code: str) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM ubicacion WHERE code = ?", (code,))


# ====================== Promoter ======================

PROMOTER_COLS = [
    "pr_code", "owner_code", "br", "bc", "tipo", "leader", "grupo",
    "kpi_trabajo", "cantidad_dia_trabajo", "estado", "activo",
]


def list_promoter() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM promoter ORDER BY bc, grupo, pr_code", conn
        )


def get_promoter(pr_code: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM promoter WHERE pr_code = ?", (pr_code,)
        ).fetchone()
        return dict(row) if row else None


def upsert_promoter(row: dict) -> None:
    cols = [c for c in PROMOTER_COLS if c in row]
    placeholders = ",".join(["?"] * len(cols))
    col_list = ",".join(cols)
    updates = ",".join(f"{c}=excluded.{c}" for c in cols if c != "pr_code")
    sql = (
        f"INSERT INTO promoter ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT(pr_code) DO UPDATE SET {updates}"
    )
    with transaction() as conn:
        conn.execute(sql, [row[c] for c in cols])


def bulk_upsert_promoter(rows: Iterable[dict]) -> int:
    n = 0
    for r in rows:
        upsert_promoter(r)
        n += 1
    return n


def delete_promoter(pr_code: str) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM promoter WHERE pr_code = ?", (pr_code,))


# ====================== Counts ======================

def stats_counts() -> dict:
    with get_conn() as conn:
        cur = conn.cursor()
        out = {
            "ubicacion": cur.execute(
                "SELECT COUNT(*) FROM ubicacion WHERE activo=1"
            ).fetchone()[0],
            "promoter": cur.execute(
                "SELECT COUNT(*) FROM promoter WHERE activo=1"
            ).fetchone()[0],
            "campaign": cur.execute("SELECT COUNT(*) FROM campaign").fetchone()[0],
            "campaign_done": cur.execute(
                "SELECT COUNT(*) FROM campaign WHERE status='DONE'"
            ).fetchone()[0],
        }
        return out
