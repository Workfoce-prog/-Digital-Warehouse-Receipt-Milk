import streamlit as st
import pandas as pd
from datetime import datetime
from utils import load_csv, save_csv, log_event, gen_id

st.set_page_config(page_title="Sale & Settlement", layout="wide")
user = st.session_state.user
st.title("Sale Contract + Mobile Money Settlement (Demo)")

receipts = load_csv("dwr_receipts.csv")
lots = load_csv("dairy_lots.csv")
contracts = load_csv("sales_contracts.csv")
payments = load_csv("payments.csv")
advances = load_csv("advances.csv")

eligible = receipts[receipts["status"].isin(["active","advance_active"])].copy()
if eligible.empty:
    st.info("No receipts available for sale.")
    st.stop()

receipt_id = st.selectbox("Select receipt", eligible["receipt_id"].tolist())
r = receipts[receipts["receipt_id"]==receipt_id].iloc[0].to_dict()
lot = lots[lots["lot_id"]==r["lot_id"]].iloc[0].to_dict()

buyer_id = st.text_input("Buyer entity ID", value="E-BUY-001")
price = st.number_input("Total price (XOF)", min_value=0.0, value=50000.0, step=5000.0)
terms = st.selectbox("Terms", ["mobile_money_instant","mobile_money_T+1","cash_on_delivery"])

if st.button("Create sale contract", type="primary"):
    cid = gen_id("SC-", 8)
    row = {
        "contract_id": cid,
        "receipt_id": receipt_id,
        "buyer_entity_id": buyer_id,
        "price_xof": float(price),
        "payment_terms": terms,
        "status": "pending_payment",
        "created_at": datetime.utcnow().isoformat()+"Z",
        "settled_at": "",
        "notes": ""
    }
    contracts = pd.concat([contracts, pd.DataFrame([row])], ignore_index=True)
    save_csv(contracts, "sales_contracts.csv")
    receipts.loc[receipts["receipt_id"]==receipt_id, "status"] = "pending_sale"
    save_csv(receipts, "dwr_receipts.csv")
    log_event(user["username"], "sale_contract_created", "sale_contract", cid, {"receipt_id": receipt_id, "price": price})
    st.success(f"Contract created: {cid}. Now settle payment below.")

st.markdown("---")
st.subheader("Settle payment (demo)")
pending = contracts[contracts["status"]=="pending_payment"]
if pending.empty:
    st.info("No pending contracts.")
    st.stop()

contract_id = st.selectbox("Pending contract", pending["contract_id"].tolist())
c = pending[pending["contract_id"]==contract_id].iloc[0].to_dict()
method = st.selectbox("Payment method", ["orange_money","moov_money","wave","bank_transfer"])

if st.button("Confirm payment", type="primary"):
    pid = gen_id("PAY-", 8)
    pay = {
        "payment_id": pid,
        "ref_type": "sale_contract",
        "ref_id": contract_id,
        "payer_id": c["buyer_entity_id"],
        "payee_id": "E-PLAT-001",
        "amount_xof": float(c["price_xof"]),
        "method": method,
        "status": "confirmed",
        "created_at": datetime.utcnow().isoformat()+"Z",
        "confirmed_at": datetime.utcnow().isoformat()+"Z",
        "provider_ref": gen_id("MM-", 10)
    }
    payments = pd.concat([payments, pd.DataFrame([pay])], ignore_index=True)
    save_csv(payments, "payments.csv")

    receipt_id = c["receipt_id"]
    adv = advances[(advances["receipt_id"]==receipt_id) & (advances["status"]=="active")]
    net_to_owner = float(c["price_xof"])
    if not adv.empty:
        adv0 = adv.iloc[0]
        net_to_owner -= float(adv0["advance_xof"]) + float(adv0["fee_xof"])
        advances.loc[advances["advance_id"]==adv0["advance_id"], "status"] = "repaid"
        advances.loc[advances["advance_id"]==adv0["advance_id"], "repaid_at"] = datetime.utcnow().isoformat()+"Z"
        save_csv(advances, "advances.csv")
        log_event("system", "advance_repaid", "advance", adv0["advance_id"], {"receipt_id": receipt_id})

    contracts.loc[contracts["contract_id"]==contract_id, "status"] = "settled"
    contracts.loc[contracts["contract_id"]==contract_id, "settled_at"] = datetime.utcnow().isoformat()+"Z"
    save_csv(contracts, "sales_contracts.csv")

    receipts = load_csv("dwr_receipts.csv")
    receipts.loc[receipts["receipt_id"]==receipt_id, "status"] = "sold"
    save_csv(receipts, "dwr_receipts.csv")
    log_event(user["username"], "sale_settled", "sale_contract", contract_id, {"payment_id": pid, "net_to_owner_est": net_to_owner})
    st.success(f"Payment confirmed: {pid}. Receipt marked SOLD. Net to owner estimate: {int(net_to_owner)} XOF.")
