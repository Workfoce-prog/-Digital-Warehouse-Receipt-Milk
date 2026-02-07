import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils import load_csv, save_csv, log_event, gen_id

st.set_page_config(page_title="In-house Advance", layout="wide")
user = st.session_state.user
st.title("In-house Advance (Pilot) — Platform-led finance")

if user["role"] not in ["platform","owner"]:
    st.error("Access denied.")
    st.stop()

receipts = load_csv("dwr_receipts.csv")
lots = load_csv("dairy_lots.csv")
advances = load_csv("advances.csv")
entities = load_csv("entities.csv")
prices = load_csv("reference_prices.csv")

if receipts.empty:
    st.info("No receipts.")
    st.stop()

if user["role"] == "owner":
    mine = receipts[receipts["owner_entity_id"]==user["entity_id"]]
    if mine.empty:
        st.info("You have no receipts.")
        st.stop()
    receipt_id = st.selectbox("Your receipt", mine["receipt_id"].tolist())
else:
    receipt_id = st.selectbox("Receipt", receipts["receipt_id"].tolist())

r = receipts[receipts["receipt_id"]==receipt_id].iloc[0].to_dict()
lot = lots[lots["lot_id"]==r["lot_id"]].iloc[0].to_dict()

owner_region = entities[entities["entity_id"]==r["owner_entity_id"]].iloc[0]["region"]
pr = prices[(prices["product_type"]==lot["product_type"]) & (prices["region"]==owner_region)]
xof_per_liter = float(pr.iloc[0]["xof_per_liter"]) if not pr.empty else 500.0
est_value = float(lot["quantity_liters"]) * xof_per_liter

c1,c2,c3 = st.columns(3)
c1.metric("Ref price (XOF/L)", int(xof_per_liter))
c2.metric("Estimated value (XOF)", int(est_value))
ltv = st.slider("Advance rate (LTV)", 0.1, 0.9, 0.7, 0.05)
c3.metric("Max advance (XOF)", int(est_value*ltv))

advance_xof = st.number_input("Requested advance (XOF)", min_value=0.0, value=float(int(est_value*ltv*0.8)), step=5000.0)
fee_pct = st.slider("Fee %", 0.0, 0.15, 0.05, 0.01)
tenor = st.number_input("Tenor (days)", min_value=1, value=7, step=1)

if st.button("Create advance (pilot)", type="primary"):
    if r["status"] not in ["active"]:
        st.error(f"Receipt must be ACTIVE. Current: {r['status']}")
        st.stop()
    adv_id = gen_id("ADV-", 8)
    fee = advance_xof*fee_pct
    created = datetime.utcnow()
    due = created + timedelta(days=int(tenor))
    row = {
        "advance_id": adv_id,
        "receipt_id": receipt_id,
        "provider_type": "platform",
        "provider_id": "E-PLAT-001",
        "advance_xof": float(advance_xof),
        "fee_xof": float(fee),
        "tenor_days": int(tenor),
        "status": "active",
        "created_at": created.isoformat()+"Z",
        "due_at": due.isoformat()+"Z",
        "repaid_at": "",
        "notes": "Pilot in-house advance"
    }
    advances = pd.concat([advances, pd.DataFrame([row])], ignore_index=True)
    save_csv(advances, "advances.csv")

    receipts.loc[receipts["receipt_id"]==receipt_id, "status"] = "advance_active"
    save_csv(receipts, "dwr_receipts.csv")
    log_event(user["username"], "advance_created", "advance", adv_id, {"receipt_id": receipt_id, "amount": advance_xof, "fee": fee})
    st.success(f"Advance created: {adv_id}. Receipt status set to advance_active.")
