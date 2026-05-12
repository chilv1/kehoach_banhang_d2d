"""Import từ file Campana Plan.xlsx, export plan ra Excel."""
from datetime import date

import streamlit as st

from lib import db, excel_io

st.set_page_config(page_title="Import/Export", page_icon="📂", layout="wide")
db.init_db()

st.title("📂 Import / Export Excel")

tab_imp, tab_exp = st.tabs(["⬆️ Import", "⬇️ Export"])

with tab_imp:
    st.subheader("Import dữ liệu từ Campana Plan.xlsx")
    st.caption(
        "File phải có 2 sheet: **Ubicacion** (master danh sách điểm bán) "
        "và **PR Grupo** (danh sách promoter). Cấu trúc giống file mẫu."
    )
    uploaded = st.file_uploader("Chọn file .xlsx", type=["xlsx"])
    if uploaded and st.button("⬆️ Import", type="primary"):
        try:
            counts = excel_io.import_excel(uploaded)
            st.success(
                f"✅ Đã import: {counts['ubicacion']} điểm bán, "
                f"{counts['promoter']} promoters."
            )
        except Exception as e:
            st.error(f"Lỗi import: {e}")

    st.divider()
    counts = db.stats_counts()
    c1, c2 = st.columns(2)
    c1.metric("Ubicaciones hiện có", counts["ubicacion"])
    c2.metric("Promoters hiện có", counts["promoter"])

with tab_exp:
    st.subheader("Export kế hoạch ra Excel")
    today = date.today()
    c1, c2 = st.columns([1, 1])
    year = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
    month = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
    month_key = f"{year:04d}-{month:02d}"

    plan = db.list_plan(month_key)
    st.caption(f"Plan tháng {month_key}: **{len(plan)}** dòng.")
    if not plan.empty:
        data = excel_io.export_plan_xlsx(month_key)
        st.download_button(
            "⬇️ Tải file Excel kế hoạch",
            data=data,
            file_name=f"plan_{month_key}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
    else:
        st.info("Chưa có plan cho tháng này.")
