import streamlit as st
import pandas as pd
from urllib.parse import parse_qs
from utils import load_csv

st.set_page_config(page_title="Verify DWR", layout="wide")
st.title("Verify DWR/BDN (QR / Receipt ID)")

receipts = load_csv("dwr_receipts.csv")
lots = load_csv("dairy_lots.csv")
entities = load_csv("entities.csv")
custodians = load_csv("custodians.csv")
advances = load_csv("advances.csv")
disputes = load_csv("disputes.csv")

q = st.text_input("Enter Receipt ID (DWR-...) or QR payload")
receipt_id = None
if q.strip().startswith("DWR-"):
    receipt_id = q.strip()
elif "receipt_id=" in q:
    try:
        parsed = parse_qs(q.strip(), keep_blank_values=True)
        receipt_id = parsed.get("receipt_id",[None])[0]
    except Exception:
        receipt_id = None

if not receipt_id:
    st.info("Enter a receipt id or QR payload.")
    st.stop()

r = receipts[receipts["receipt_id"]==receipt_id]
if r.empty:
    st.error("Receipt not found.")
    st.stop()

r0 = r.iloc[0].to_dict()
lot = lots[lots["lot_id"]==r0["lot_id"]].iloc[0].to_dict()
owner = entities[entities["entity_id"]==r0["owner_entity_id"]].iloc[0].to_dict()
cust = custodians[custodians["custodian_id"]==r0["custodian_id"]].iloc[0].to_dict()

exp = pd.to_datetime(r0["expiry_ts"], errors="coerce")
expired = False if pd.isna(exp) else exp < pd.Timestamp.utcnow()
active_adv = not advances[(advances["receipt_id"]==receipt_id) & (advances["status"]=="active")].empty
open_disp = not disputes[(disputes["receipt_id"]==receipt_id) & (disputes["status"]=="open")].empty

if (not expired) and (not open_disp):
    st.success("VERIFIED ✅ (demo checks passed)")
else:
    st.warning("VERIFICATION WARNING ⚠️ (expired or disputed)")

c1,c2,c3,c4 = st.columns(4)
c1.metric("Status", r0["status"])
c2.metric("Expired", "YES" if expired else "NO")
c3.metric("Advance active", "YES" if active_adv else "NO")
c4.metric("Open dispute", "YES" if open_disp else "NO")

st.subheader("Details")
left,right = st.columns(2)
with left:
    st.json({"receipt": r0, "owner": owner})
with right:
    st.json({"lot": lot, "custodian": cust})
