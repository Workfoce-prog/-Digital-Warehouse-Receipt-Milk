import os
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_PATH = os.path.join(BASE_DIR, "users.csv")

def ensure_users_file():
    if not os.path.exists(USERS_PATH):
        default_users = pd.DataFrame([
            {
                "username": "admin",
                "password": "Admin123!",
                "role": "admin",
                "entity_id": "E-PLAT-001",
                "name": "Platform Admin"
            }
        ])
        default_users.to_csv(USERS_PATH, index=False)

def load_users():
    ensure_users_file()
    return pd.read_csv(USERS_PATH)

def require_login():
    if "user" in st.session_state and st.session_state.user is not None:
        return st.session_state.user

    ensure_users_file()

    st.title("Login")
    st.caption("Mali Dairy Digital Warehouse Receipt Platform")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        try:
            users = load_users()
        except Exception as e:
            st.error(f"Login system error: {e}")
            st.stop()

        required_cols = {"username", "password", "role", "entity_id"}
        missing = required_cols - set(users.columns)
        if missing:
            st.error(f"Users file is missing required columns: {sorted(missing)}")
            st.stop()

        users["username"] = users["username"].astype(str).str.strip()
        users["password"] = users["password"].astype(str).str.strip()

        match = users[
            (users["username"] == str(username).strip()) &
            (users["password"] == str(password).strip())
        ]

        if not match.empty:
            user = match.iloc[0].to_dict()
            st.session_state.user = user
            st.success(f"Welcome, {user.get('name', user['username'])}")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.info("Demo login: admin / Admin123!")
    st.stop()
