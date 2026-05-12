# Hệ thống quản lý Campaign bán hàng D2D

Ứng dụng Streamlit để **lập, theo dõi và đóng các chương trình bán hàng (campaign)** theo từng vị trí (Ubicacion) và nguồn lực (PR/Grupo) — mô phỏng workflow của file `Campana Plan.xlsx`.

## Mô hình

- **Ubicacion** — danh mục điểm bán (CP01…) với GPS, lịch traffic, Meta/Gasto/Merch mặc định.
- **PR / Grupo** — danh sách promoter, nhóm làm việc, KPI, capacity ngày/tháng.
- **Campaign** — 1 chương trình bán hàng tại 1 vị trí vào 1 ngày, có:
  - mã `CMP-YYYYMM-CPxx-NN`, tên, PR phân công, leader, grupo
  - Meta (chỉ tiêu), Gasto (chi phí), Merchandising kế hoạch
  - **Trạng thái** (status): `DRAFT → PLANNED → RUNNING → DONE` (hoặc `CANCELLED`)
  - Mọi thay đổi trạng thái được ghi log (`campaign_log`)
- **Campaign Result** — kết quả thực tế + checklist khi đóng campaign.

```
DRAFT → PLANNED → RUNNING → DONE
            ↓        ↓
        CANCELLED  CANCELLED
```

## Các trang

| Trang | Mục đích |
|---|---|
| 📍 **Ubicacion** | CRUD điểm bán (form + bulk editor) |
| 👥 **PR / Grupo** | CRUD nhân lực |
| ⚙️ **Plan Generator** | Sinh hàng loạt campaign DRAFT cho 1 tháng theo prioridad + lịch traffic + ràng buộc nguồn lực |
| 🎯 **Campaigns** | Danh sách / Kanban / Lịch / chuyển trạng thái / xem log |
| 📝 **Campaign Form** | Tạo / sửa 1 campaign thủ công (form đầy đủ Meta + Gasto + Merch) |
| ✅ **Resultados** | Ghi nhận kết quả + checklist, đóng campaign sang DONE |
| 📊 **Dashboard** | Funnel trạng thái, phân bố ngày/BC, Meta vs Resultado, chi phí, tải PR, map |
| 📂 **Import/Export** | Import master từ file Excel mẫu, export campaign/result tháng |

## Thuật toán Plan Generator

Sinh DRAFT campaigns cho 1 tháng bằng 4 pass (ưu tiên trước bán trước):

1. **Pass 1** — `prioridad` thấp được xếp trước; ngày khớp `Fecha Alta Traffico`; PR cùng BC.
2. **Pass 2** — nếu thiếu PR cùng BC, cho phép PR khác BC (ghi chú vào campaign).
3. **Pass 3** — vẫn thiếu? cho phép ngày ngoài lịch traffic, ưu tiên PR cùng BC.
4. **Pass 4** — không có PR phù hợp → tạo campaign chưa phân công, để team tự gán.

Mỗi PR không vượt `cantidad_dia_trabajo`; mỗi (PR, ngày) tối đa 1 ca; mỗi (Ubicacion, ngày) tối đa 1 campaign.

## Cài đặt

```bash
pip install -r requirements.txt
streamlit run app.py
```

DB SQLite tự tạo trong `data/app.db`.

## Cấu trúc code

```
app.py                       # Home page
lib/
  db.py                      # SQLite schema + helpers
  campaign.py                # CRUD + state machine
  planner.py                 # Thuật toán sinh DRAFT campaigns
  excel_io.py                # Import/Export Excel
pages/
  1_Ubicacion.py
  2_PR_Grupo.py
  3_Campaigns.py             # List / Kanban / Calendar / Status
  4_Campaign_Form.py         # Form tạo/sửa
  5_Plan_Generator.py
  6_Resultados.py
  7_Dashboard.py
  8_Import_Export.py
data/app.db                  # SQLite (auto-gen, gitignored)
```
