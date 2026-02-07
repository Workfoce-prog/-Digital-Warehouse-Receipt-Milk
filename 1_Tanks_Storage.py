import streamlit as st
import pandas as pd
from utils import load_csv, save_csv, log_event

st.set_page_config(page_title="Tanks & Cold Storage", layout="wide")
user = st.session_state.user

st.title("Tanks & Cold Storage (Rental / Rent-to-Own)")
tanks = load_csv("tanks.csv")
custodians = load_csv("custodians.csv")

st.subheader("Tanks")
view = tanks.merge(custodians[["custodian_id","name","region","license_status"]], on="custodian_id", how="left")
st.dataframe(view.sort_values(["status","capacity_liters"]), use_container_width=True)

st.markdown("---")
st.subheader("Request tank access (demo)")
if user["role"] not in ["owner","platform"]:
    st.info("Only owners/platform can request tank access in pilot.")
    st.stop()

tank_id = st.selectbox("Tank", tanks["tank_id"].tolist())
model = st.selectbox("Model", ["rental","rent_to_own","pay_per_liter"])
days = st.number_input("Days (rental) / Months (rent-to-own)", min_value=1, value=7)
notes = st.text_input("Notes (optional)")

if st.button("Submit request", type="primary"):
    idx = tanks.index[tanks["tank_id"]==tank_id][0]
    if str(tanks.loc[idx,"status"]) != "available":
        st.error("Tank not available.")
    else:
        tanks.loc[idx,"status"] = "occupied"
        tanks.loc[idx,"ownership_model"] = model
        tanks.loc[idx,"owner_entity_id"] = user["entity_id"]
        save_csv(tanks, "tanks.csv")
        log_event(user["username"], "tank_assigned", "tank", tank_id, {"model": model, "duration": int(days), "notes": notes})
        st.success("Tank assigned (demo). Proceed to Intake & Tests.")
