import streamlit as st
import datetime
import pandas as pd
from db_POS import insert_new_order, update_db_status, update_db_payment

# Base64 encoded WAV file for notification sound
DING_SOUND = "data:audio/wav;base64,UklGRl9QDQBXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQBQGwEBCjELBgwIBgIIGAsGDAoBBiYKGAgDAxELBgwL"

# --- Functions for App Logic ---
def setup_session_state():
    """Initializes session state variables if they don't exist."""
    if "current_order" not in st.session_state:
        st.session_state.current_order = []
    if 'view_state' not in st.session_state:
        st.session_state.view_state = 'menu'
    if 'submitted_order_id' not in st.session_state:
        st.session_state.submitted_order_id = None
    if 'create_new_order' not in st.session_state:
        st.session_state.create_new_order = False
    # New state for complex item configuration
    if 'item_to_configure' not in st.session_state:
        st.session_state.item_to_configure = None

def add_to_order(item, price, quantity, remarks):
    """Adds an item with specified quantity to the current order (in session state)."""
    if quantity <= 0:
        st.warning("Sila masukkan kuantiti yang sah.")
        return
    # Note: price here is the FINAL price per unit (base + add-ons)
    st.session_state.current_order.append(
        {'Item': item, 
         'Kuantiti': quantity, 
         'Harga': price, 
         'Subtotal': price * quantity,
         'Remarks': remarks if remarks else ''
        })
    #st.success(f"{quantity} x {item} ditambah ke dalam pesanan.")
    # Clear configuration state after successful addition
    st.session_state.item_to_configure = None 
    #st.rerun() # Rerun to refresh the menu without configuration UI
    return True

def remove_from_order(index):
    """Removes an item from the current order list by index."""
    if 0 <= index < len(st.session_state.current_order):
        del st.session_state.current_order[index]
        # st.rerun()

def submit_order(order_id, dine_option): 
    """Submits the current order from session state to the database."""
    if not st.session_state.current_order:
        st.error("Ralat: pesanan tidak boleh dibiarkan kosong.")
        return
    
    if insert_new_order(order_id, dine_option, st.session_state.current_order):
        # Clear basket
        st.session_state.current_order = []
        st.audio(DING_SOUND, format="audio/wav", autoplay=True)
        # Force a rerun to switch to the order status view
        st.rerun()

def update_order_status(order_id, new_status):
    """Updates the status of an order in the database."""
    update_db_status(order_id, new_status)
    st.success(f"Status pesanan {order_id} dikemas kini kepada '{new_status}'.")
    st.cache_data.clear()
    st.rerun()

def update_payment_status(order_id, new_payment_method):
    """Updates the payment status and method of an order in the database."""
    update_db_payment(order_id, new_payment_method)
    st.success(f"Pembayaran untuk pesanan {order_id} dikemas kini.")
    st.cache_data.clear()
    st.rerun()