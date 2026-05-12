"""Plan generator + lịch hiển thị."""
from datetime import date

import pandas as pd
import streamlit as st

from lib import db
from lib.planner import generate_plan, plan_summary

st.set_page_config(page_title="Plan Generator", page_icon="🗓️", layout="wide")
db.init_db()

st.title("🗓️ Sinh kế hoạch bán hàng")

today = date.today()
c1, c2, c3 = st.columns([1, 1, 3])
year = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
month = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
month_key = f"{year:04d}-{month:02d}"

ubic = db.list_ubicacion()
prs = db.list_promoter()

with c3:
    st.metric("Ubicaciones (active)",
              int((ubic.get("activo", 0) == 1).sum()) if not ubic.empty else 0)
    st.metric("Promoters (active)",
              int((prs.get("activo", 0) == 1).sum()) if not prs.empty else 0)

st.divider()

cc1, cc2, cc3 = st.columns([1, 1, 3])
do_clear = cc1.checkbox("Xoá plan tháng trước khi sinh", value=True)
gen = cc2.button("🚀 Sinh kế hoạch", type="primary",
                  disabled=ubic.empty or prs.empty)
if gen:
    if do_clear:
        db.clear_plan(month_key)
    rows, warnings = generate_plan(ubic, prs, int(year), int(month))
    db.insert_plan_rows(rows)
    summary = plan_summary(pd.DataFrame(rows)) if rows else {
        "total": 0, "assigned": 0, "unassigned": 0, "by_bc": {}}
    st.success(
        f"✅ Đã sinh {summary['total']} dòng plan — "
        f"{summary['assigned']} đã ghép PR, {summary['unassigned']} chưa ghép."
    )
    if warnings:
        with st.expander(f"⚠️ Thông báo ({len(warnings)})"):
            st.dataframe(pd.DataFrame(warnings), use_container_width=True)

st.divider()

plan_df = db.list_plan(month_key)
st.subheader(f"📅 Kế hoạch tháng {month_key}")

if plan_df.empty:
    st.info("Chưa có plan. Nhấn 'Sinh kế hoạch' phía trên.")
else:
    summary = plan_summary(plan_df)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng ca", summary["total"])
    m2.metric("Đã ghép PR", summary["assigned"])
    m3.metric("Chưa ghép", summary["unassigned"])
    m4.metric("BC tham gia", len(summary["by_bc"]))

    # Filters
    f1, f2, f3 = st.columns(3)
    bcs = sorted(plan_df["bc"].dropna().unique().tolist())
    sel_bc = f1.multiselect("BC", bcs, default=bcs)
    only_unassigned = f2.checkbox("Chỉ xem chưa ghép", value=False)

    view = plan_df[plan_df["bc"].isin(sel_bc)] if sel_bc else plan_df
    if only_unassigned:
        view = view[view["pr_code"].isna()]

    tab1, tab2, tab3 = st.tabs(["📋 Danh sách", "🗓️ Lịch (pivot)", "👥 Theo PR"])

    with tab1:
        st.dataframe(view, use_container_width=True, height=520)

    with tab2:
        if view.empty:
            st.info("Không có dữ liệu.")
        else:
            pivot = view.pivot_table(
                index=["bc", "ubicacion_code"],
                columns="fecha",
                values="pr_code",
                aggfunc="first",
            ).fillna("")
            st.dataframe(pivot, use_container_width=True, height=520)

    with tab3:
        if view.empty:
            st.info("Không có dữ liệu.")
        else:
            by_pr = view.dropna(subset=["pr_code"]).groupby("pr_code").agg(
                so_ca=("ubicacion_code", "count"),
                bc=("bc", "first"),
                grupo=("grupo", "first"),
            ).reset_index().sort_values("so_ca", ascending=False)
            st.dataframe(by_pr, use_container_width=True, height=520)
