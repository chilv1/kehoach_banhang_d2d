"""Campaign service — CRUD + state machine cho chương trình bán hàng."""
from __future__ import annotations

import pandas as pd

from .db import (
    TRANSITIONS,
    get_conn,
    get_ubicacion,
    now_iso,
    transaction,
)

CAMPAIGN_FIELDS = [
    "codigo", "nombre", "ubicacion_code", "fecha", "horario",
    "pr_code", "bc", "br", "grupo", "leader", "status", "prioridad",
    "meta_prepago", "meta_postpago", "meta_bipay", "meta_tv360", "meta_mnp",
    "meta_agentes", "meta_usuarios_bipay", "meta_pago_servicios", "meta_tusami",
    "gasto_comida", "gasto_hotel", "gasto_movilidad", "gasto_renta",
    "merch_boligrafo", "merch_taza", "merch_llavero", "merch_papin", "merch_sombrero",
    "notas",
]

META_FIELDS = [c for c in CAMPAIGN_FIELDS if c.startswith("meta_")]
GASTO_FIELDS = [c for c in CAMPAIGN_FIELDS if c.startswith("gasto_")]
MERCH_FIELDS = [c for c in CAMPAIGN_FIELDS if c.startswith("merch_")]

RESULT_FIELDS = [
    "res_prepago", "res_postpago", "res_bipay", "res_tv360", "res_mnp",
    "res_agentes", "res_usuarios_bipay", "res_pago_servicios", "res_tusami",
    "gasto_real",
    "evidencia_pago", "merch_entregado", "checklist_ok",
    "activaciones_ok", "digital_ok", "campana_ok",
    "dfcode_btscode", "nota",
]


# ---------- Code generator ----------

def next_campaign_code(fecha: str, ubicacion_code: str) -> str:
    """Sinh mã CMP-YYYYMM-CPxx-NN."""
    yyyymm = fecha[:7].replace("-", "")
    with get_conn() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM campaign WHERE codigo LIKE ?",
            (f"CMP-{yyyymm}-{ubicacion_code}-%",),
        ).fetchone()[0]
    return f"CMP-{yyyymm}-{ubicacion_code}-{n + 1:02d}"


# ---------- Create ----------

def create_campaign(data: dict, actor: str = "system") -> int:
    """Tạo campaign mới. data tối thiểu: ubicacion_code, fecha. Trả về id."""
    ubicacion_code = data["ubicacion_code"]
    fecha = data["fecha"]
    ubic = get_ubicacion(ubicacion_code)
    if not ubic:
        raise ValueError(f"Ubicacion '{ubicacion_code}' không tồn tại")

    row = {f: None for f in CAMPAIGN_FIELDS}
    # default từ ubicacion
    for f in META_FIELDS + GASTO_FIELDS + MERCH_FIELDS:
        row[f] = ubic.get(f, 0) or 0
    row["bc"] = ubic.get("bc")
    row["br"] = ubic.get("br")
    row["horario"] = ubic.get("horario_traffico")
    row["prioridad"] = ubic.get("prioridad") or 1
    row["status"] = "DRAFT"
    row["nombre"] = f"{ubic.get('distrito') or ubicacion_code} — {ubic.get('tipo_dfcp') or ''}".strip(" —")

    # override với input
    for k, v in data.items():
        if k in CAMPAIGN_FIELDS:
            row[k] = v

    row["codigo"] = row.get("codigo") or next_campaign_code(fecha, ubicacion_code)
    ts = now_iso()
    cols = list(CAMPAIGN_FIELDS) + ["created_at", "updated_at"]
    values = [row.get(c) for c in CAMPAIGN_FIELDS] + [ts, ts]
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT INTO campaign ({','.join(cols)}) VALUES ({placeholders})"

    with transaction() as conn:
        cur = conn.execute(sql, values)
        cid = cur.lastrowid
        conn.execute(
            "INSERT INTO campaign_log "
            "(campaign_id, accion, new_status, nota, actor, at) "
            "VALUES (?, 'CREATED', ?, ?, ?, ?)",
            (cid, row["status"], "Tạo campaign", actor, ts),
        )
    return cid


def bulk_create_campaigns(rows: list[dict], actor: str = "planner") -> int:
    n = 0
    for r in rows:
        try:
            create_campaign(r, actor=actor)
            n += 1
        except Exception:
            # bỏ qua duplicate (fecha, ubicacion_code)
            continue
    return n


# ---------- Update / Status ----------

def update_campaign(cid: int, patch: dict, actor: str = "user") -> None:
    fields = [f for f in CAMPAIGN_FIELDS if f in patch and f != "status"]
    if not fields:
        return
    sets = ",".join(f"{f}=?" for f in fields) + ",updated_at=?"
    values = [patch[f] for f in fields] + [now_iso(), cid]
    with transaction() as conn:
        conn.execute(f"UPDATE campaign SET {sets} WHERE id=?", values)
        conn.execute(
            "INSERT INTO campaign_log (campaign_id, accion, nota, actor, at) "
            "VALUES (?, 'UPDATED', ?, ?, ?)",
            (cid, f"Updated fields: {', '.join(fields)}", actor, now_iso()),
        )


