# ProjectWeb — MS Project clone screenshots

Demo mockup cho 9 chức năng của ProjectWeb (MS Project clone web app).

> 💡 Các ảnh PNG full-resolution đang ở feature branch `claude/excel-file-upload-FK94T`. Một số bản JPG nén nhỏ đã push vào branch `main`.

## 1. 🔐 Login / Register (Phase 8 Auth)

JWT HS256 + pbkdf2 (200k iterations) — stdlib-only, không cần thư viện `cryptography`. User đầu tiên đăng ký tự động thành admin.

![Login](https://raw.githubusercontent.com/chilv1/kehoach_banhang_d2d/claude/excel-file-upload-FK94T/mockup/projectweb/screenshots/01_login.png)

## 2. 📁 Projects list

CRUD project — tạo project mới với start date, click tên để mở Gantt view.

![Projects](https://raw.githubusercontent.com/chilv1/kehoach_banhang_d2d/claude/excel-file-upload-FK94T/mockup/projectweb/screenshots/02_projects.png)

## 3. 📊 Gantt view (Phase 2 CPM)

Critical path đỏ, normal xanh, milestone tím, today line đỏ đứt. Drag bar đổi ngày, double-click xoá, kéo % progress trên bar.

![Gantt](https://raw.githubusercontent.com/chilv1/kehoach_banhang_d2d/claude/excel-file-upload-FK94T/mockup/projectweb/screenshots/03_gantt.png)

## 4. 📋 Task Grid (Phase 1 WBS)

Bảng kiểu MS Project: ID, WBS auto, Name, Duration, Start/Finish, Slack, %, Predecessors, Status. Double-click edit inline; `⇨ Indent` / `⇦ Outdent` tự cập nhật WBS.

![Grid](https://raw.githubusercontent.com/chilv1/kehoach_banhang_d2d/claude/excel-file-upload-FK94T/mockup/projectweb/screenshots/04_grid.png)

## 5. 🧑 Resources (Phase 3)

3 loại resource: **WORK** (người, Std Rate $/h + Max Units), **MATERIAL** (per-unit cost), **COST** (chi phí thuần).

![Resources](https://raw.githubusercontent.com/chilv1/kehoach_banhang_d2d/claude/excel-file-upload-FK94T/mockup/projectweb/screenshots/05_resources.png)

## 6. 📈 Tracking — Baseline + Variance (Phase 4)

Snapshot kế hoạch gốc (Baseline #0..#10). So sánh baseline vs current → SLIPPING khi `Finish var > 0`.

![Tracking](https://raw.githubusercontent.com/chilv1/kehoach_banhang_d2d/claude/excel-file-upload-FK94T/mockup/projectweb/screenshots/06_tracking.png)

## 7. ⚖️ Resource Leveling (Phase 5)

Auto-resolve over-allocation. Thuật toán greedy: với mỗi ngày overallocated, chọn task priority THẤP nhất (slack cao nhất tie-break) để delay 1 working day, set `constraint_type=SNET`, rồi re-run CPM. Loop tới converged.

![Leveling](https://raw.githubusercontent.com/chilv1/kehoach_banhang_d2d/claude/excel-file-upload-FK94T/mockup/projectweb/screenshots/07_leveling.png)

## 8. 💰 Earned Value Management (Phase 6)

12 metrics PMI: **BAC** (budget), **BCWS** (planned), **BCWP** (earned), **ACWP** (actual), **CV/SV** (variance), **CPI/SPI** (index), **EAC/ETC/VAC/TCPI** (forecast). Diễn giải tiếng Việt phía dưới.

![EVM](https://raw.githubusercontent.com/chilv1/kehoach_banhang_d2d/claude/excel-file-upload-FK94T/mockup/projectweb/screenshots/08_evm.png)

## 9. 📂 XML Import / Export (Phase 7)

Export `project_X.xml` chứa toàn bộ tasks/deps/resources/assignments theo schema giản lược MS Project. Import XML tạo project mới với UID map lại.

![XML](https://raw.githubusercontent.com/chilv1/kehoach_banhang_d2d/claude/excel-file-upload-FK94T/mockup/projectweb/screenshots/09_xml.png)

---

## Quy trình tổng thể (workflow 8 phases)

```
1. Đăng nhập (Phase 8)
   ↓
2. Tạo Project
   ↓
3. Nhập Task + WBS (Phase 1)
   ↓
4. Tạo Dependencies (FS/SS/FF/SF + lag)
   ↓
5. Phân Resources (Phase 3)
   ↓
6. Schedule CPM (Phase 2)
   ↓
7. Resource Leveling (Phase 5)
   ↓
8. Save Baseline (Phase 4)
   ↓
9. Track % complete (Phase 4)
   ↓
10. EVM Report (Phase 6)
   ↓
11. XML Export (Phase 7)
```

## Endpoints chính

| Phase | Endpoint |
|---|---|
| 8 | `POST /api/auth/{register,login,me}` |
| 0 | `GET/POST/DELETE /api/projects` |
| 2 | `POST /api/projects/{id}/schedule` |
| 1 | `POST /api/tasks/{id}/{indent,outdent}` |
| 3 | `POST /api/projects/{id}/costs/recompute` |
| 4 | `POST /api/baselines`, `GET /api/projects/{id}/variance` |
| 5 | `GET /api/projects/{id}/overallocations`, `POST /level` |
| 6 | `GET /api/projects/{id}/evm` |
| 7 | `GET /api/projects/{id}/export-xml`, `POST /api/projects/import-xml` |

Tổng cộng **47 REST endpoints** + **full UI** cho 8 phase.

## Setup nhanh

```bash
git clone https://github.com/chilv1/kehoach_banhang_d2d
cd kehoach_banhang_d2d

# Backend
cd backend
pip install -r requirements.txt
python3 -m app.seed.demo
uvicorn app.main:app --reload --port 8500
# → Swagger: http://127.0.0.1:8500/docs

# Frontend (terminal khác)
cd ../frontend
npm install
npm run dev
# → http://localhost:5173
```

## File mockup

- `mockup/projectweb/index.html` — interactive mockup (mở trong browser)
- `mockup/projectweb/screenshots/` — 9 PNG screenshots
