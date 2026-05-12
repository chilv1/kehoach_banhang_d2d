"""Hệ thống quản lý Campaign (chương trình bán hàng) D2D — Streamlit."""
import streamlit as st

from lib import db
from lib.db import STATUSES

st.set_page_config(
    page_title="Quản lý Campaign D2D",
    page_icon="🎯",
    layout="wide",
)
db.init_db()

st.title("🎯 Hệ thống quản lý Campaign bán hàng D2D")
st.caption(
    "Lập, theo dõi và đóng các chương trình bán hàng (campaign) theo "
    "vị trí (Ubicacion) và nguồn lực (PR/Grupo). Mỗi campaign có quy "
    "trình trạng thái rõ ràng từ DRAFT → DONE."
)

st.divider()

c = db.stats_counts()
m = st.columns(4)
m[0].metric("Ubicaciones", c["ubicacion"])
m[1].metric("Promoters", c["promoter"])
m[2].metric("Campaigns", c["campaign"])
m[3].metric("Campaigns DONE", c["campaign_done"])

st.divider()

col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("🔄 Quy trình campaign")
    st.markdown(
        """
1. **DRAFT** — vừa tạo (thủ công hoặc qua Plan Generator)
2. **PLANNED** — đã duyệt, sẵn sàng chạy
3. **RUNNING** — đang triển khai
4. **DONE** — đã hoàn tất, có kết quả + checklist
5. **CANCELLED** — huỷ
        """
    )
    st.code(" → ".join(STATUSES[:-1]) + "\n         ↓\n    CANCELLED",
            language=None)

with col2:
    st.subheader("📌 Các bước sử dụng")
    st.markdown(
        """
1. **📍 Ubicacion** — nhập danh mục điểm bán (master data).
2. **👥 PR / Grupo** — nhập danh sách promoter và nhóm.
3. **⚙️ Plan Generator** — tự động sinh campaign DRAFT cho 1 tháng,
   theo prioridad + lịch traffic + ràng buộc nguồn lực.
4. **🎯 Campaigns** — duyệt DRAFT → PLANNED, quản lý qua Kanban /
   list / lịch; xem chi tiết & log từng campaign.
5. **📝 Campaign Form** — tạo / sửa từng campaign thủ công (form đầy
   đủ Meta / Gasto / Merchandising).
6. **✅ Resultados** — ghi nhận kết quả thực tế + checklist, đóng
   campaign sang DONE.
7. **📊 Dashboard** — theo dõi funnel trạng thái, Meta vs Resultado,
   chi phí, tải PR, bản đồ.
8. **📂 Import/Export** — import master từ file `Campana Plan.xlsx`,
   export campaign + result ra Excel.
        """
    )

st.divider()
st.info("👈 Chọn trang ở thanh bên trái để bắt đầu.")
