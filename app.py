"""Ứng dụng lập kế hoạch bán hàng D2D — Streamlit Home page."""
import streamlit as st

from lib import db

st.set_page_config(
    page_title="Kế hoạch bán hàng D2D",
    page_icon="📋",
    layout="wide",
)

db.init_db()

st.title("📋 Kế hoạch bán hàng D2D")
st.caption(
    "Lập kế hoạch theo vị trí (Ubicacion) + nguồn lực (PR/Grupo), "
    "tự động phân bổ theo BC/Branch và ưu tiên — kèm dashboard thống kê."
)

st.divider()

counts = db.stats_counts()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ubicaciones", counts["ubicacion"])
c2.metric("Promoters", counts["promoter"])
c3.metric("Plan rows", counts["plan"])
c4.metric("Resultados", counts["resultado"])

st.divider()

st.markdown(
    """
### Hướng dẫn sử dụng

1. **Ubicacion** — nhập / import các điểm bán (CP). Mỗi điểm có:
   - BR, BC, Distrito, Tipo (Mercado / BTS / Rural / ...)
   - Lịch traffic (WEEKDAY / WEEKEND / MONDAY ... SUNDAY)
   - **Prioridad** (1 = ưu tiên cao nhất)
   - Số ngày cần campaign trong tháng
   - Meta (chỉ tiêu), Gasto (chi phí), Merchandising
2. **PR / Grupo** — nhập / import nhân lực:
   - Mỗi PR thuộc 1 BC, 1 Grupo
   - Số ngày làm việc tối đa / tháng
3. **Plan** — chọn tháng, nhấn **Sinh kế hoạch** để tự động ghép:
   - Ưu tiên prioridad thấp được xếp trước
   - Khớp với lịch traffic của điểm
   - Ưu tiên PR cùng BC, không vượt capacity
4. **Dashboard** — xem thống kê coverage / Meta vs Resultado / chi phí.
5. **Import/Export** — đọc dữ liệu từ file `Campana Plan.xlsx`, xuất kế hoạch ra Excel.

> 👈 Chọn trang từ thanh bên trái để bắt đầu.
"""
)
