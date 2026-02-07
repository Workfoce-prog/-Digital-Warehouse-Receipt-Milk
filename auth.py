import streamlit as st
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_PATH = DATA_DIR / "users.csv"

REQUIRED_COLS = ["username", "password", "role", "entity_id"]

DEMO_USERS = pd.DataFrame(
    [
        ["platform_admin", "Admin123!", "platform", "E-PLAT-001"],
        ["women_group", "Admin123!", "owner", "E-WG-001"],
        ["woman_processor", "Admin123!", "owner", "E-WI-001"],
        ["private_dairy", "Admin123!", "owner", "E-COMP-001"],
        ["custodian_mcc", "Admin123!", "custodian", "C-MCC-001"],
        ["bank_demo", "Admin123!", "bank", "BANK-001"],
        ["buyer_demo", "Admin123!", "buyer", "E-BUY-001"],
        ["government", "Admin123!", "government", "GOV-REG-001"],
    ],
    columns=REQUIRED_COLS,
)

def _load_users() -> pd.DataFrame:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not USERS_PATH.exists():
        DEMO_USERS.to_csv(USERS_PATH, index=False)
        return DEMO_USERS.copy()

    try:
        df = pd.read_csv(USERS_PATH)
    except Exception:
        DEMO_USERS.to_csv(USERS_PATH, index=False)
        return DEMO_USERS.copy()

    # Validate required columns
    if df.empty or any(c not in df.columns for c in REQUIRED_COLS):
        DEMO_USERS.to_csv(USERS_PATH, index=False)
        return DEMO_USERS.copy()

    # Keep only required columns (avoid surprises)
    return df[REQUIRED_COLS].copy()

def require_login():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        return st.session_state.user

    st.title("Login — Mali Dairy DWR Platform")
    st.caption("Use demo credentials to access the pilot workflow.")

    users = _load_users()

    username = st.text_input("Username", value="")
    password = st.text_input("Password", type="password", value="")

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


