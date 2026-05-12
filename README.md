# Kế Hoạch Bán Hàng D2D

Ứng dụng Streamlit lập kế hoạch bán hàng theo điểm (Ubicacion) và nhân lực (PR/Grupo) cho từng BC/Branch, mô phỏng quy trình của file `Campana Plan.xlsx`.

## Tính năng

- **CRUD Ubicacion**: quản lý các điểm bán (CP) với toạ độ GPS, lịch traffic, ưu tiên, Meta/Gasto/Merchandising.
- **CRUD PR/Grupo**: quản lý promoter, nhóm làm việc, KPI, số ngày làm việc tối đa.
- **Plan Generator**: sinh lịch tháng tự động theo:
  - Ưu tiên (Prioridad) — vị trí ưu tiên thấp được bán trước.
  - Lịch traffic (WEEKDAY / WEEKEND / ngày cụ thể trong tuần).
  - Ràng buộc nguồn lực (PR cùng BC, không vượt `Cantidad Día Trabajo`).
- **Dashboard**: thống kê Meta vs Resultado, phân bố theo BC, coverage, chi phí.
- **Excel I/O**: import dữ liệu từ file `Campana Plan.xlsx`, export lịch ra Excel.

## Cài đặt

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Cấu trúc

```
app.py              # Trang Home + navigation
pages/
  1_Ubicacion.py    # Quản lý điểm bán
  2_PR_Grupo.py     # Quản lý promoter
  3_Plan.py         # Sinh kế hoạch
  4_Dashboard.py    # Báo cáo thống kê
  5_Import_Export.py # Import/Export Excel
lib/
  db.py             # SQLite layer
  planner.py        # Thuật toán sinh lịch
  excel_io.py       # Đọc/ghi Excel
data/
  app.db            # SQLite database (auto-generated)
```
