import streamlit as st
from auth import require_login
from utils import load_csv_schema
import pandas as pd

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
import pandas as pd

entity_schema = ["entity_id","entity_type","name","contact_name","phone","region","legal_status","mobile_money_id"]
custodian_schema = ["custodian_id","custodian_type","name","region","license_status","power_source","notes"]
tank_schema = ["tank_id","custodian_id","capacity_liters","cooling_type","temp_min_c","temp_max_c","status","ownership_model","owner_entity_id","rent_xof_per_day","rent_to_own_months","purchase_price_xof"]
lot_schema = ["lot_id","created_at","owner_entity_id","custodian_id","tank_id","product_type","quantity_liters","fat_pct","snf_pct","acidity","antibiotic_test","bacterial_score","temp_avg_c","temp_breach_count","collection_time","chill_time","expiry_ts","quality_grade","status","notes"]
receipt_schema = ["receipt_id","issued_at","lot_id","owner_entity_id","custodian_id","status","expiry_ts","qr_payload","lien_active","lien_holder_id"]

seed_entities = pd.DataFrame([
    ["E-WG-001","women_group","Association Femmes Laitières de Sikasso","Awa Traoré","+22370000001","Sikasso","informal_registered","OM-AWA-001"],
    ["E-WI-001","woman_individual","Fatoumata Diallo (Transformatrice)","Fatoumata Diallo","+22370000002","Koulikoro","informal_registered","OM-FAT-001"],
    ["E-COOP-001","coop","Coopérative Lait Bamako","Mariama Koné","+22370000003","Bamako","formal","OM-COOP-001"],
    ["E-COMP-001","company","LaitMali SARL","Moussa Keita","+22370000004","Bamako","formal","OM-LAIT-001"],
    ["E-BUY-001","buyer","Hôpital Régional Sikasso","Procurement","+22370000005","Sikasso","formal","OM-HOSP-001"],
    ["E-PLAT-001","platform","Mali Dairy DWR Platform","Admin","+22370000099","Bamako","formal","PLAT"],
], columns=entity_schema)

seed_custodians = pd.DataFrame([
    ["C-MCC-001","mcc","Centre de Collecte Sikasso","Sikasso","licensed","solar+grid","Chilling available"],
    ["C-CHILL-001","chilling_center","Chiller Koulikoro","Koulikoro","licensed","grid","Bulk tank"],
    ["C-PROC-001","processor","Mini-Usine Bamako","Bamako","licensed","grid","Yogurt/butter processing"],
], columns=custodian_schema)

seed_tanks = pd.DataFrame([
    ["T-500-001","C-MCC-001",500,"direct_expansion",2,6,"available","rental","E-PLAT-001",5000,12,2500000],
    ["T-1000-001","C-CHILL-001",1000,"ice_bank",2,6,"available","rent_to_own","E-PLAT-001",8000,18,4200000],
    ["T-300-001","C-PROC-001",300,"direct_expansion",2,6,"occupied","owned","E-COMP-001",0,0,1800000],
], columns=tank_schema)

# Load all with schema enforcement (self-heals if broken/missing)
entities = load_csv_schema("entities.csv", entity_schema, seed_df=seed_entities)
custodians = load_csv_schema("custodians.csv", custodian_schema, seed_df=seed_custodians)
tanks = load_csv_schema("tanks.csv", tank_schema, seed_df=seed_tanks)

lots = load_csv_schema("dairy_lots.csv", lot_schema, seed_df=pd.DataFrame(columns=lot_schema))
receipts = load_csv_schema("dwr_receipts.csv", receipt_schema, seed_df=pd.DataFrame(columns=receipt_schema))


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
