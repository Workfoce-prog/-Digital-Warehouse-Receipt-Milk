import streamlit as st
import pandas as pd
from utils import load_csv, save_csv, log_event, gen_id, make_qr_payload, generate_receipt_pdf

st.set_page_config(page_title="Issue DWR/BDN", layout="wide")
user = st.session_state.user
st.title("Issue Digital Warehouse Receipt (DWR/BDN)")

if user["role"] not in ["platform","government"]:
    st.error("Access denied. Platform/Government role required.")
    st.stop()

lots = load_csv("dairy_lots.csv")
receipts = load_csv("dwr_receipts.csv")
entities = load_csv("entities.csv")
custodians = load_csv("custodians.csv")

eligible = lots[lots["status"]=="active"].copy()
if eligible.empty:
    st.info("No eligible lots.")
    st.stop()

lot_id = st.selectbox("Select active lot", eligible["lot_id"].tolist())
lot = eligible[eligible["lot_id"]==lot_id].iloc[0].to_dict()
owner = entities[entities["entity_id"]==lot["owner_entity_id"]].iloc[0].to_dict()
cust = custodians[custodians["custodian_id"]==lot["custodian_id"]].iloc[0].to_dict()

c1,c2,c3,c4 = st.columns(4)
c1.metric("Product", lot["product_type"])
c2.metric("Qty (L)", float(lot["quantity_liters"]))
c3.metric("Temp avg", f"{lot['temp_avg_c']} °C")
c4.metric("Expiry", lot["expiry_ts"])

if st.button("Issue DWR/BDN", type="primary"):
    receipt_id = gen_id("DWR-", 8)
    qr = make_qr_payload(receipt_id, lot_id, lot["owner_entity_id"], lot["custodian_id"])
    row = {
        "receipt_id": receipt_id,
        "issued_at": pd.Timestamp.utcnow().isoformat()+"Z",
        "lot_id": lot_id,
        "owner_entity_id": lot["owner_entity_id"],
        "custodian_id": lot["custodian_id"],
        "status": "active",
        "expiry_ts": lot["expiry_ts"],
        "qr_payload": qr,
        "lien_active": "no",
        "lien_holder_id": "",
    }
    receipts = pd.concat([receipts, pd.DataFrame([row])], ignore_index=True)
    save_csv(receipts, "dwr_receipts.csv")
    log_event(user["username"], "receipt_issued", "dwr", receipt_id, {"lot_id": lot_id})
    st.success(f"DWR issued: {receipt_id}")

    pdf = generate_receipt_pdf(row, lot, owner, cust)
    st.download_button("Download PDF receipt", data=pdf, file_name=f"{receipt_id}.pdf", mime="application/pdf")
