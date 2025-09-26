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
    # Removed last_status_check as it's no longer needed for automatic status display
    if 'view_state' not in st.session_state:
        st.session_state.view_state = 'menu' # New state: 'menu', 'checkout', or 'status'
    if 'submitted_order_id' not in st.session_state:
        st.session_state.submitted_order_id = None 
    if 'create_new_order' not in st.session_state:
        st.session_state.create_new_order = False

def add_to_order(item, price, quantity):
    """Adds an item with specified quantity to the current order (in session state)."""
    if quantity <= 0:
        st.warning("Sila masukkan kuantiti yang sah.")
        return
    st.session_state.current_order.append({'Item': item, 'Kuantiti': quantity, 'Harga': price, 'Subtotal': price * quantity})
    st.success(f"{quantity} x {item} ditambah ke dalam pesanan.")

def remove_from_order(item_index):
    """Removes an item from the current order based on its index."""
    if 0 <= item_index < len(st.session_state.current_order):
        # Remove the item at the specified index
        del st.session_state.current_order[item_index]
        # Force a rerun to immediately update the visible basket and total
        st.rerun()

def submit_order(order_id, dine_option):
    """Submits the current order from session state to the database."""
    if not st.session_state.current_order:
        st.error("Ralat: pesanan tidak boleh dibiarkan kosong.")
        return
    
    # The view_state is set to the order_id in UI_POS before calling this function
    if insert_new_order(order_id, dine_option, st.session_state.current_order):
        # Clear basket
        st.session_state.current_order = []
        # Set the order ID for the status view and switch view state
        # The submitted_order_id is already set in UI_POS before calling this function
        st.audio(DING_SOUND, format="audio/wav", autoplay=True)
        # Force a rerun to switch to the order status view
        st.rerun()

def close_sidebar_on_mobile():
    """
    Injects reliable JavaScript to simulate a click on the sidebar collapse button, 
    ensuring the sidebar is hidden after selection.
    """
    # This targets the button by its stable ARIA label: 'Collapse'
    js_code = """
    <script>
        try {
            var button = window.parent.document.querySelector('button[aria-label="Collapse"]');
            if (button) {
                button.click();
            }
        } catch (e) {
            // Error handling is necessary for component execution safety
        }
    </script>
    """
    st.components.v1.html(js_code, height=0, width=0)

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
