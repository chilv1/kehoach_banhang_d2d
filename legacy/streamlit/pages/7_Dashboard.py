"""Dashboard campaign-centric: funnel + KPI + chi phí + map."""
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from lib import campaign, db
from lib.db import STATUSES

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
db.init_db()

st.title("📊 Dashboard tổng quan")

today = date.today()
c1, c2 = st.columns([1, 1])
year = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
month = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
month_key = f"{year:04d}-{month:02d}"

ubic = db.list_ubicacion()
prs = db.list_promoter()
camps = campaign.list_campaigns(month=month_key)
res_df = campaign.list_results_with_campaign(month=month_key)

# ===== Top KPIs =====
st.subheader("Tổng quan")
m_cols = st.columns(6)
m_cols[0].metric("Ubicaciones", len(ubic))
m_cols[1].metric("Promoters", len(prs))
m_cols[2].metric("Campaigns tháng", len(camps))
m_cols[3].metric("DRAFT", int((camps["status"] == "DRAFT").sum()) if not camps.empty else 0)
m_cols[4].metric("PLANNED", int((camps["status"] == "PLANNED").sum()) if not camps.empty else 0)
m_cols[5].metric("DONE", int((camps["status"] == "DONE").sum()) if not camps.empty else 0)

if camps.empty:
    st.info(f"Chưa có campaign trong tháng {month_key}.")
    st.stop()

st.divider()

# ===== Funnel =====
st.subheader("🌀 Funnel trạng thái")
counts = camps.groupby("status").size().reindex(STATUSES, fill_value=0).reset_index()
counts.columns = ["status", "so_luong"]
fig_funnel = px.funnel(counts, x="so_luong", y="status",
                       title="Phân bố trạng thái campaign")
st.plotly_chart(fig_funnel, use_container_width=True)

st.divider()

# ===== Phân bố theo BC + theo ngày =====
st.subheader("📅 Phân bố campaign")
camps["fecha_dt"] = pd.to_datetime(camps["fecha"])

c1, c2 = st.columns(2)
with c1:
    by_day = camps.groupby(["fecha_dt", "status"]).size().reset_index(name="n")
    fig = px.bar(by_day, x="fecha_dt", y="n", color="status",
                  title="Số campaign theo ngày", barmode="stack")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    by_bc = camps.groupby(["bc", "status"]).size().reset_index(name="n")
    fig = px.bar(by_bc, x="bc", y="n", color="status",
                  title="Phân bố theo BC", barmode="stack")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ===== Coverage =====
st.subheader("📍 Coverage")
planned_codes = set(camps["ubicacion_code"].dropna().unique())
total_ubic = len(ubic) if not ubic.empty else 0
coverage = len(planned_codes) / total_ubic if total_ubic else 0
unassigned = int(camps["pr_code"].isna().sum())
g1, g2, g3, g4 = st.columns(4)
g1.metric("Vị trí có campaign / tổng",
          f"{len(planned_codes)}/{total_ubic}")
g2.metric("Coverage %", f"{coverage:.0%}")
g3.metric("Campaign chưa có PR", unassigned)
g4.metric("BC tham gia", camps["bc"].nunique())

st.divider()

# ===== Meta vs Resultado =====
st.subheader("🆚 Meta vs Resultado (tổng tháng)")
metric_pairs = [
    ("meta_prepago", "res_prepago", "Prepago"),
    ("meta_postpago", "res_postpago", "Postpago"),
    ("meta_bipay", "res_bipay", "Bipay"),
    ("meta_tv360", "res_tv360", "TV360"),
    ("meta_mnp", "res_mnp", "MNP"),
]
mr_rows = []
for mk, rk, label in metric_pairs:
    meta_total = float(camps[mk].sum()) if mk in camps.columns else 0
    res_total = float(res_df[rk].sum()) if rk in res_df.columns else 0
    pct = (res_total / meta_total * 100) if meta_total else 0
    mr_rows.append({"metric": label, "meta": meta_total,
                    "resultado": res_total, "pct": round(pct, 1)})
df_mr = pd.DataFrame(mr_rows)
st.dataframe(df_mr, use_container_width=True, hide_index=True)
fig = px.bar(df_mr, x="metric", y=["meta", "resultado"],
              barmode="group", title="Meta vs Resultado")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ===== Chi phí =====
st.subheader("💵 Chi phí kế hoạch")
gasto_cols = ["gasto_comida", "gasto_hotel", "gasto_movilidad", "gasto_renta"]
present = [c for c in gasto_cols if c in camps.columns]
if present:
    by_bc_g = camps.groupby("bc")[present].sum().reset_index()
    long_g = by_bc_g.melt(id_vars="bc", var_name="loai",
                          value_name="gasto")
    fig = px.bar(long_g, x="bc", y="gasto", color="loai",
                 title="Chi phí kế hoạch theo BC (stacked)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Tổng chi phí kế hoạch tháng: **{by_bc_g[present].sum().sum():,.0f}**")

st.divider()

# ===== PR workload =====
st.subheader("👥 Tải công việc PR")
assigned = camps.dropna(subset=["pr_code"])
if not assigned.empty:
    by_pr = (assigned.groupby("pr_code").size().reset_index(name="so_ca")
             .merge(prs[["pr_code", "bc", "grupo", "cantidad_dia_trabajo"]],
                    on="pr_code", how="left"))
    by_pr["utilization_%"] = (
        by_pr["so_ca"] / by_pr["cantidad_dia_trabajo"].replace(0, 1) * 100
    ).round(1)
    by_pr = by_pr.sort_values("so_ca", ascending=False)
    st.dataframe(by_pr, use_container_width=True, hide_index=True, height=320)
    fig = px.bar(by_pr.head(30), x="pr_code", y="so_ca", color="bc",
                 title="Top 30 PR theo số ca")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Chưa có campaign nào được phân PR.")

st.divider()

# ===== Map =====
st.subheader("🗺️ Bản đồ campaign")
geo = camps.dropna(subset=["latitud", "longitud"]).copy()
geo = geo[(geo["latitud"] != 0) & (geo["longitud"] != 0)]
if not geo.empty:
    geo = geo.rename(columns={"latitud": "lat", "longitud": "lon"})
    st.map(geo[["lat", "lon"]])
    st.caption(f"Hiển thị {len(geo)} campaign có toạ độ.")
else:
    st.info("Chưa có toạ độ.")
