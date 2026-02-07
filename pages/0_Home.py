import streamlit as st
from auth import require_login

st.set_page_config(page_title="Mali Dairy DWR Platform", layout="wide")

user = require_login()

st.title("Mali Dairy Digital Warehouse Receipt (DWR/BDN) Platform — Pilot")
st.caption("Women groups • Independent women processors • Private dairies • Custodians • In-house finance • Future bank integration")

st.subheader("Pilot flow")
st.markdown("""1) **Tanks & Storage** (rent / rent-to-own)  
2) **Intake + tests** → create **Dairy Lot**  
3) Issue **DWR/BDN** (short expiry for raw milk)  
4) **In-house advance** (pilot) or **bank lien** (growth)  
5) **Sale contract + mobile money settlement** (auto-repay advances)  
6) **Release order** (dispatch)  
7) **Disputes, Verification, Cold-chain SLA, Audit Log** (oversight)""")

st.sidebar.markdown("---")
st.sidebar.write(f"**Role:** {user['role']}")
st.sidebar.write(f"**Entity:** {user['entity_id']}")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()
