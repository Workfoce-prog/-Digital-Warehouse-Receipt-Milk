import streamlit as st
from utils import load_csv

def require_login():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        return st.session_state.user

    st.sidebar.subheader("Sign in")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login", type="primary"):
        users = load_csv("users.csv")
        match = users[(users["username"]==username) & (users["password"]==password)]
        if match.empty:
            st.sidebar.error("Invalid credentials")
        else:
            st.session_state.user = match.iloc[0].to_dict()
            st.sidebar.success("Signed in")
            st.rerun()

    st.stop()
