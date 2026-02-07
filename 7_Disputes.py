import streamlit as st
import pandas as pd
from datetime import datetime
from utils import load_csv, save_csv, log_event, gen_id

st.set_page_config(page_title="Disputes", layout="wide")
user = st.session_state.user
st.title("Disputes (Quality / Payment / Spoilage)")

receipts = load_csv("dwr_receipts.csv")
disputes = load_csv("disputes.csv")

if receipts.empty:
    st.info("No receipts.")
    st.stop()

receipt_id = st.selectbox("Receipt", receipts["receipt_id"].tolist())
dtype = st.selectbox("Dispute type", ["quality","spoilage","payment_delay","grading","custody"])
desc = st.text_area("Description")

if st.button("File dispute", type="primary"):
    did = gen_id("DSP-", 8)
    row = {
        "dispute_id": did,
        "receipt_id": receipt_id,
        "raised_by_entity_id": user["entity_id"],
        "dispute_type": dtype,
        "description": desc,
        "status": "open",
        "created_at": datetime.utcnow().isoformat()+"Z",
        "resolved_at": "",
        "resolution": ""
    }
    disputes = pd.concat([disputes, pd.DataFrame([row])], ignore_index=True)
    save_csv(disputes, "disputes.csv")
    receipts.loc[receipts["receipt_id"]==receipt_id, "status"] = "disputed"
    save_csv(receipts, "dwr_receipts.csv")
    log_event(user["username"], "dispute_filed", "dispute", did, {"receipt_id": receipt_id, "type": dtype})
    st.success(f"Dispute filed: {did}")

st.markdown("---")
st.subheader("Resolve dispute (platform/government)")
if user["role"] not in ["platform","government"]:
    st.info("Only platform/government can resolve disputes (demo).")
    st.stop()

open_df = disputes[disputes["status"]=="open"]
if open_df.empty:
    st.info("No open disputes.")
    st.stop()

did = st.selectbox("Open dispute", open_df["dispute_id"].tolist())
resolution = st.text_area("Resolution")
if st.button("Resolve", type="primary"):
    disputes.loc[disputes["dispute_id"]==did, "status"] = "resolved"
    disputes.loc[disputes["dispute_id"]==did, "resolved_at"] = datetime.utcnow().isoformat()+"Z"
    disputes.loc[disputes["dispute_id"]==did, "resolution"] = resolution
    save_csv(disputes, "disputes.csv")

    receipt_id = disputes[disputes["dispute_id"]==did].iloc[0]["receipt_id"]
    receipts = load_csv("dwr_receipts.csv")
    if receipts.loc[receipts["receipt_id"]==receipt_id, "status"].iloc[0] == "disputed":
        receipts.loc[receipts["receipt_id"]==receipt_id, "status"] = "active"
        save_csv(receipts, "dwr_receipts.csv")
    log_event(user["username"], "dispute_resolved", "dispute", did, {"receipt_id": receipt_id})
    st.success("Dispute resolved.")
