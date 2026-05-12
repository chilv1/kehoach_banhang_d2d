"""Project Gantt (MS Project style) — mỗi Ubicacion = 1 task.

Cột:
  • Vị trí (Ubicacion)
  • Start / End / Duration
  • Resources (PR/Grupo)
  • Progress %
Visualization:
  • Thanh task từ start → end
  • Markers cho từng ngày campaign (theo status)
  • Vertical line = hôm nay
  • Conflict detection panel
"""
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib import campaign, db
from lib.gantt import build_tasks, detect_conflicts, resource_load

st.set_page_config(page_title="Project Gantt", page_icon="📈", layout="wide")
db.init_db()

st.title("📈 Project Gantt — kế hoạch & tiến độ theo task")
st.caption(
    "Style Microsoft Project: mỗi vị trí = 1 task có ngày bắt đầu / kết thúc / "
    "nguồn lực / tiến độ. Tự phát hiện xung đột lịch & quá tải."
)

# ---------- Filters ----------
today = date.today()
c1, c2, c3, c4 = st.columns([1, 1, 2, 2])
year = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
month = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
month_key = f"{year:04d}-{month:02d}"

camps = campaign.list_campaigns(month=month_key)
ubic = db.list_ubicacion()
prs = db.list_promoter()

if camps.empty:
    st.info(f"Chưa có campaign trong tháng {month_key}. Vào **Plan Generator** để sinh.")
    st.stop()

all_bcs = sorted(camps["bc"].dropna().unique().tolist())
sel_bc = c3.multiselect("BC", all_bcs, default=all_bcs)
all_status = sorted(camps["status"].unique())
sel_status = c4.multiselect("Status", all_status, default=all_status)

df = camps.copy()
if sel_bc:
    df = df[df["bc"].isin(sel_bc)]
if sel_status:
    df = df[df["status"].isin(sel_status)]

if df.empty:
    st.warning("Không có campaign với bộ lọc hiện tại.")
    st.stop()

# ---------- Build tasks ----------
tasks = build_tasks(df, ubic)
conflicts = detect_conflicts(df, prs, ubic)

# ---------- Summary KPIs ----------
st.divider()
k = st.columns(6)
k[0].metric("Tổng task", len(tasks))
k[1].metric("Tổng ca", int(tasks["total_camps"].sum()))
k[2].metric("Hoàn tất", int(tasks["done_camps"].sum()))
k[3].metric("Đang chạy", int(tasks["running_camps"].sum()))
k[4].metric("Tiến độ TB",
            f"{tasks['progress_pct'].mean():.0f}%" if len(tasks) else "0%")
k[5].metric("Xung đột", len(conflicts),
            delta=None if conflicts.empty else "⚠️", delta_color="inverse")

tab_table, tab_gantt, tab_resource, tab_conflict = st.tabs([
    "📋 Task table", "📊 Gantt biểu đồ",
    "🧑 Tải nguồn lực", "⚠️ Xung đột",
])

# ---------- TAB 1: Task table ----------
with tab_table:
    st.markdown("**Mỗi dòng = 1 task (1 vị trí).** Sort/filter để tìm task chậm tiến độ.")
    show = tasks.copy()
    show["task_start"] = show["task_start"].dt.strftime("%Y-%m-%d")
    show["task_end"] = show["task_end"].dt.strftime("%Y-%m-%d")
    show = show[[
        "ubicacion_code", "bc", "distrito", "prioridad",
        "task_start", "task_end", "duration_days",
        "total_camps", "done_camps", "running_camps",
        "planned_camps", "draft_camps", "cancelled_camps",
        "resources", "n_resources", "progress_pct",
    ]].rename(columns={
        "ubicacion_code": "Vị trí",
        "bc": "BC",
        "distrito": "Distrito",
        "prioridad": "Prio",
        "task_start": "Start",
        "task_end": "End",
        "duration_days": "Dur (ngày)",
        "total_camps": "Tổng",
        "done_camps": "DONE",
        "running_camps": "RUN",
        "planned_camps": "PLAN",
        "draft_camps": "DRAFT",
        "cancelled_camps": "CANC",
        "resources": "Nguồn lực",
        "n_resources": "#PR",
        "progress_pct": "% Tiến độ",
    })
    st.dataframe(
        show,
        use_container_width=True,
        height=520,
        hide_index=True,
        column_config={
            "% Tiến độ": st.column_config.ProgressColumn(
                "% Tiến độ", min_value=0, max_value=100, format="%d%%"
            ),
        },
    )
    csv = show.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Tải CSV task", data=csv,
                        file_name=f"tasks_{month_key}.csv", mime="text/csv")

