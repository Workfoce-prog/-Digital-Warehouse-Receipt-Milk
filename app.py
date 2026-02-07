import streamlit as st
from utils import load_csv_schema
import pandas as pd
from auth import require_login
user = require_login()
custodian_schema = ["custodian_id","custodian_type","name","region","license_status","power_source","notes"]

seed_custodians = pd.DataFrame([
    ["C-MCC-001","mcc","Centre de Collecte Sikasso","Sikasso","licensed","solar+grid","Chilling available"],
    ["C-CHILL-001","chilling_center","Chiller Koulikoro","Koulikoro","licensed","grid","Bulk tank"],
    ["C-PROC-001","processor","Mini-Usine Bamako","Bamako","licensed","grid","Yogurt/butter processing"],
], columns=custodian_schema)

custodians = load_csv_schema("custodians.csv", custodian_schema, seed_df=seed_custodians)

st.set_page_config(page_title="Mali Dairy DWR Platform", layout="wide")

st.sidebar.markdown("---")
st.sidebar.write(f"**Role:** {user['role']}")
st.sidebar.write(f"**Entity:** {user['entity_id']}")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

st.title("Mali Dairy Digital Warehouse Receipt (DWR/BDN) Platform — Pilot")
st.caption("Women groups • Independent women processors • Private dairies • Custodians • In-house finance • Future bank integration")

entities = load_csv("entities.csv")
custodians = load_csv("custodians.csv")
tanks = load_csv("tanks.csv")
lots = load_csv("dairy_lots.csv")
receipts = load_csv("dwr_receipts.csv")

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Owner entities", len(entities))
licensed_count = 0
if not custodians.empty and "license_status" in custodians.columns:
    licensed_count = int(custodians["license_status"].astype(str).str.contains("licensed", na=False).sum())

c2.metric("Licensed custodians", licensed_count)
c3.metric("Tanks", len(tanks))
c4.metric("Active lots", len(lots[lots['status'].fillna('')=='active']))
c5.metric("Active receipts", len(receipts[receipts['status'].fillna('')=='active']))

st.subheader("Pilot flow")
st.markdown("""1) **Tanks & Storage** (rent / rent-to-own)  
2) **Intake + tests** → create **Dairy Lot**  
3) Issue **DWR/BDN** (short expiry for raw milk)  
4) **In-house advance** (pilot) or **bank lien** (growth)  
5) **Sale contract + mobile money settlement** (auto-repay advances)  
6) **Release order** (dispatch)  
7) **Audit & Cold-chain SLA** (oversight)""")