def change_status(cid: int, new_status: str, actor: str = "user",
                  nota: str = "") -> None:
    with transaction() as conn:
        row = conn.execute("SELECT status FROM campaign WHERE id=?",
                           (cid,)).fetchone()
        if not row:
            raise ValueError(f"Campaign {cid} không tồn tại")
        old = row["status"]
        if new_status == old:
            return
        if new_status not in TRANSITIONS.get(old, set()):
            raise ValueError(
                f"Không thể chuyển {old} → {new_status}. "
                f"Cho phép: {sorted(TRANSITIONS.get(old, set()))}"
            )
        conn.execute(
            "UPDATE campaign SET status=?, updated_at=? WHERE id=?",
            (new_status, now_iso(), cid),
        )
        conn.execute(
            "INSERT INTO campaign_log "
            "(campaign_id, accion, old_status, new_status, nota, actor, at) "
            "VALUES (?, 'STATUS', ?, ?, ?, ?, ?)",
            (cid, old, new_status, nota, actor, now_iso()),
        )


def delete_campaign(cid: int) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM campaign WHERE id=?", (cid,))


# ---------- Read ----------

def list_campaigns(
    month: str | None = None,
    status: list[str] | None = None,
    bc: list[str] | None = None,
) -> pd.DataFrame:
    sql = ["SELECT c.*, u.distrito, u.tipo_dfcp, u.latitud, u.longitud "
           "FROM campaign c LEFT JOIN ubicacion u ON u.code = c.ubicacion_code"]
    where = []
    params: list = []
    if month:
        where.append("c.fecha LIKE ?")
        params.append(f"{month}-%")
    if status:
        where.append(f"c.status IN ({','.join(['?'] * len(status))})")
        params.extend(status)
    if bc:
        where.append(f"c.bc IN ({','.join(['?'] * len(bc))})")
        params.extend(bc)
    if where:
        sql.append("WHERE " + " AND ".join(where))
    sql.append("ORDER BY c.fecha, c.bc, c.ubicacion_code")
    with get_conn() as conn:
        return pd.read_sql_query(" ".join(sql), conn, params=params)


def get_campaign(cid: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM campaign WHERE id=?", (cid,)).fetchone()
        return dict(row) if row else None


def campaign_log(cid: int) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM campaign_log WHERE campaign_id=? ORDER BY at DESC",
            conn, params=(cid,),
        )


# ---------- Result ----------

def upsert_result(cid: int, data: dict, actor: str = "user") -> None:
    cols = [c for c in RESULT_FIELDS if c in data]
    if not cols:
        return
    cols_full = ["campaign_id"] + cols + ["recorded_at"]
    placeholders = ",".join(["?"] * len(cols_full))
    updates = ",".join(f"{c}=excluded.{c}" for c in cols) + ",recorded_at=excluded.recorded_at"
    sql = (
        f"INSERT INTO campaign_result ({','.join(cols_full)}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT(campaign_id) DO UPDATE SET {updates}"
    )
    values = [cid] + [data[c] for c in cols] + [now_iso()]
    with transaction() as conn:
        conn.execute(sql, values)
        conn.execute(
            "INSERT INTO campaign_log (campaign_id, accion, nota, actor, at) "
            "VALUES (?, 'UPDATED', ?, ?, ?)",
            (cid, "Cập nhật kết quả", actor, now_iso()),
        )


def get_result(cid: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM campaign_result WHERE campaign_id=?", (cid,)
        ).fetchone()
        return dict(row) if row else None


def list_results_with_campaign(month: str | None = None) -> pd.DataFrame:
    sql = (
        "SELECT c.id, c.codigo, c.fecha, c.bc, c.ubicacion_code, c.status, "
        "c.meta_prepago, c.meta_postpago, c.meta_bipay, c.meta_tv360, c.meta_mnp, "
        "r.res_prepago, r.res_postpago, r.res_bipay, r.res_tv360, r.res_mnp, "
        "r.gasto_real, r.campana_ok "
        "FROM campaign c LEFT JOIN campaign_result r ON r.campaign_id = c.id"
    )
    params: list = []
    if month:
        sql += " WHERE c.fecha LIKE ?"
        params.append(f"{month}-%")
    sql += " ORDER BY c.fecha"
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def clear_campaigns(month: str, only_status: list[str] | None = None) -> int:
    """Xoá campaign trong tháng. Mặc định chỉ xoá DRAFT để an toàn."""
    only_status = only_status or ["DRAFT"]
    placeholders = ",".join(["?"] * len(only_status))
    with transaction() as conn:
        cur = conn.execute(
            f"DELETE FROM campaign WHERE fecha LIKE ? AND status IN ({placeholders})",
            [f"{month}-%"] + only_status,
        )
        return cur.rowcount
