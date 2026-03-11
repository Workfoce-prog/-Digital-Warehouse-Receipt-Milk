import streamlit as st
import pandas as pd
from utils import load_csv, save_csv, log_event
from auth import require_login

# ----------------------------
# Page config MUST be first
# ----------------------------
st.set_page_config(page_title="Tanks & Cold Storage", layout="wide")

# ----------------------------
# Login
# ----------------------------
user = require_login()

st.title("Tanks & Cold Storage (Rental / Rent-to-Own)")

# ----------------------------
# Load data
# ----------------------------
tanks = load_csv("tanks.csv")
custodians = load_csv("custodians.csv")

# ----------------------------
# Sidebar user info + logout
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.write(f"**Role:** {user.get('role', '')}")
st.sidebar.write(f"**Entity:** {user.get('entity_id', '')}")

if st.sidebar.button("Logout"):
    st.session_state.pop("user", None)
    st.rerun()

# ----------------------------
# Tanks view
# ----------------------------
st.subheader("Tanks")

if tanks.empty:
    st.warning("No tanks data found.")
    st.stop()

if not custodians.empty and "custodian_id" in tanks.columns and "custodian_id" in custodians.columns:
    custodian_cols = [c for c in ["custodian_id", "name", "region", "license_status"] if c in custodians.columns]
    view = tanks.merge(custodians[custodian_cols], on="custodian_id", how="left")
else:
    view = tanks.copy()

sort_cols = [c for c in ["status", "capacity_liters"] if c in view.columns]
if sort_cols:
    view = view.sort_values(sort_cols)

st.dataframe(view, use_container_width=True)

# ----------------------------
# Tank request
# ----------------------------
st.markdown("---")
st.subheader("Request tank access (demo)")

if user.get("role") not in ["owner", "platform", "admin"]:
    st.info("Only owners/platform/admin can request tank access in pilot.")
    st.stop()

tank_options = tanks["tank_id"].dropna().astype(str).tolist() if "tank_id" in tanks.columns else []
if not tank_options:
    st.warning("No tank IDs available.")
    st.stop()

tank_id = st.selectbox("Tank", tank_options)
model = st.selectbox("Model", ["rental", "rent_to_own", "pay_per_liter"])
days = st.number_input("Days (rental) / Months (rent-to-own)", min_value=1, value=7)
notes = st.text_input("Notes (optional)")

if st.button("Submit request", type="primary"):
    match_idx = tanks.index[tanks["tank_id"].astype(str) == str(tank_id)].tolist()

    if not match_idx:
        st.error("Selected tank was not found.")
        st.stop()

    idx = match_idx[0]

    current_status = str(tanks.loc[idx, "status"]) if "status" in tanks.columns else ""
    if current_status != "available":
        st.error("Tank not available.")
    else:
        # ensure required columns exist
        for col in ["status", "ownership_model", "owner_entity_id"]:
            if col not in tanks.columns:
                tanks[col] = None

        tanks.loc[idx, "status"] = "occupied"
        tanks.loc[idx, "ownership_model"] = model
        tanks.loc[idx, "owner_entity_id"] = user.get("entity_id", "")

        save_csv(tanks, "tanks.csv")

        log_event(
            user.get("username", "unknown"),
            "tank_assigned",
            "tank",
            tank_id,
            {
                "model": model,
                "duration": int(days),
                "notes": notes,
                "entity_id": user.get("entity_id", "")
            }
        )

        st.success("Tank assigned (demo). Proceed to Intake & Tests.")
