"""Bảng điều phối Campaign — list / filter / Kanban / chuyển trạng thái."""
from datetime import date

import pandas as pd
import streamlit as st

from lib import campaign, db
from lib.db import STATUSES, TRANSITIONS

st.set_page_config(page_title="Campaigns", page_icon="🎯", layout="wide")
db.init_db()

st.title("🎯 Quản lý Campaign")
st.caption("Danh sách + Kanban + chuyển trạng thái các chương trình bán hàng.")

# ---------- Filters ----------
today = date.today()
c1, c2, c3, c4 = st.columns([1, 1, 2, 2])
year = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
month = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
month_key = f"{year:04d}-{month:02d}"

all_camps = campaign.list_campaigns(month=month_key)
all_bcs = sorted(all_camps["bc"].dropna().unique().tolist()) if not all_camps.empty else []
sel_bc = c3.multiselect("BC", all_bcs, default=all_bcs)
sel_status = c4.multiselect("Status", STATUSES, default=STATUSES)

camps = campaign.list_campaigns(month=month_key, status=sel_status, bc=sel_bc)

# ---------- Top metrics ----------
m_cols = st.columns(len(STATUSES) + 1)
m_cols[0].metric("Tổng", len(camps))
for i, s in enumerate(STATUSES, start=1):
    cnt = int((camps["status"] == s).sum()) if not camps.empty else 0
    m_cols[i].metric(s, cnt)

st.divider()

tab_list, tab_kanban, tab_calendar, tab_detail = st.tabs(
    ["📋 Danh sách", "🗂️ Kanban", "🗓️ Lịch", "🔍 Chi tiết / Đổi trạng thái"]
)

# ---------- LIST ----------
with tab_list:
    if camps.empty:
        st.info("Không có campaign nào với bộ lọc hiện tại.")
    else:
        cols = ["id", "codigo", "fecha", "bc", "ubicacion_code", "distrito",
                "tipo_dfcp", "pr_code", "grupo", "status", "prioridad",
                "horario", "notas"]
        cols = [c for c in cols if c in camps.columns]
        st.dataframe(camps[cols], use_container_width=True, height=520,
                     hide_index=True)
        csv = camps.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Tải CSV", data=csv,
                           file_name=f"campaigns_{month_key}.csv",
                           mime="text/csv")

# ---------- KANBAN ----------
with tab_kanban:
    if camps.empty:
        st.info("Không có campaign.")
    else:
        kcols = st.columns(len(STATUSES))
        for i, s in enumerate(STATUSES):
            with kcols[i]:
                subset = camps[camps["status"] == s]
                st.markdown(f"### {s}\n_{len(subset)}_")
                for _, r in subset.iterrows():
                    label = (f"**{r['codigo']}**\n"
                             f"{r['fecha']} · {r['bc']} · {r['ubicacion_code']}\n"
                             f"PR: {r.get('pr_code') or '—'}")
                    with st.container(border=True):
                        st.markdown(label)

# ---------- CALENDAR ----------
with tab_calendar:
    if camps.empty:
        st.info("Không có campaign.")
    else:
        pivot = camps.pivot_table(
            index=["bc", "ubicacion_code"],
            columns="fecha",
            values="status",
            aggfunc="first",
        ).fillna("")
        st.dataframe(pivot, use_container_width=True, height=520)
        st.caption("Mỗi ô = trạng thái campaign tại (vị trí, ngày).")

# ---------- DETAIL / STATUS ----------
with tab_detail:
    if camps.empty:
        st.info("Không có campaign để xem.")
    else:
        # selectbox theo codigo
        choices = camps.apply(
            lambda r: f"{r['codigo']} | {r['fecha']} | {r['ubicacion_code']} | {r['status']}",
            axis=1,
        ).tolist()
        idx = st.selectbox("Chọn campaign", range(len(choices)),
                           format_func=lambda i: choices[i])
        cid = int(camps.iloc[idx]["id"])
        c = campaign.get_campaign(cid)
        if c is None:
            st.error("Không tìm thấy campaign.")
            st.stop()

        gi1, gi2, gi3, gi4 = st.columns(4)
        gi1.metric("Status", c["status"])
        gi2.metric("Ngày", c["fecha"])
        gi3.metric("BC", c["bc"])
        gi4.metric("Vị trí", c["ubicacion_code"])

        st.markdown(f"**Mã**: `{c['codigo']}`  ·  **Tên**: {c.get('nombre') or '—'}  ·  "
                    f"**PR**: {c.get('pr_code') or '—'}  ·  **Grupo**: {c.get('grupo') or '—'}")
        if c.get("notas"):
            st.info(c["notas"])

        # Hành động chuyển trạng thái
        st.subheader("Chuyển trạng thái")
        allowed = sorted(TRANSITIONS.get(c["status"], set()))
        if not allowed:
            st.warning("Không có trạng thái kế tiếp.")
        else:
            colA, colB = st.columns([2, 5])
            new_status = colA.selectbox("Trạng thái mới", allowed,
                                        key=f"newst_{cid}")
            nota = colB.text_input("Ghi chú", key=f"note_{cid}")
            if st.button(f"➡️ Chuyển sang {new_status}", type="primary",
                         key=f"go_{cid}"):
                try:
                    campaign.change_status(cid, new_status, nota=nota)
                    st.success(f"Đã chuyển {c['status']} → {new_status}.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

        st.divider()
        st.subheader("Lịch sử")
        log = campaign.campaign_log(cid)
        if log.empty:
            st.caption("Chưa có log.")
        else:
            st.dataframe(log[["at", "accion", "old_status", "new_status",
                              "nota", "actor"]],
                         use_container_width=True, hide_index=True)

        st.divider()
        if st.button("🗑️ Xoá campaign này", type="secondary",
                     key=f"del_{cid}"):
            campaign.delete_campaign(cid)
            st.success("Đã xoá.")
            st.rerun()
