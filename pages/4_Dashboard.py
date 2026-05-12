"""Dashboard thống kê."""
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from lib import db

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
db.init_db()

st.title("📊 Dashboard thống kê")

today = date.today()
c1, c2 = st.columns([1, 1])
year = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
month = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
month_key = f"{year:04d}-{month:02d}"

ubic = db.list_ubicacion()
prs = db.list_promoter()
plan = db.list_plan(month_key)
res = db.list_resultado(month_key)

if ubic.empty and prs.empty:
    st.info("Chưa có dữ liệu. Vào trang Ubicacion / PR / Import để nạp.")
    st.stop()

# ===== Overview =====
st.subheader("Tổng quan")
o1, o2, o3, o4, o5 = st.columns(5)
o1.metric("Ubicaciones", len(ubic))
o2.metric("Promoters", len(prs))
o3.metric("Plan ca", len(plan))
o4.metric("Đã ghép PR", int(plan["pr_code"].notna().sum()) if not plan.empty else 0)
o5.metric("Resultados", len(res))

st.divider()

# ===== KPI Meta tổng (theo BC) =====
st.subheader("🎯 Tổng hợp Meta theo BC")
if not ubic.empty:
    meta_cols = ["meta_prepago", "meta_postpago", "meta_bipay",
                 "meta_tv360", "meta_mnp", "meta_agentes",
                 "meta_usuarios_bipay", "meta_pago_servicios", "meta_tusami"]
    meta_present = [c for c in meta_cols if c in ubic.columns]
    if meta_present:
        agg = ubic.groupby("bc")[meta_present].sum().reset_index()
        st.dataframe(agg, use_container_width=True)

        long_df = agg.melt(id_vars="bc", var_name="metric", value_name="meta")
        fig = px.bar(long_df, x="bc", y="meta", color="metric",
                     title="Meta theo BC (stacked)", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ===== Plan distribution =====
st.subheader("📅 Phân bố plan trong tháng")
if plan.empty:
    st.info("Chưa có plan cho tháng này.")
else:
    plan["fecha_dt"] = pd.to_datetime(plan["fecha"])

    by_day = plan.groupby("fecha_dt").size().reset_index(name="so_ca")
    fig1 = px.bar(by_day, x="fecha_dt", y="so_ca",
                  title="Số ca campaign theo ngày")
    st.plotly_chart(fig1, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        by_bc = plan.groupby("bc").size().reset_index(name="so_ca")
        fig2 = px.pie(by_bc, names="bc", values="so_ca",
                      title="Phân bố ca theo BC")
        st.plotly_chart(fig2, use_container_width=True)
    with c2:
        if "tipo_dfcp" in plan.columns:
            by_tipo = plan.groupby("tipo_dfcp").size().reset_index(name="so_ca")
            fig3 = px.bar(by_tipo, x="tipo_dfcp", y="so_ca",
                          title="Phân bố ca theo Tipo DF/CP")
            st.plotly_chart(fig3, use_container_width=True)

    # Coverage: vị trí đã được lên plan / tổng số
    planned_codes = set(plan["ubicacion_code"].dropna().unique())
    total_ubic = len(ubic)
    coverage = len(planned_codes) / total_ubic if total_ubic else 0
    st.metric("Coverage (vị trí có plan / tổng)",
              f"{coverage:.0%} ({len(planned_codes)}/{total_ubic})")

st.divider()

# ===== PR workload =====
st.subheader("👥 Tải công việc của PR")
if plan.empty or "pr_code" not in plan.columns:
    st.info("Chưa có plan.")
else:
    assigned = plan.dropna(subset=["pr_code"])
    if assigned.empty:
        st.info("Chưa có ca nào được ghép PR.")
    else:
        by_pr = assigned.groupby("pr_code").size().reset_index(name="so_ca")
        by_pr = by_pr.merge(prs[["pr_code", "bc", "grupo",
                                  "cantidad_dia_trabajo"]],
                             on="pr_code", how="left")
        by_pr["utilization_pct"] = (
            by_pr["so_ca"] / by_pr["cantidad_dia_trabajo"].replace(0, 1) * 100
        ).round(1)
        st.dataframe(by_pr, use_container_width=True, height=400)

        fig = px.bar(by_pr.sort_values("so_ca", ascending=False).head(30),
                     x="pr_code", y="so_ca", color="bc",
                     title="Top 30 PR theo số ca")
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ===== Meta vs Resultado =====
st.subheader("🆚 Meta vs Resultado")
if res.empty:
    st.info("Chưa có dữ liệu Resultado.")
else:
    metric_pairs = [
        ("meta_prepago", "res_prepago", "Prepago"),
        ("meta_postpago", "res_postpago", "Postpago"),
        ("meta_bipay", "res_bipay", "Bipay"),
        ("meta_tv360", "res_tv360", "TV360"),
        ("meta_mnp", "res_mnp", "MNP"),
    ]
    rows = []
    for meta_col, res_col, label in metric_pairs:
        meta_total = ubic[meta_col].sum() if meta_col in ubic.columns else 0
        res_total = res[res_col].sum() if res_col in res.columns else 0
        pct = (res_total / meta_total * 100) if meta_total else 0
        rows.append({"metric": label, "meta": meta_total,
                      "resultado": res_total, "pct": round(pct, 1)})
    df_mr = pd.DataFrame(rows)
    st.dataframe(df_mr, use_container_width=True)

    fig = px.bar(df_mr, x="metric", y=["meta", "resultado"],
                 barmode="group", title="Meta vs Resultado")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ===== Bản đồ điểm bán =====
st.subheader("🗺️ Bản đồ điểm bán")
if not ubic.empty and {"latitud", "longitud"}.issubset(ubic.columns):
    geo = ubic.dropna(subset=["latitud", "longitud"]).copy()
    geo = geo[(geo["latitud"] != 0) & (geo["longitud"] != 0)]
    if not geo.empty:
        geo = geo.rename(columns={"latitud": "lat", "longitud": "lon"})
        st.map(geo[["lat", "lon"]])
        st.caption(f"Hiển thị {len(geo)} điểm có toạ độ.")
    else:
        st.info("Chưa có điểm nào với toạ độ hợp lệ.")
