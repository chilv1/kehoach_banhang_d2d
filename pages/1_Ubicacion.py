"""CRUD Ubicacion (điểm bán)."""
import pandas as pd
import streamlit as st

from lib import db

st.set_page_config(page_title="Ubicacion", page_icon="📍", layout="wide")
db.init_db()

st.title("📍 Quản lý Ubicacion (điểm bán)")

TRAFFIC_OPTIONS = ["", "WEEKDAY", "WEEKEND",
                   "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
                   "FRIDAY", "SATURDAY", "SUNDAY"]
TIPO_OPTIONS = ["DF Fijo", "BTS Upgrade", "Mercado", "Rural",
                "Plaza", "Pilot Mercado", "Universidad", "Zone 5%",
                "Grifo", "Otro"]

tab_list, tab_add, tab_edit = st.tabs(["📋 Danh sách", "➕ Thêm mới", "✏️ Sửa/Xoá"])

with tab_list:
    df = db.list_ubicacion()
    if df.empty:
        st.info("Chưa có điểm bán nào. Hãy thêm mới hoặc dùng trang Import/Export.")
    else:
        bcs = sorted(df["bc"].dropna().unique().tolist())
        sel_bc = st.multiselect("Lọc theo BC", bcs, default=bcs)
        view = df[df["bc"].isin(sel_bc)] if sel_bc else df
        st.dataframe(view, use_container_width=True, height=480)
        st.caption(f"Tổng cộng: **{len(view)}** / {len(df)} điểm bán")

with tab_add:
    st.subheader("Thêm điểm bán mới")
    with st.form("add_ubic", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            code = st.text_input("Code Ubicacion *", placeholder="vd. CP01")
            br = st.text_input("BR *", placeholder="vd. LI3BR")
            bc = st.text_input("BC *", placeholder="vd. LI3BC12")
            departamento = st.text_input("Departamento", value="LIMA")
            distrito = st.text_input("Distrito")
        with c2:
            tipo_dfcp = st.selectbox("Tipo DF/CP", TIPO_OPTIONS)
            horario = st.text_input("Horario traffico", placeholder="08:00 - 16:00")
            fecha_alta = st.selectbox("Fecha Alta Traffico", TRAFFIC_OPTIONS)
            prioridad = st.number_input("Prioridad", min_value=1, max_value=10, value=1)
            cantidad_dia = st.number_input("Cantidad ngày campaign / tháng", min_value=1, value=1)
        with c3:
            latitud = st.number_input("Latitud", format="%.10f", value=0.0)
            longitud = st.number_input("Longitud", format="%.10f", value=0.0)
            nota = st.text_area("Nota", height=120)

        st.markdown("**Meta (chỉ tiêu)**")
        mc1, mc2, mc3, mc4 = st.columns(4)
        meta_prepago = mc1.number_input("Prepago", min_value=0, value=15)
        meta_postpago = mc2.number_input("Postpago", min_value=0, value=2)
        meta_bipay = mc3.number_input("Bipay cashin", min_value=0, value=2)
        meta_tv360 = mc4.number_input("TV360", min_value=0, value=13)
        meta_mnp = mc1.number_input("MNP", min_value=0, value=4)
        meta_agentes = mc2.number_input("Agentes/Negocio", min_value=0, value=4)
        meta_usuarios_bipay = mc3.number_input("Usuarios Bipay", min_value=0, value=0)
        meta_pago_servicios = mc4.number_input("Pago Servicios", min_value=0, value=0)
        meta_tusami = mc1.number_input("Meta Tusami", min_value=0, value=0)

        st.markdown("**Gasto (chi phí)**")
        gc1, gc2, gc3, gc4 = st.columns(4)
        gasto_comida = gc1.number_input("Comida", min_value=0.0, value=2.0)
        gasto_hotel = gc2.number_input("Hotel", min_value=0.0, value=0.0)
        gasto_movilidad = gc3.number_input("Movilidad", min_value=0.0, value=0.0)
        gasto_renta = gc4.number_input("Renta Local", min_value=0.0, value=0.0)

        st.markdown("**Merchandising**")
        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
        merch_boligrafo = ec1.number_input("Bolígrafo", min_value=0, value=2)
        merch_taza = ec2.number_input("Taza", min_value=0, value=5)
        merch_llavero = ec3.number_input("Llavero", min_value=0, value=3)
        merch_papin = ec4.number_input("Papin", min_value=0, value=1)
        merch_sombrero = ec5.number_input("Sombrero", min_value=0, value=1)

        submitted = st.form_submit_button("💾 Lưu", type="primary")
        if submitted:
            if not code or not br or not bc:
                st.error("Bắt buộc nhập Code, BR, BC.")
            else:
                db.upsert_ubicacion({
                    "code": code.strip(),
                    "br": br.strip(),
                    "bc": bc.strip(),
                    "departamento": departamento,
                    "distrito": distrito,
                    "tipo_dfcp": tipo_dfcp,
                    "horario_traffico": horario,
                    "fecha_alta_traffico": fecha_alta,
                    "prioridad": prioridad,
                    "latitud": latitud,
                    "longitud": longitud,
                    "cantidad_dia": cantidad_dia,
                    "nota": nota,
                    "meta_prepago": meta_prepago,
                    "meta_postpago": meta_postpago,
                    "meta_bipay": meta_bipay,
                    "meta_tv360": meta_tv360,
                    "meta_mnp": meta_mnp,
                    "meta_agentes": meta_agentes,
                    "meta_usuarios_bipay": meta_usuarios_bipay,
                    "meta_pago_servicios": meta_pago_servicios,
                    "meta_tusami": meta_tusami,
                    "gasto_comida": gasto_comida,
                    "gasto_hotel": gasto_hotel,
                    "gasto_movilidad": gasto_movilidad,
                    "gasto_renta": gasto_renta,
                    "merch_boligrafo": merch_boligrafo,
                    "merch_taza": merch_taza,
                    "merch_llavero": merch_llavero,
                    "merch_papin": merch_papin,
                    "merch_sombrero": merch_sombrero,
                    "activo": 1,
                })
                st.success(f"Đã lưu {code}.")

with tab_edit:
    st.subheader("Chỉnh sửa hàng loạt (Data Editor)")
    df = db.list_ubicacion()
    if df.empty:
        st.info("Chưa có dữ liệu.")
    else:
        edited = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            disabled=["code"],
            height=500,
            key="ubic_editor",
        )
        c1, c2 = st.columns([1, 4])
        if c1.button("💾 Lưu thay đổi", type="primary"):
            n = 0
            for _, r in edited.iterrows():
                if not r.get("code"):
                    continue
                db.upsert_ubicacion(r.to_dict())
                n += 1
            st.success(f"Đã lưu {n} dòng.")
            st.rerun()
        st.divider()
        del_code = st.selectbox("Xoá điểm bán", [""] + df["code"].tolist())
        if del_code and st.button("🗑️ Xoá", type="secondary"):
            db.delete_ubicacion(del_code)
            st.success(f"Đã xoá {del_code}.")
            st.rerun()
