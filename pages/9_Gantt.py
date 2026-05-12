"""Biểu đồ Gantt cho kế hoạch bán hàng — 3 góc nhìn:
  • Theo Vị trí (Ubicacion)
  • Theo Đội (Grupo / BC)
  • Theo Promoter
Mỗi campaign = 1 thanh kéo dài đúng 1 ngày, màu theo status.
"""
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from lib import campaign, db

st.set_page_config(page_title="Gantt", page_icon="📈", layout="wide")
db.init_db()

st.title("📈 Gantt — Kế hoạch bán hàng theo thời gian")
st.caption("Mỗi thanh = 1 campaign trong 1 ngày. Màu = trạng thái. "
           "Hover để xem PR/grupo/notes.")

# ---------- Filters ----------
today = date.today()
c1, c2, c3, c4 = st.columns([1, 1, 2, 2])
year = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
month = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
month_key = f"{year:04d}-{month:02d}"

camps = campaign.list_campaigns(month=month_key)
if camps.empty:
    st.info(f"Chưa có campaign trong tháng {month_key}. Vào **Plan Generator** để sinh.")
    st.stop()

all_bcs = sorted(camps["bc"].dropna().unique().tolist())
sel_bc = c3.multiselect("BC", all_bcs, default=all_bcs)
all_statuses = sorted(camps["status"].unique().tolist())
sel_status = c4.multiselect("Status", all_statuses, default=all_statuses)

df = camps.copy()
if sel_bc:
    df = df[df["bc"].isin(sel_bc)]
if sel_status:
    df = df[df["status"].isin(sel_status)]

if df.empty:
    st.warning("Không có campaign với bộ lọc hiện tại.")
    st.stop()

# Chuẩn bị cột start/end cho Gantt
df["start"] = pd.to_datetime(df["fecha"])
df["end"] = df["start"] + pd.Timedelta(days=1)
df["pr_label"] = df["pr_code"].fillna("— chưa gán —")
df["grupo_label"] = df["grupo"].fillna("(không nhóm)")
df["campaign_label"] = df.apply(
    lambda r: f"{r['codigo']} · {r['ubicacion_code']} · {r['pr_label']}", axis=1
)

STATUS_COLORS = {
    "DRAFT":     "#9ca3af",
    "PLANNED":   "#3b82f6",
    "RUNNING":   "#f59e0b",
    "DONE":      "#10b981",
    "CANCELLED": "#ef4444",
}

st.divider()
st.metric("Tổng campaign hiển thị", len(df))

tab1, tab2, tab3, tab4 = st.tabs([
    "📍 Theo vị trí (Ubicacion)",
    "👥 Theo đội (Grupo)",
    "🏢 Theo BC",
    "🧑 Theo Promoter",
])


def gantt(data: pd.DataFrame, y_col: str, title: str, height: int = 600):
    """Render plotly timeline."""
    fig = px.timeline(
        data,
        x_start="start",
        x_end="end",
        y=y_col,
        color="status",
        color_discrete_map=STATUS_COLORS,
        hover_data={
            "codigo": True,
            "fecha": True,
            "pr_label": True,
            "grupo_label": True,
            "bc": True,
            "notas": True,
            "start": False,
            "end": False,
        },
        title=title,
    )
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_xaxes(
        title="Ngày",
        tickformat="%d/%m",
        dtick=86400000.0,  # 1 day
    )
    fig.update_layout(
        height=height,
        legend_title_text="Status",
        margin=dict(l=10, r=10, t=50, b=30),
        xaxis=dict(showgrid=True, gridcolor="#e5e7eb"),
    )
    return fig


with tab1:
    st.markdown("**Mỗi hàng là 1 điểm bán (Ubicacion).** Thanh ngang = campaign tại điểm đó vào ngày đó.")
    # sort y theo BC + ubicacion_code
    ordered = df.sort_values(["bc", "ubicacion_code"])["ubicacion_code"].unique().tolist()
    df1 = df.copy()
    df1["ubicacion_code"] = pd.Categorical(df1["ubicacion_code"],
                                            categories=ordered, ordered=True)
    h = max(400, 18 * len(ordered))
    st.plotly_chart(
        gantt(df1, "ubicacion_code", "Gantt theo vị trí", height=h),
        use_container_width=True,
    )

with tab2:
    st.markdown("**Mỗi hàng là 1 Grupo.** Nhìn được workload phân bổ qua các đội.")
    ordered = sorted(df["grupo_label"].unique().tolist())
    df2 = df.copy()
    df2["grupo_label"] = pd.Categorical(df2["grupo_label"],
                                         categories=ordered, ordered=True)
    h = max(300, 28 * len(ordered))
    st.plotly_chart(
        gantt(df2, "grupo_label", "Gantt theo Grupo", height=h),
        use_container_width=True,
    )

with tab3:
    st.markdown("**Mỗi hàng là 1 BC (Business Center).** Tổng quan theo từng vùng.")
    ordered = sorted(df["bc"].unique().tolist())
    df3 = df.copy()
    df3["bc"] = pd.Categorical(df3["bc"], categories=ordered, ordered=True)
    h = max(300, 36 * len(ordered))
    st.plotly_chart(
        gantt(df3, "bc", "Gantt theo BC", height=h),
        use_container_width=True,
    )

with tab4:
    st.markdown("**Mỗi hàng là 1 Promoter.** Xem ai bị quá tải / dư thời gian.")
    df4 = df[df["pr_code"].notna()].copy()
    if df4.empty:
        st.info("Chưa có campaign nào được gán PR.")
    else:
        ordered = sorted(df4["pr_label"].unique().tolist())
        df4["pr_label"] = pd.Categorical(df4["pr_label"],
                                          categories=ordered, ordered=True)
        h = max(400, 18 * len(ordered))
        st.plotly_chart(
            gantt(df4, "pr_label", "Gantt theo Promoter", height=h),
            use_container_width=True,
        )

st.divider()
st.subheader("🔥 Heatmap mật độ — Ngày × BC")
heat = (df.assign(d=df["start"].dt.day)
          .groupby(["bc", "d"]).size().reset_index(name="so_ca"))
fig_h = px.density_heatmap(
    heat, x="d", y="bc", z="so_ca",
    nbinsx=31, color_continuous_scale="Blues",
    title="Số campaign theo ngày × BC",
)
fig_h.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=30))
fig_h.update_xaxes(title="Ngày trong tháng", dtick=1)
fig_h.update_yaxes(title="")
st.plotly_chart(fig_h, use_container_width=True)
