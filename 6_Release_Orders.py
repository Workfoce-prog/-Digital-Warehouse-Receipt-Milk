import streamlit as st
import pandas as pd
from datetime import datetime
from utils import load_csv, save_csv, log_event, gen_id
from auth import require_login
user = require_login()


st.set_page_config(page_title="Release Orders", layout="wide")
st.title("Release Orders (Dispatch / Pickup)")

receipts = load_csv("dwr_receipts.csv")
ro = load_csv("release_orders.csv")

sold = receipts[receipts["status"]=="sold"]
if sold.empty:
    st.info("No sold receipts awaiting release.")
    st.stop()

receipt_id = st.selectbox("Sold receipt", sold["receipt_id"].tolist())
r = sold[sold["receipt_id"]==receipt_id].iloc[0].to_dict()

buyer_id = st.text_input("Buyer entity ID", value="E-BUY-001")
notes = st.text_input("Dispatch notes", value="Pickup with insulated transport. Verify ID at gate.")

if st.button("Create release order", type="primary"):
    ro_id = gen_id("RO-", 8)
    row = {
        "release_order_id": ro_id,
        "receipt_id": receipt_id,
        "custodian_id": r["custodian_id"],
        "buyer_entity_id": buyer_id,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()+"Z",
        "confirmed_at": "",
        "notes": notes
    }
    ro = pd.concat([ro, pd.DataFrame([row])], ignore_index=True)
    save_csv(ro, "release_orders.csv")
    log_event(user["username"], "release_order_created", "release_order", ro_id, {"receipt_id": receipt_id})
    st.success(f"Release order created: {ro_id}")

st.markdown("---")
st.subheader("Confirm release (custodian)")
if user["role"] not in ["custodian","platform"]:
    st.info("Only custodian/platform can confirm release.")
    st.stop()

pending = ro[ro["status"]=="pending"]
if pending.empty:
    st.info("No pending release orders.")
    st.stop()

ro_id = st.selectbox("Pending RO", pending["release_order_id"].tolist())
if st.button("Confirm released", type="primary"):
    ro.loc[ro["release_order_id"]==ro_id, "status"] = "released"
    ro.loc[ro["release_order_id"]==ro_id, "confirmed_at"] = datetime.utcnow().isoformat()+"Z"
    save_csv(ro, "release_orders.csv")

    receipt_id = ro[ro["release_order_id"]==ro_id].iloc[0]["receipt_id"]
    receipts = load_csv("dwr_receipts.csv")
    receipts.loc[receipts["receipt_id"]==receipt_id, "status"] = "released"
    save_csv(receipts, "dwr_receipts.csv")

    log_event(user["username"], "released", "dwr", receipt_id, {"release_order_id": ro_id})
    st.success("Release confirmed. Receipt closed as RELEASED.")
