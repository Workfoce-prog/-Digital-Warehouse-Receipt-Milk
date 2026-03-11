import streamlit as st
from auth import require_login
from utils import load_csv_schema
import pandas as pd

# ----------------------------
# Page config MUST be first
# ----------------------------
st.set_page_config(page_title="Mali Dairy DWR Platform", layout="wide")

# ----------------------------
# Login
# ----------------------------
user = require_login()

# ----------------------------
# Sidebar user info + logout
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.write(f"**Role:** {user['role']}")
st.sidebar.write(f"**Entity:** {user['entity_id']}")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# ----------------------------
# Forced navigation
# ----------------------------
pages = {
    "Pilot Workflow": [
        st.Page("pages/0_Home.py", title="Home"),
        st.Page("pages/1_Tanks_Storage.py", title="Tanks & Storage"),
        st.Page("pages/2_Intake_and_Tests.py", title="Intake & Tests"),
        st.Page("pages/3_Issue_DWR.py", title="Issue DWR / BDN"),
        st.Page("pages/4_InHouse_Advance.py", title="In-house Advance"),
        st.Page("pages/5_Sale_and_Settlement.py", title="Sale & Settlement"),
        st.Page("pages/6_Release_Orders.py", title="Release Orders"),
        st.Page("pages/7_Disputes.py", title="Disputes"),
        st.Page("pages/8_Registry_Verification.py", title="Verify DWR"),
        st.Page("pages/9_ColdChain_SLA.py", title="Cold Chain SLA"),
        st.Page("pages/10_Audit_Log.py", title="Audit Log"),
    ]
}

pg = st.navigation(pages)
pg.run()
st.stop()
