import streamlit as st
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_PATH = os.path.join(DATA_DIR, "users.csv")

os.makedirs(DATA_DIR, exist_ok=True)

def ensure_users():
    if not os.path.exists(USERS_PATH):
        df = pd.DataFrame([
            {"username":"admin","password":"Admin123!","role":"admin","entity_id":"E-PLAT-001"}
        ])
        df.to_csv(USERS_PATH,index=False)

def load_users():
    ensure_users()
    return pd.read_csv(USERS_PATH)

def require_login():

    if "user" in st.session_state:
        return st.session_state.user

    st.title("Platform Login")

    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password",type="password")
        submit = st.form_submit_button("Login")

    if submit:
        users = load_users()

        match = users[
            (users.username == u) &
            (users.password == p)
        ]

        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()


