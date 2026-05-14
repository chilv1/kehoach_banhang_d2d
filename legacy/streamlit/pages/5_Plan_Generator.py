"""Plan Generator — tạo hàng loạt campaign DRAFT cho 1 tháng."""
from datetime import date

import pandas as pd
import streamlit as st

from lib import campaign, db, planner

st.set_page_config(page_title="Plan Generator", page_icon="⚙️", layout="wide")
db.init_db()

st.title("⚙️ Plan Generator — Sinh nhanh kế hoạch tháng")
st.caption(
    "Sinh hàng loạt campaign DRAFT cho 1 tháng dựa trên Ubicacion + PR. "
    "Ưu tiên prioridad thấp trước, khớp lịch traffic, cùng BC, "
    "không vượt số ngày làm việc của PR."
)

today = date.today()
c1, c2, c3 = st.columns([1, 1, 3])
year = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
month = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
month_key = f"{year:04d}-{month:02d}"

ubic = db.list_ubicacion()
prs = db.list_promoter()
existing = campaign.list_campaigns(month=month_key)

with c3:
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Ubic active",
               int((ubic.get("activo", 0) == 1).sum()) if not ubic.empty else 0)
    cc2.metric("PR active",
               int((prs.get("activo", 0) == 1).sum()) if not prs.empty else 0)
    cc3.metric("Campaign tháng này", len(existing))

st.divider()

st.subheader("⚙️ Tuỳ chọn")
o1, o2 = st.columns(2)
clear_draft = o1.checkbox("Xoá DRAFT cũ trong tháng trước khi sinh", value=True)
o2.info("DRAFT cũ sẽ bị thay; PLANNED/RUNNING/DONE không bị động đến.")

if st.button("🚀 Sinh kế hoạch", type="primary",
             disabled=ubic.empty or prs.empty):
    if clear_draft:
        n_del = campaign.clear_campaigns(month_key, only_status=["DRAFT"])
        st.info(f"Đã xoá {n_del} DRAFT cũ.")
    rows, warnings = planner.generate_draft_campaigns(
        ubic, prs, int(year), int(month)
    )
    n_created = campaign.bulk_create_campaigns(rows, actor="planner")
    st.success(
        f"✅ Đã sinh {n_created}/{len(rows)} campaign DRAFT. "
        f"Vào trang **Campaigns** để duyệt và chuyển PLANNED."
    )
    if warnings:
        with st.expander(f"⚠️ Thông báo ({len(warnings)})", expanded=False):
            st.dataframe(pd.DataFrame(warnings), use_container_width=True)

st.divider()

# Preview existing
st.subheader(f"📋 Campaign hiện có trong tháng {month_key}")
if existing.empty:
    st.info("Chưa có campaign nào.")
else:
    counts = existing.groupby("status").size().reset_index(name="so_luong")
    st.dataframe(counts, use_container_width=True, hide_index=True)
    st.dataframe(
        existing[["codigo", "fecha", "bc", "ubicacion_code",
                  "pr_code", "status", "prioridad", "notas"]],
        use_container_width=True, height=400, hide_index=True,
    )

st.divider()

# Hành động hàng loạt
st.subheader("🛠️ Hành động hàng loạt")
if existing.empty:
    st.caption("—")
else:
    a1, a2, a3 = st.columns([2, 2, 3])
    drafts = existing[existing["status"] == "DRAFT"]
    a1.metric("DRAFT", len(drafts))
    if a2.button("✅ Duyệt toàn bộ DRAFT → PLANNED",
                 disabled=drafts.empty):
        n = 0
        for cid in drafts["id"]:
            try:
                campaign.change_status(int(cid), "PLANNED",
                                       actor="bulk_approver",
                                       nota="Duyệt hàng loạt")
                n += 1
            except Exception:
                pass
        st.success(f"Đã duyệt {n} campaign.")
        st.rerun()
