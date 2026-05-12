"""SQLite layer cho ứng dụng kế hoạch bán hàng D2D."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

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

CREATE TABLE IF NOT EXISTS plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    ubicacion_code TEXT NOT NULL,
    pr_code TEXT,
    bc TEXT,
    grupo TEXT,
    notas TEXT,
    UNIQUE(fecha, ubicacion_code),
    FOREIGN KEY (ubicacion_code) REFERENCES ubicacion(code),
    FOREIGN KEY (pr_code) REFERENCES promoter(pr_code)
);

CREATE TABLE IF NOT EXISTS resultado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    ubicacion_code TEXT NOT NULL,
    res_prepago REAL DEFAULT 0,
    res_postpago REAL DEFAULT 0,
    res_bipay REAL DEFAULT 0,
    res_tv360 REAL DEFAULT 0,
    res_mnp REAL DEFAULT 0,
    res_agentes REAL DEFAULT 0,
    res_usuarios_bipay REAL DEFAULT 0,
    res_pago_servicios REAL DEFAULT 0,
    res_tusami REAL DEFAULT 0,
    campana_ok INTEGER DEFAULT 0,
    nota TEXT,
    UNIQUE(fecha, ubicacion_code)
);

CREATE INDEX IF NOT EXISTS idx_plan_fecha ON plan(fecha);
CREATE INDEX IF NOT EXISTS idx_plan_bc ON plan(bc);
CREATE INDEX IF NOT EXISTS idx_ubic_bc ON ubicacion(bc);
CREATE INDEX IF NOT EXISTS idx_pr_bc ON promoter(bc);
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


# ---------- Ubicacion ----------

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


# ---------- Promoter ----------

PROMOTER_COLS = [
    "pr_code", "owner_code", "br", "bc", "tipo", "leader", "grupo",
    "kpi_trabajo", "cantidad_dia_trabajo", "estado", "activo",
]


def list_promoter() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM promoter ORDER BY bc, grupo, pr_code", conn
        )


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


# ---------- Plan ----------

def clear_plan(month: str | None = None) -> None:
    """month dạng 'YYYY-MM'."""
    with transaction() as conn:
        if month:
            conn.execute("DELETE FROM plan WHERE fecha LIKE ?", (f"{month}-%",))
        else:
            conn.execute("DELETE FROM plan")


def insert_plan_rows(rows: list[dict]) -> int:
    if not rows:
        return 0
    with transaction() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO plan "
            "(fecha, ubicacion_code, pr_code, bc, grupo, notas) "
            "VALUES (:fecha, :ubicacion_code, :pr_code, :bc, :grupo, :notas)",
            rows,
        )
    return len(rows)


def list_plan(month: str | None = None) -> pd.DataFrame:
    with get_conn() as conn:
        if month:
            return pd.read_sql_query(
                """SELECT p.*, u.distrito, u.tipo_dfcp, u.prioridad,
                          u.meta_prepago, u.meta_postpago, u.meta_bipay,
                          u.meta_tv360, u.meta_mnp
                   FROM plan p
                   LEFT JOIN ubicacion u ON u.code = p.ubicacion_code
                   WHERE p.fecha LIKE ?
                   ORDER BY p.fecha, p.bc, p.ubicacion_code""",
                conn,
                params=(f"{month}-%",),
            )
        return pd.read_sql_query(
            """SELECT p.*, u.distrito, u.tipo_dfcp, u.prioridad,
                      u.meta_prepago, u.meta_postpago, u.meta_bipay,
                      u.meta_tv360, u.meta_mnp
               FROM plan p
               LEFT JOIN ubicacion u ON u.code = p.ubicacion_code
               ORDER BY p.fecha""",
            conn,
        )


# ---------- Resultado ----------

def upsert_resultado(row: dict) -> None:
    cols = list(row.keys())
    placeholders = ",".join(["?"] * len(cols))
    col_list = ",".join(cols)
    updates = ",".join(
        f"{c}=excluded.{c}" for c in cols if c not in ("fecha", "ubicacion_code")
    )
    sql = (
        f"INSERT INTO resultado ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT(fecha, ubicacion_code) DO UPDATE SET {updates}"
    )
    with transaction() as conn:
        conn.execute(sql, [row[c] for c in cols])


def list_resultado(month: str | None = None) -> pd.DataFrame:
    with get_conn() as conn:
        if month:
            return pd.read_sql_query(
                "SELECT * FROM resultado WHERE fecha LIKE ? ORDER BY fecha",
                conn,
                params=(f"{month}-%",),
            )
        return pd.read_sql_query("SELECT * FROM resultado ORDER BY fecha", conn)


# ---------- Utilities ----------

def stats_counts() -> dict:
    with get_conn() as conn:
        cur = conn.cursor()
        out = {}
        out["ubicacion"] = cur.execute(
            "SELECT COUNT(*) FROM ubicacion WHERE activo=1"
        ).fetchone()[0]
        out["promoter"] = cur.execute(
            "SELECT COUNT(*) FROM promoter WHERE activo=1"
        ).fetchone()[0]
        out["plan"] = cur.execute("SELECT COUNT(*) FROM plan").fetchone()[0]
        out["resultado"] = cur.execute("SELECT COUNT(*) FROM resultado").fetchone()[0]
        return out
