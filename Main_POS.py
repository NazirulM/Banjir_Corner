import streamlit as st
import pandas as pd
import datetime
from UI_POS import customer_interface, employee_interface
from logic_POS import setup_session_state
import psycopg2
import toml
import os
import sys

# --- App Configuration ---
st.set_page_config(
    page_title="Food Stall POS",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

#st.write(st.secrets)

# --- Main App Function ---
def run_app():
    """Main function to run the Streamlit app based on query parameters."""
    query_params = st.experimental_get_query_params()
    user_type = query_params.get("user", ["customer"])[0]
    table_number = query_params.get("table", [None])[0]

    # Initialize session state for the current order
    setup_session_state()
        
    st.title("🍔 Aplikasi Pengurusan Gerai Makanan")
    st.markdown("---")

    if user_type == "employee":
        employee_interface()
    else:
        # Pass the user_type to the customer interface to handle different UIs
        customer_interface(table_number, user_type)

# --- Initial Instructions & Sidebar ---


run_app()
