"""Trang ghi nhận Kết quả + Checklist + Đóng campaign."""
from datetime import date

import streamlit as st

from lib import campaign, db
from lib.db import TRANSITIONS

st.set_page_config(page_title="Kết quả", page_icon="✅", layout="wide")
db.init_db()

st.title("✅ Ghi nhận kết quả & Đóng campaign")
st.caption("Nhập kết quả thực tế, checklist, sau đó chuyển campaign sang DONE.")

today = date.today()
c1, c2, c3 = st.columns([1, 1, 3])
year = c1.number_input("Năm", min_value=2024, max_value=2030, value=today.year)
month = c2.number_input("Tháng", min_value=1, max_value=12, value=today.month)
month_key = f"{year:04d}-{month:02d}"
status_filter = c3.multiselect(
    "Status", ["PLANNED", "RUNNING", "DONE"],
    default=["PLANNED", "RUNNING"],
)

camps = campaign.list_campaigns(month=month_key, status=status_filter)
if camps.empty:
    st.info("Không có campaign phù hợp.")
    st.stop()

choices = camps.apply(
    lambda r: f"{r['codigo']} | {r['fecha']} | {r['ubicacion_code']} | {r['bc']} | {r['status']}",
    axis=1,
).tolist()
idx = st.selectbox("Chọn campaign", range(len(choices)),
                    format_func=lambda i: choices[i])
cid = int(camps.iloc[idx]["id"])
c = campaign.get_campaign(cid)
res = campaign.get_result(cid) or {}

# Top info
i1, i2, i3, i4 = st.columns(4)
i1.metric("Status", c["status"])
i2.metric("Ngày", c["fecha"])
i3.metric("Vị trí", c["ubicacion_code"])
i4.metric("PR", c.get("pr_code") or "—")

st.divider()

with st.form("result_form"):
    st.subheader("🆚 Meta vs Resultado (Mobile + Digital)")
    pairs = [
        ("Prepago", "meta_prepago", "res_prepago"),
        ("Postpago", "meta_postpago", "res_postpago"),
        ("Bipay", "meta_bipay", "res_bipay"),
        ("TV360", "meta_tv360", "res_tv360"),
        ("MNP", "meta_mnp", "res_mnp"),
        ("Agentes", "meta_agentes", "res_agentes"),
        ("Usuarios Bipay", "meta_usuarios_bipay", "res_usuarios_bipay"),
        ("Pago Servicios", "meta_pago_servicios", "res_pago_servicios"),
        ("Tusami", "meta_tusami", "res_tusami"),
    ]
    inputs: dict = {}
    for label, mkey, rkey in pairs:
        cc1, cc2, cc3 = st.columns([2, 2, 2])
        cc1.markdown(f"**{label}**")
        cc2.metric("Meta", c.get(mkey) or 0)
        inputs[rkey] = cc3.number_input(
            f"Resultado {label}", min_value=0,
            value=int(res.get(rkey) or 0),
            key=f"r_{rkey}",
        )

    st.subheader("💵 Gasto thực tế")
    inputs["gasto_real"] = st.number_input(
        "Gasto total thực tế", min_value=0.0,
        value=float(res.get("gasto_real") or 0),
    )

    st.subheader("📋 Checklist trợ lý (Assistente Check)")
    cl_cols = st.columns(6)
    inputs["evidencia_pago"] = int(cl_cols[0].checkbox(
        "Evidencia pago", value=bool(res.get("evidencia_pago"))))
    inputs["merch_entregado"] = int(cl_cols[1].checkbox(
        "Merch entregado", value=bool(res.get("merch_entregado"))))
    inputs["checklist_ok"] = int(cl_cols[2].checkbox(
        "Checklist OK", value=bool(res.get("checklist_ok"))))
    inputs["activaciones_ok"] = int(cl_cols[3].checkbox(
        "Activaciones OK", value=bool(res.get("activaciones_ok"))))
    inputs["digital_ok"] = int(cl_cols[4].checkbox(
        "Digital OK", value=bool(res.get("digital_ok"))))
    inputs["campana_ok"] = int(cl_cols[5].checkbox(
        "Campaña OK (tổng kết)", value=bool(res.get("campana_ok"))))

    inputs["dfcode_btscode"] = st.text_input(
        "DF/BTS Code", value=res.get("dfcode_btscode") or "")
    inputs["nota"] = st.text_area(
        "Nota", value=res.get("nota") or "", height=80)

    st.markdown("---")
    cA, cB = st.columns([2, 5])
    save_btn = cA.form_submit_button("💾 Lưu kết quả", type="primary")
    close_btn = cB.form_submit_button("🏁 Lưu & chuyển sang DONE",
                                       type="secondary")

    if save_btn or close_btn:
        try:
            campaign.upsert_result(cid, inputs)
            st.success("Đã lưu kết quả.")
            if close_btn:
                if "DONE" in TRANSITIONS.get(c["status"], set()):
                    campaign.change_status(cid, "DONE",
                                            nota="Đóng từ trang Kết quả")
                    st.success("✅ Campaign đã chuyển sang DONE.")
                else:
                    st.warning(
                        f"Không thể chuyển {c['status']} → DONE. "
                        f"Vào Campaigns để chuyển thủ công."
                    )
        except Exception as e:
            st.error(f"Lỗi: {e}")

st.divider()
with st.expander("📜 Lịch sử thay đổi"):
    log = campaign.campaign_log(cid)
    if log.empty:
        st.caption("Chưa có log.")
    else:
        st.dataframe(
            log[["at", "accion", "old_status", "new_status", "nota", "actor"]],
            use_container_width=True, hide_index=True,
        )
