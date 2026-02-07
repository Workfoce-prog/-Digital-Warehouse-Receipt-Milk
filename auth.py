import streamlit as st
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_PATH = DATA_DIR / "users.csv"
REQUIRED_COLS = ["username", "password", "role", "entity_id"]

def load_users() -> pd.DataFrame:
    if not USERS_PATH.exists():
        raise FileNotFoundError(f"Missing users file at: {USERS_PATH}")

    # Force correct parsing
    df = pd.read_csv(USERS_PATH, sep=",", header=0, engine="python")

    # If someone saved it with header=None previously, first row becomes data
    # Example: columns = [0,1,2,3] and first row contains 'username'
    if list(df.columns) != REQUIRED_COLS:
        # Try reading without header then promote first row to header if it matches
        df2 = pd.read_csv(USERS_PATH, sep=",", header=None, engine="python")
        first_row = df2.iloc[0].astype(str).str.strip().tolist()
        if first_row == REQUIRED_COLS:
            df2 = df2.iloc[1:].copy()
            df2.columns = REQUIRED_COLS
            df = df2
        else:
            raise ValueError(
                f"users.csv headers not recognized.\n"
                f"Read columns: {list(df.columns)}\n"
                f"First row (if headerless): {first_row}\n"
                f"Expected: {REQUIRED_COLS}\n"
                f"File: {USERS_PATH}"
            )

    return df

def require_login():
    if "user" not in st.session_state:
        st.session_state.user = None
    if st.session_state.user:
        return st.session_state.user

    st.title("Login — Mali Dairy DWR Platform")

    try:
        users = load_users()
    except Exception as e:
        st.error(f"Login system error: {e}")
        st.stop()

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        match = users[(users["username"] == username) & (users["password"] == password)]
        if match.empty:
            st.error("Invalid credentials")
        else:
            st.session_state.user = match.iloc[0].to_dict()
            st.success("Signed in")
            st.rerun()

    st.info("Demo password for all users: Admin123!")
    st.stop()



