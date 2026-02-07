import streamlit as st
from utils import load_csv

st.set_page_config(page_title="Audit Log", layout="wide")
st.title("Audit Log (Append-only)")

events = load_csv("events.csv")
if events.empty:
    st.info("No events yet.")
    st.stop()

c1,c2,c3 = st.columns(3)
et = c1.selectbox("Event type", ["All"] + sorted(events["event_type"].dropna().unique().tolist()))
ent = c2.selectbox("Entity type", ["All"] + sorted(events["entity_type"].dropna().unique().tolist()))
search = c3.text_input("Search")

df = events.copy()
if et != "All": df = df[df["event_type"]==et]
if ent != "All": df = df[df["entity_type"]==ent]
if search.strip():
    s = search.strip()
    df = df[df["entity_id"].astype(str).str.contains(s, na=False) | df["details_json"].astype(str).str.contains(s, na=False)]
st.dataframe(df.sort_values("timestamp", ascending=False).head(400), use_container_width=True)
