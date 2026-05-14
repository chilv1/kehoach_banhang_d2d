"""Biểu mẫu Tạo / Sửa Campaign — đầy đủ Meta / Gasto / Merchandising."""
from datetime import date

import pandas as pd
import streamlit as st

from lib import campaign, db

st.set_page_config(page_title="Campaign Form", page_icon="📝", layout="wide")
db.init_db()

st.title("📝 Tạo / Sửa Campaign")
st.caption("Mỗi campaign = 1 chương trình bán hàng tại 1 vị trí vào 1 ngày.")

ubic = db.list_ubicacion()
prs = db.list_promoter()

if ubic.empty:
    st.warning("Chưa có Ubicacion nào. Vào trang **Ubicacion** để thêm trước.")
    st.stop()

mode = st.radio("Chế độ", ["Tạo mới", "Sửa campaign có sẵn"], horizontal=True)

# ---------- Pick template ----------
edit_cid: int | None = None
existing: dict = {}

if mode == "Sửa campaign có sẵn":
    today = date.today()
    c1, c2 = st.columns([1, 1])
    yr = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
    mo = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
    month_key = f"{yr:04d}-{mo:02d}"
    cs = campaign.list_campaigns(month=month_key)
    if cs.empty:
        st.info("Không có campaign trong tháng này. Hãy tạo mới.")
        st.stop()
    options = cs.apply(
        lambda r: f"{r['codigo']} | {r['fecha']} | {r['ubicacion_code']} | {r['status']}",
        axis=1,
    ).tolist()
    idx = st.selectbox("Chọn campaign", range(len(options)),
                       format_func=lambda i: options[i])
    edit_cid = int(cs.iloc[idx]["id"])
    existing = campaign.get_campaign(edit_cid) or {}

# ---------- Defaults ----------
def _g(key, default=None):
    return existing.get(key, default)


