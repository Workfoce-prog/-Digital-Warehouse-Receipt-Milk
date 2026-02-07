import streamlit as st
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

def require_login():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        return st.session_state.user

    st.title("Login — Mali Dairy DWR Platform")
    st.caption("Use demo credentials to access the pilot workflow.")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        users = load_csv("users.csv")
        match = users[(users["username"] == username) & (users["password"] == password)]
        if match.empty:
            st.error("Invalid credentials")
        else:
            st.session_state.user = match.iloc[0].to_dict()
            st.success("Signed in")
            st.rerun()

    st.info("Demo password for all users: Admin123!")
    st.stop()

