"""CRUD Promoter / Grupo."""
import streamlit as st

from lib import db

st.set_page_config(page_title="PR / Grupo", page_icon="👥", layout="wide")
db.init_db()

st.title("👥 Quản lý PR / Grupo (nhân lực)")

TIPO_PR_OPTIONS = ["Exclusive", "Part-time", "Nuevo"]
ESTADO_OPTIONS = ["OK", "NO OK"]

tab_list, tab_add, tab_edit = st.tabs(["📋 Danh sách", "➕ Thêm mới", "✏️ Sửa/Xoá"])

with tab_list:
    df = db.list_promoter()
    if df.empty:
        st.info("Chưa có PR nào.")
    else:
        bcs = sorted(df["bc"].dropna().unique().tolist())
        grupos = sorted(df["grupo"].dropna().unique().tolist())
        c1, c2 = st.columns(2)
        sel_bc = c1.multiselect("Lọc theo BC", bcs, default=bcs)
        sel_grupo = c2.multiselect("Lọc theo Grupo", grupos, default=grupos)
        view = df.copy()
        if sel_bc:
            view = view[view["bc"].isin(sel_bc)]
        if sel_grupo:
            view = view[view["grupo"].isin(sel_grupo)]
        st.dataframe(view, use_container_width=True, height=480)
        st.caption(f"Tổng cộng: **{len(view)}** / {len(df)} PR")

        st.divider()
        st.subheader("Tổng quan theo Grupo / BC")
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Số PR theo BC**")
            st.bar_chart(df.groupby("bc").size())
        with c2:
            st.write("**Số PR theo Tipo**")
            st.bar_chart(df.groupby("tipo").size())

with tab_add:
    st.subheader("Thêm PR mới")
    with st.form("add_pr", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            pr_code = st.text_input("PR Code *", placeholder="vd. LI3PR10116")
            br = st.text_input("BR *", placeholder="vd. LI3BR")
            bc = st.text_input("BC *", placeholder="vd. LI3BC03")
        with c2:
            owner_code = st.text_input("Owner code", placeholder="AF_ANACC_LI3")
            tipo = st.selectbox("Tipo de PR", TIPO_PR_OPTIONS)
            leader = st.text_input("Leader (AF/BC)")
        with c3:
            grupo = st.text_input("Grupo", placeholder="Grupo 1 / LI3PR10136")
            kpi = st.number_input("KPI Trabajo", min_value=0, value=25)
            cantidad = st.number_input("Cantidad ngày làm việc/tháng", min_value=0, value=18)
            estado = st.selectbox("Estado", ESTADO_OPTIONS)

        submitted = st.form_submit_button("💾 Lưu", type="primary")
        if submitted:
            if not pr_code or not br or not bc:
                st.error("Bắt buộc nhập PR Code, BR, BC.")
            else:
                db.upsert_promoter({
                    "pr_code": pr_code.strip(),
                    "owner_code": owner_code.strip() or None,
                    "br": br.strip(),
                    "bc": bc.strip(),
                    "tipo": tipo,
                    "leader": leader.strip() or None,
                    "grupo": grupo.strip() or None,
                    "kpi_trabajo": kpi,
                    "cantidad_dia_trabajo": cantidad,
                    "estado": estado,
                    "activo": 1,
                })
                st.success(f"Đã lưu {pr_code}.")

with tab_edit:
    st.subheader("Chỉnh sửa hàng loạt")
    df = db.list_promoter()
    if df.empty:
        st.info("Chưa có dữ liệu.")
    else:
        edited = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            disabled=["pr_code"],
            height=500,
            key="pr_editor",
        )
        c1, c2 = st.columns([1, 4])
        if c1.button("💾 Lưu thay đổi", type="primary"):
            n = 0
            for _, r in edited.iterrows():
                if not r.get("pr_code"):
                    continue
                db.upsert_promoter(r.to_dict())
                n += 1
            st.success(f"Đã lưu {n} dòng.")
            st.rerun()
        st.divider()
        del_code = st.selectbox("Xoá PR", [""] + df["pr_code"].tolist())
        if del_code and st.button("🗑️ Xoá", type="secondary"):
            db.delete_promoter(del_code)
            st.success(f"Đã xoá {del_code}.")
            st.rerun()