# ---------- Form ----------
with st.form("campaign_form", clear_on_submit=False):
    st.subheader("Thông tin chung")
    c1, c2, c3 = st.columns(3)
    ubic_codes = ubic["code"].tolist()
    default_ubic = _g("ubicacion_code") or ubic_codes[0]
    sel_ubic = c1.selectbox("Ubicacion *", ubic_codes,
                             index=ubic_codes.index(default_ubic)
                             if default_ubic in ubic_codes else 0)
    fecha = c2.date_input("Ngày *",
                          value=pd.to_datetime(_g("fecha")).date()
                          if _g("fecha") else date.today())
    horario = c3.text_input("Horario", value=_g("horario") or "08:00 - 16:00")

    c1, c2, c3 = st.columns(3)
    nombre = c1.text_input("Tên campaign", value=_g("nombre") or "")
    pr_options = [""] + prs["pr_code"].tolist() if not prs.empty else [""]
    cur_pr = _g("pr_code") or ""
    pr_idx = pr_options.index(cur_pr) if cur_pr in pr_options else 0
    pr_sel = c2.selectbox("Phân công PR", pr_options, index=pr_idx)
    grupo = c3.text_input("Grupo", value=_g("grupo") or "")

    c1, c2, c3 = st.columns(3)
    prioridad = c1.number_input("Prioridad", min_value=1, max_value=10,
                                value=int(_g("prioridad") or 1))
    leader = c2.text_input("Leader", value=_g("leader") or "")
    notas = c3.text_area("Notas", value=_g("notas") or "", height=80)

    # === Meta ===
    st.subheader("🎯 Meta (chỉ tiêu)")
    m1, m2, m3, m4, m5 = st.columns(5)
    meta_prepago = m1.number_input("Prepago", min_value=0,
                                    value=int(_g("meta_prepago") or 0))
    meta_postpago = m2.number_input("Postpago", min_value=0,
                                     value=int(_g("meta_postpago") or 0))
    meta_bipay = m3.number_input("Bipay cashin", min_value=0,
                                  value=int(_g("meta_bipay") or 0))
    meta_tv360 = m4.number_input("TV360", min_value=0,
                                  value=int(_g("meta_tv360") or 0))
    meta_mnp = m5.number_input("MNP", min_value=0,
                                value=int(_g("meta_mnp") or 0))
    meta_agentes = m1.number_input("Agentes", min_value=0,
                                    value=int(_g("meta_agentes") or 0))
    meta_usuarios_bipay = m2.number_input("Usuarios Bipay", min_value=0,
                                           value=int(_g("meta_usuarios_bipay") or 0))
    meta_pago_servicios = m3.number_input("Pago Servicios", min_value=0,
                                           value=int(_g("meta_pago_servicios") or 0))
    meta_tusami = m4.number_input("Meta Tusami", min_value=0,
                                   value=int(_g("meta_tusami") or 0))

    # === Gasto ===
    st.subheader("💵 Gasto kế hoạch")
    g1, g2, g3, g4 = st.columns(4)
    gasto_comida = g1.number_input("Comida", min_value=0.0,
                                    value=float(_g("gasto_comida") or 0))
    gasto_hotel = g2.number_input("Hotel", min_value=0.0,
                                   value=float(_g("gasto_hotel") or 0))
    gasto_movilidad = g3.number_input("Movilidad", min_value=0.0,
                                       value=float(_g("gasto_movilidad") or 0))
    gasto_renta = g4.number_input("Renta", min_value=0.0,
                                   value=float(_g("gasto_renta") or 0))

    # === Merchandising ===
    st.subheader("🎁 Merchandising kế hoạch")
    e1, e2, e3, e4, e5 = st.columns(5)
    merch_boligrafo = e1.number_input("Bolígrafo", min_value=0,
                                       value=int(_g("merch_boligrafo") or 0))
    merch_taza = e2.number_input("Taza", min_value=0,
                                  value=int(_g("merch_taza") or 0))
    merch_llavero = e3.number_input("Llavero", min_value=0,
                                     value=int(_g("merch_llavero") or 0))
    merch_papin = e4.number_input("Papin", min_value=0,
                                   value=int(_g("merch_papin") or 0))
    merch_sombrero = e5.number_input("Sombrero", min_value=0,
                                      value=int(_g("merch_sombrero") or 0))

    submitted = st.form_submit_button("💾 Lưu campaign", type="primary")

    if submitted:
        payload = {
            "ubicacion_code": sel_ubic,
            "fecha": fecha.isoformat(),
            "horario": horario,
            "nombre": nombre or None,
            "pr_code": pr_sel or None,
            "grupo": grupo or None,
            "leader": leader or None,
            "prioridad": prioridad,
            "notas": notas or None,
            "meta_prepago": meta_prepago, "meta_postpago": meta_postpago,
            "meta_bipay": meta_bipay, "meta_tv360": meta_tv360,
            "meta_mnp": meta_mnp, "meta_agentes": meta_agentes,
            "meta_usuarios_bipay": meta_usuarios_bipay,
            "meta_pago_servicios": meta_pago_servicios,
            "meta_tusami": meta_tusami,
            "gasto_comida": gasto_comida, "gasto_hotel": gasto_hotel,
            "gasto_movilidad": gasto_movilidad, "gasto_renta": gasto_renta,
            "merch_boligrafo": merch_boligrafo, "merch_taza": merch_taza,
            "merch_llavero": merch_llavero, "merch_papin": merch_papin,
            "merch_sombrero": merch_sombrero,
        }
        try:
            if edit_cid:
                campaign.update_campaign(edit_cid, payload)
                st.success(f"Đã cập nhật campaign #{edit_cid}.")
            else:
                cid = campaign.create_campaign(payload)
                st.success(f"Đã tạo campaign #{cid}.")
        except Exception as e:
            st.error(f"Lỗi: {e}")