# ---------- TAB 2: Gantt visualization ----------
with tab_gantt:
    st.markdown(
        "Thanh dài = khoảng thời gian task (start → end). "
        "Marker = ngày có campaign (màu theo status). Đường dọc đỏ = hôm nay."
    )
    sort_by = st.radio(
        "Sắp xếp",
        ["BC + Prioridad", "Start sớm nhất", "Progress thấp nhất"],
        horizontal=True,
    )
    g = tasks.copy()
    if sort_by == "Start sớm nhất":
        g = g.sort_values("task_start")
    elif sort_by == "Progress thấp nhất":
        g = g.sort_values("progress_pct")
    else:
        g = g.sort_values(["bc", "prioridad", "ubicacion_code"])

    # Build y-label kèm progress
    g["y_label"] = g.apply(
        lambda r: f"{r['ubicacion_code']} · {r['bc']} · {int(r['progress_pct'])}%",
        axis=1,
    )
    g["task_end_excl"] = g["task_end"] + pd.Timedelta(days=1)

    # Background bar (task span)
    fig = px.timeline(
        g, x_start="task_start", x_end="task_end_excl", y="y_label",
        color="progress_pct",
        color_continuous_scale=[(0, "#ef4444"), (0.5, "#f59e0b"), (1.0, "#10b981")],
        range_color=[0, 100],
        hover_data={
            "ubicacion_code": True, "bc": True, "distrito": True,
            "duration_days": True, "total_camps": True,
            "resources": True, "progress_pct": True,
            "y_label": False, "task_end_excl": False,
        },
    )
    fig.update_yaxes(autorange="reversed", title="")

    # Marker layer: individual campaign days
    STATUS_COLORS = {
        "DRAFT": "#9ca3af", "PLANNED": "#3b82f6", "RUNNING": "#f59e0b",
        "DONE": "#10b981", "CANCELLED": "#ef4444",
    }
    df_dots = df.merge(
        g[["ubicacion_code", "y_label"]], on="ubicacion_code", how="inner"
    )
    df_dots["fecha_dt"] = pd.to_datetime(df_dots["fecha"]) + pd.Timedelta(hours=12)
    for status, color in STATUS_COLORS.items():
        sub = df_dots[df_dots["status"] == status]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["fecha_dt"], y=sub["y_label"],
            mode="markers",
            marker=dict(color=color, size=9, symbol="square",
                        line=dict(color="white", width=1)),
            name=status,
            customdata=sub[["codigo", "pr_code", "notas"]].values,
            hovertemplate=("<b>%{customdata[0]}</b><br>"
                            "Ngày: %{x|%Y-%m-%d}<br>"
                            "PR: %{customdata[1]}<br>"
                            "Status: " + status + "<br>"
                            "Notas: %{customdata[2]}<extra></extra>"),
            showlegend=True,
        ))

    # Today marker
    today_ts = pd.Timestamp(today)
    fig.add_vline(x=today_ts, line_width=2, line_dash="dash",
                  line_color="red", annotation_text="Hôm nay",
                  annotation_position="top right")

    fig.update_xaxes(title="Ngày", tickformat="%d/%m", dtick=86400000.0 * 2)
    fig.update_layout(
        height=max(500, 24 * len(g)),
        margin=dict(l=10, r=10, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        coloraxis_colorbar=dict(title="% Done", x=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 3: Resource load ----------
with tab_resource:
    load = resource_load(df, prs)
    if load.empty:
        st.info("Chưa có campaign được phân PR.")
    else:
        st.markdown(
            "**Tải công việc từng PR**. Cột `over` = ⚠️ nếu vượt capacity (cần phân lại)."
        )
        rl = load.copy()
        rl["over_icon"] = rl["over"].map({True: "⚠️", False: "✓"})
        st.dataframe(
            rl[["pr_code", "bc", "grupo", "tipo",
                "days_planned", "cantidad_dia_trabajo",
                "utilization_pct", "over_icon"]].rename(columns={
                "pr_code": "PR", "bc": "BC", "grupo": "Grupo", "tipo": "Loại",
                "days_planned": "Đã xếp", "cantidad_dia_trabajo": "Capacity",
                "utilization_pct": "Util %", "over_icon": "",
            }),
            use_container_width=True, height=500, hide_index=True,
            column_config={
                "Util %": st.column_config.ProgressColumn(
                    "Util %", min_value=0, max_value=150, format="%.0f%%"
                ),
            },
        )
        st.bar_chart(rl.set_index("pr_code")["days_planned"].sort_values(ascending=False).head(30),
                     height=300)

# ---------- TAB 4: Conflicts ----------
with tab_conflict:
    if conflicts.empty:
        st.success("✅ Không phát hiện xung đột.")
    else:
        st.markdown(f"**{len(conflicts)} vấn đề được phát hiện.**")
        # Group by severity
        sev_count = conflicts.groupby("severity").size().to_dict()
        sc = st.columns(len(sev_count))
        for i, (k, v) in enumerate(sev_count.items()):
            sc[i].metric(k, v)
        sel_sev = st.multiselect(
            "Lọc severity", sorted(conflicts["severity"].unique()),
            default=sorted(conflicts["severity"].unique()),
        )
        view = conflicts[conflicts["severity"].isin(sel_sev)]
        sel_tipo = st.multiselect(
            "Loại xung đột", sorted(conflicts["tipo"].unique()),
            default=sorted(conflicts["tipo"].unique()),
        )
        if sel_tipo:
            view = view[view["tipo"].isin(sel_tipo)]
        st.dataframe(view, use_container_width=True, height=480, hide_index=True)

        st.divider()
        st.markdown("**📖 Giải thích loại xung đột**")
        st.markdown("""
- 🔴 **PR overlap** — cùng 1 PR bị xếp 2+ campaign trong 1 ngày → phải phân lại.
- 🔴 **Vị trí trùng** — cùng 1 vị trí có 2+ campaign trong 1 ngày → vi phạm rule.
- 🟠 **Vượt capacity** — PR bị xếp nhiều hơn `cantidad_dia_trabajo` → cần cắt bớt hoặc bổ sung PR.
- 🟡 **Chưa phân PR** — campaign DRAFT chưa có PR → cần gán thủ công.
- 🟡 **Ngoài lịch traffic** — campaign rơi vào ngày không khớp `Fecha Alta Traffico` của Ubicacion.
        """)
