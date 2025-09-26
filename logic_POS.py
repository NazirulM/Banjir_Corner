import streamlit as st
import datetime
import pandas as pd
from db_POS import insert_new_order, update_db_status, update_db_payment

# Base64 encoded WAV file for notification sound
# A short "ding" sound
DING_SOUND = "data:audio/wav;base64,UklGRl9QDQBXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQBQGwEBCjELBgwIBgIIGAsGDAoBBiYKGAgDAxELBgwL"

# --- Functions for App Logic ---
def setup_session_state():
    """Initializes session state variables if they don't exist."""
    if "current_order" not in st.session_state:
        st.session_state.current_order = []
    if 'last_status_check' not in st.session_state:
        st.session_state.last_status_check = None

def add_to_order(item, price, quantity):
    """Adds an item with specified quantity to the current order (in session state)."""
    if quantity <= 0:
        st.warning("Sila masukkan kuantiti yang sah.")
        return
    st.session_state.current_order.append({'Item': item, 'Kuantiti': quantity, 'Harga': price, 'Subtotal': price * quantity})
    st.success(f"{quantity} x {item} ditambah ke dalam pesanan.")

def submit_order(order_id, dine_option):
    """Submits the current order from session state to the database."""
    if not st.session_state.current_order:
        st.error("Ralat: pesanan tidak boleh dibiarkan kosong.")
        return
    if insert_new_order(order_id, dine_option, st.session_state.current_order):
        st.session_state.current_order = []
        st.audio(DING_SOUND, format="audio/wav", autoplay=True)
        st.success(f"Pesanan {order_id} telah berjaya dimasukkan! Sila tunggu, pesanan anda sedang diproses.")
        # Force a rerun to clear the form and reflect the new order status
        st.rerun()

def update_order_status(order_id, new_status):
    """Updates the status of an order in the database."""
    update_db_status(order_id, new_status)
    st.success(f"Status pesanan {order_id} dikemas kini kepada '{new_status}'.")
    st.cache_data.clear() # Clear cache to force a fresh data fetch on rerun
    st.rerun()

def update_payment_status(order_id, new_payment_method):
    """Updates the payment status and method of an order in the database."""
    update_db_payment(order_id, new_payment_method)
    st.success(f"Pembayaran untuk pesanan {order_id} dikemas kini.")
    st.cache_data.clear()
    st.rerun()
