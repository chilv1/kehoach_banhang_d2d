"""Import master data từ Campana Plan.xlsx, Export campaign tháng ra Excel."""
from datetime import date

import streamlit as st

from lib import campaign, db, excel_io

st.set_page_config(page_title="Import/Export", page_icon="📂", layout="wide")
db.init_db()

st.title("📂 Import / Export Excel")

tab_imp, tab_exp = st.tabs(["⬆️ Import master", "⬇️ Export campaigns"])

with tab_imp:
    st.subheader("Import Ubicacion + PR/Grupo từ Excel mẫu")
    st.caption(
        "File phải có 2 sheet: **Ubicacion** và **PR Grupo** (theo cấu trúc "
        "file `Campana Plan.xlsx`). Sau khi import master, qua trang "
        "**Plan Generator** để tự động sinh campaign cho tháng."
    )
    up = st.file_uploader("Chọn file .xlsx", type=["xlsx"])
    if up and st.button("⬆️ Import", type="primary"):
        try:
            counts = excel_io.import_master_xlsx(up)
            st.success(
                f"✅ Đã import: {counts['ubicacion']} điểm bán, "
                f"{counts['promoter']} promoters."
            )
        except Exception as e:
            st.error(f"Lỗi: {e}")

    st.divider()
    counts = db.stats_counts()
    cc = st.columns(4)
    cc[0].metric("Ubicaciones", counts["ubicacion"])
    cc[1].metric("Promoters", counts["promoter"])
    cc[2].metric("Campaigns", counts["campaign"])
    cc[3].metric("Campaigns DONE", counts["campaign_done"])

with tab_exp:
    st.subheader("Export campaign + kết quả ra Excel")
    today = date.today()
    c1, c2 = st.columns([1, 1])
    yr = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
    mo = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
    month_key = f"{yr:04d}-{mo:02d}"

    camps = campaign.list_campaigns(month=month_key)
    st.caption(f"Tháng {month_key}: **{len(camps)}** campaigns")
    if not camps.empty:
        data = excel_io.export_campaigns_xlsx(month_key)
        st.download_button(
            "⬇️ Tải Excel campaigns + results",
            data=data,
            file_name=f"campaigns_{month_key}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
    else:
        st.info("Chưa có campaign cho tháng này.")
