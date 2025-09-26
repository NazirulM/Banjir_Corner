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
    #initial_sidebar_state="expanded",
)

#st.write(st.secrets)

# --- Main App Function ---
def run_app():
    """Main function to run the Streamlit app based on query parameters."""
    # Use the new, stable st.query_params object
    query_params = st.query_params
        
    # Get the 'user' parameter. Use .get() for safe access.
    # If 'user' is not in the URL, it defaults to None. 
    # We then use the OR operator to default to 'customer' if it's None.
    user_type = query_params.get("user") or "customer" 
        
    # Get the 'table' parameter. .get() safely returns the string value or None.
    # No need for [0] as the value is a string, not a list.
    table_number = query_params.get("table")

    # Initialize session state for the current order
    setup_session_state()
        
    st.title("🍔 Banjir Corner")

    st.markdown("---")

    if user_type == "employee":
        employee_interface()
    else:
        # Pass the user_type to the customer interface to handle different UIs
        customer_interface(table_number, user_type)

# --- Initial Instructions & Sidebar ---


run_app()
