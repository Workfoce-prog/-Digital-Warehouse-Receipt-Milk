import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils import load_csv, save_csv, log_event, gen_id
from auth import require_login
user = require_login()


st.set_page_config(page_title="Intake & Tests", layout="wide")

st.title("Dairy Intake & Quality Tests (Custodian)")

if user["role"] not in ["custodian","platform"]:
    st.error("Access denied. Custodian/platform role required.")
    st.stop()

entities = load_csv("entities.csv")
custodians = load_csv("custodians.csv")
tanks = load_csv("tanks.csv")
lots = load_csv("dairy_lots.csv")

custodian_id = user["entity_id"] if user["role"]=="custodian" else st.selectbox("Custodian", custodians["custodian_id"].tolist())
cust = custodians[custodians["custodian_id"]==custodian_id].iloc[0].to_dict()

st.subheader(f"Custodian: {cust['name']} ({custodian_id}) — {cust['region']}")
avail_tanks = tanks[(tanks["custodian_id"]==custodian_id)]
if avail_tanks.empty:
    st.warning("No tanks registered for this custodian.")
    st.stop()

tank_id = st.selectbox("Tank ID", avail_tanks["tank_id"].tolist())
owner_entity_id = st.selectbox("Owner entity", entities["entity_id"].tolist())
product_type = st.selectbox("Product", ["raw_milk","yogurt","butter","ghee","cheese"])
quantity = st.number_input("Quantity (liters)", min_value=1.0, value=50.0, step=1.0)
fat_pct = st.number_input("Fat %", min_value=0.0, value=4.0, step=0.1)
antibiotic = st.selectbox("Antibiotic rapid test", ["pass","fail","not_tested"])
temp_avg = st.number_input("Avg temp (°C)", value=4.0, step=0.1)
breaches = st.number_input("Temp breaches (count)", min_value=0, value=0, step=1)
quality = st.selectbox("Quality grade", ["A","B","C"])
notes = st.text_input("Notes")

hours = {"raw_milk":48, "yogurt":240, "butter":720, "ghee":2160, "cheese":1440}
expiry = datetime.utcnow() + timedelta(hours=hours[product_type])

if st.button("Create Dairy Lot", type="primary"):
    status = "quarantined" if antibiotic=="fail" else "active"
    lot_id = gen_id("LOT-", 8)
    row = {
        "lot_id": lot_id,
        "created_at": datetime.utcnow().isoformat()+"Z",
        "owner_entity_id": owner_entity_id,
        "custodian_id": custodian_id,
        "tank_id": tank_id,
        "product_type": product_type,
        "quantity_liters": quantity,
        "fat_pct": fat_pct,
        "snf_pct": "",
        "acidity": "",
        "antibiotic_test": antibiotic,
        "bacterial_score": "",
        "temp_avg_c": temp_avg,
        "temp_breach_count": int(breaches),
        "collection_time": "",
        "chill_time": "",
        "expiry_ts": expiry.isoformat()+"Z",
        "quality_grade": quality,
        "status": status,
        "notes": notes,
    }
    lots = pd.concat([lots, pd.DataFrame([row])], ignore_index=True)
    save_csv(lots, "dairy_lots.csv")
    log_event(user["username"], "lot_created", "dairy_lot", lot_id, {"custodian_id": custodian_id, "owner": owner_entity_id, "status": status})
    if status=="quarantined":
        st.warning("Lot created but QUARANTINED (antibiotic fail).")
    else:
        st.success("Lot created. Proceed to Issue DWR.")
