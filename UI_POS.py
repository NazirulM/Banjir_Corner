import streamlit as st
import pandas as pd
import datetime
import time
# Ensure remove_from_order is imported (as per previous steps)
from logic_POS import add_to_order, submit_order, update_order_status, update_payment_status, setup_session_state, remove_from_order
from db_POS import get_orders_from_db, get_single_order_from_db

# --- Data & Menu ---
MENU = {
    "makanan": {
        "Lamb Chop": 17.00,
        "Chicken Chop": 6.00,
        "Chicken Grilled": 12.00,
        "Spaghetti Bolognese": 6.00,
        "Spaghetti Carbonara": 6.00,
        "Fries": 4.00,
        "Fish N Chip": 7.00
    },
    "minuman": {
        "Teh O Ais": 3.00,
        "Sirap Limau": 3.50,
        "Kopi Panas": 2.50,
        "Jus Oren": 4.00,
    }
}

PAYMENT_METHODS = ["Tunai", "DuitNow QR Pay", "TnG Online Transfer"]

def render_menu_category(category_name, menu_items, table_number):
    """Renders the menu for a specific category."""
    st.subheader(f"{category_name.capitalize()}")
    for item, price in menu_items.items():
        # Use a unique key based on item and table number/category for consistent state
        unique_key = f"qty_{item}_{table_number}_{category_name}" 
        
        col_item_name, col_item_qty, col_add_btn = st.columns([2, 1, 1])
        with col_item_name:
            st.write(f"**{item}** (RM{price:.2f})")
        with col_item_qty:
            quantity = st.number_input("Kuantiti", min_value=1, value=1, key=unique_key, label_visibility="collapsed")
        with col_add_btn:
            if st.button("Tambah", key=f"btn_{item}_{table_number}_{category_name}"):
                add_to_order(item, price, quantity)

def reset_customer_view_state():
    """Function to clear all customer-related session state keys and return to menu."""
    if 'submitted_order_id' in st.session_state:
        del st.session_state.submitted_order_id
    if 'view_state' in st.session_state:
        st.session_state.view_state = 'menu'
    if 'takeaway_order_id' in st.session_state:
        del st.session_state.takeaway_order_id
    if 'create_new_order' in st.session_state:
        del st.session_state.create_new_order

def display_order_status(order_id_input):
    """Displays the status of the submitted order without elapsed time."""
    
    st.header("⏳ Status Pesanan Anda")
    
    # ------------------- Data Fetch and Initial Display -------------------
    with st.spinner(f"Memuatkan status pesanan `{order_id_input}`..."):
        time.sleep(1) # Delay to show spinner, mimicking network fetch
        order_details = get_single_order_from_db(order_id_input) 
        
    if not order_details:
        st.error(f"Pesanan dengan ID `{order_id_input}` tidak ditemui.")
        st.markdown("---")
        # Ensure the new order button is available even if the order isn't found
        if st.button("➡️ Buat Pesanan Baru", use_container_width=True):
            st.session_state.create_new_order = True
            st.rerun()
        return

    # Extract data
    status = order_details[3]

    # ------------------- Status and Info Display -------------------
    if status == 'Siap Dihidangkan':
         st.success(f"Status: **{status}**! Sila tunggu kakitangan menghidangkan pesanan anda.")
    elif status == 'Dalam Dapur':
         st.warning(f"Status: **{status}**. Pesanan anda baru sahaja dimasukkan.")
    else:
         st.info(f"Status: **{status}**. Pesanan anda sedang disiapkan.")

    st.markdown(f"**ID Pesanan:** `{order_id_input}`")
    st.markdown(f"**Pilihan:** `{order_details[1]}`")
    
    st.markdown("---")
    
    # ------------------- New Order Option -------------------
    if st.button("➡️ Buat Pesanan Baru", use_container_width=True):
        st.session_state.create_new_order = True
        st.rerun()

# Note: employee_interface will still have the sidebar for login/navigation.

def customer_interface(table_number, user_type):
    """Renders the UI for the customer to place an order or view status."""
    setup_session_state()
    
    # --- CRITICAL State Pre-check: Check if the user requested a NEW order ---
    if st.session_state.get('create_new_order', False):
        reset_customer_view_state() 
    
    # --- Initialization ---
    is_takeaway_only = user_type == "customer" and not table_number
    if table_number:
        order_id_input = f"MEJA-{table_number}"
        dine_option_default = "Dine-In"
    else:
        if 'takeaway_order_id' not in st.session_state or st.session_state.view_state == 'menu':
             timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
             st.session_state.takeaway_order_id = f"BAWA PULANG-{timestamp}"
             
        order_id_input = st.session_state.takeaway_order_id
        dine_option_default = "Take-Away"
    
    
    # Initialize view_state (menu, checkout, or status)
    if 'view_state' not in st.session_state:
        st.session_state.view_state = 'menu'
    
    # Initialize menu category state
    if 'menu_category' not in st.session_state:
        st.session_state.menu_category = 'makanan' # Default to food
    
    
    # --- ORDER STATUS VIEW CHECK ---
    if st.session_state.get('submitted_order_id') and not st.session_state.get('create_new_order', False):
        display_order_status(st.session_state.submitted_order_id)
        return
        
    
    # --- Sidebar (REMOVED ENTIRELY FOR CUSTOMER VIEW) ---
    # The absence of 'with st.sidebar:' ensures no sidebar is generated.
            
    # --- MAIN CONTENT: Checkout State ---
    if st.session_state.view_state == 'checkout' and st.session_state.current_order:
        st.header("🧾 Checkout Pesanan")
        
        # ... (Checkout content with the Ringkasan Pesanan display) ...
        st.info(f"ID Pesanan: **`{order_id_input}`**")
        if table_number:
            st.info(f"Nombor Meja: **`{table_number}`**")
            
        st.markdown("---")
        st.markdown("### **Ringkasan Pesanan**")
        
        # --- Display Order Items in a Mobile-Friendly Stacked Layout ---
        for index, item_data in enumerate(st.session_state.current_order):
            
            with st.container(border=True): 
                # Row 1: Item Name and Quantity
                col_item_name, col_item_qty = st.columns([4, 2])
                with col_item_name:
                    st.markdown(f"**{item_data['Item']}**")
                with col_item_qty:
                    st.write(f"Kuantiti: **{item_data['Kuantiti']}**")
                
                # Row 2: Subtotal and Cancel Button
                col_price, col_cancel = st.columns([4, 2])
                with col_price:
                    st.subheader(f"RM{item_data['Subtotal']:.2f}")
                with col_cancel:
                    # Button to cancel the item, calling the new function
                    if st.button("❌ Batal", key=f"cancel_{index}", use_container_width=True):
                        remove_from_order(index) 

        # Recalculate total after the potential cancellation loop
        if st.session_state.current_order:
            order_df = pd.DataFrame(st.session_state.current_order)
            total_price = order_df['Subtotal'].sum()
        else:
            total_price = 0.00
            
        st.markdown("---")
        st.metric(label="Total Perlu Dibayar", value=f"RM{total_price:.2f}")
        st.markdown("---")
        
        # --- Form for Submission ---
        with st.form("checkout_form"):
            # Set dine option based on context
            if is_takeaway_only or dine_option_default == "Take-Away":
                dine_option = st.selectbox("Pilihan (Wajib)", ["Take-Away"], disabled=True)
            elif dine_option_default == "Dine-In":
                dine_option = st.selectbox("Pilihan (Wajib)", ["Dine-In", "Take-Away"], index=0)
            else:
                dine_option = st.selectbox("Pilihan (Wajib)", ["Dine-In", "Take-Away"])
            
            # Button to submit order (MUST be st.form_submit_button)
            submitted = st.form_submit_button("✅ Hantar Pesanan ke Dapur", use_container_width=True)
            
            if submitted:
                if dine_option:
                    # Set the order ID for the status view before submitting
                    st.session_state.submitted_order_id = order_id_input
                    # This call will st.rerun() in logic_POS
                    submit_order(order_id_input, dine_option) 
                else:
                    st.error("Sila pilih pilihan 'Dine-In' atau 'Take-Away'.")
        # --- End of Form ---

        # Button to go back to menu (outside the form)
        if st.button("⬅️ Kembali ke Menu", use_container_width=True):
            st.session_state.view_state = 'menu'
            st.rerun()

    # If the basket is now empty after cancellation, redirect to the menu view
    elif st.session_state.view_state == 'checkout' and not st.session_state.current_order:
        st.session_state.view_state = 'menu'
        st.rerun()

    # --- MAIN CONTENT: Menu State ---
    else: # View state is 'menu' or initial load
        st.header("🛒 Buat Pesanan Baru")
        
        # Display Info based on context
        if is_takeaway_only:
            st.warning("Anda kini membuat pesanan **Bawa Pulang**.")
            st.info(f"ID Pesanan: **`{order_id_input}`**")
        elif not table_number:
            st.warning("Sila imbas kod QR meja anda untuk membuat pesanan dine-in.")
            st.info("Anda boleh membuat pesanan bawa pulang.")
        
        st.markdown("---")
        
        # --- CATEGORY NAVIGATION AREA ---
        st.subheader("Pilih Kategori Menu:")
        col_food, col_drink = st.columns(2)
        
        food_style = "primary" if st.session_state.menu_category == 'makanan' else "secondary"
        drink_style = "primary" if st.session_state.menu_category == 'minuman' else "secondary"

        with col_food:
            if st.button("🍽️ Makanan", use_container_width=True, type=food_style):
                st.session_state.menu_category = 'makanan'
                st.rerun() 
        with col_drink:
            if st.button("☕ Minuman", use_container_width=True, type=drink_style):
                st.session_state.menu_category = 'minuman'
                st.rerun() 
                
        st.markdown("---")
        
        # Display the selected menu category
        selected_category = st.session_state.menu_category
        
        # Render the menu items
        render_menu_category(selected_category, MENU[selected_category], table_number)

        # Checkout button (still at the bottom of the main menu)
        if st.session_state.current_order:
            st.markdown("---")
            # Display total price near the checkout button for user awareness
            order_df = pd.DataFrame(st.session_state.current_order)
            total_price = order_df['Subtotal'].sum()
            st.metric(label="Total Pesanan", value=f"RM{total_price:.2f}")

            if st.button("🧾 Checkout Pesanan", key="main_checkout_btn", use_container_width=True):
                st.session_state.view_state = 'checkout'
                st.rerun()

def employee_interface():
    """Renders the UI for the employee dashboard."""
    # ... (Employee interface logic remains unchanged)
    st.sidebar.title("Login Kakitangan")
    password = st.sidebar.text_input("Kata Laluan", type="password")

    if password == "1234":
        st.sidebar.success("Selamat Datang, Kakitangan!")
        tab1, tab2, tab3 = st.tabs(["🗒️ Status Pesanan", "📈 Laporan Jualan", "💳 Pembayaran"])

        # --- Order Status Tab ---
        with tab1:
            st.header("🗒️ Status Pesanan Semasa")
            all_orders = get_orders_from_db()
            pending_orders = all_orders[all_orders['payment_status'] != 'Selesai (Bayar)']
            
            if not pending_orders.empty:
                st.info("Pesanan di bawah masih pending. Tandai sebagai selesai setelah dihidangkan.")
                for order_id in pending_orders['order_id'].unique():
                    order_data = pending_orders[pending_orders['order_id'] == order_id]
                    st.subheader(f"Pesanan: {order_id}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Pilihan:** `{order_data['dine_option'].iloc[0]}`")
                        st.markdown(f"**Status:** `{order_data['status'].iloc[0]}`")
                        
                        # Timezone fix for elapsed time calculation in employee view
                        submitted_at = order_data['submitted_at'].iloc[0].to_pydatetime()
                        if submitted_at.tzinfo is not None and submitted_at.tzinfo.utcoffset(submitted_at) is not None:
                            submitted_at = submitted_at.replace(tzinfo=None)
                            
                        elapsed_time = datetime.datetime.now() - submitted_at
                        minutes, seconds = divmod(elapsed_time.total_seconds(), 60)
                        st.markdown(f"**Masa Berlalu:** {int(minutes):02d} minit, {int(seconds):02d} saat") 

                    with col2:
                        st.markdown(f"**Dihantar Pada:** `{order_data['submitted_at'].iloc[0].strftime('%H:%M:%S')}`")
                    st.dataframe(order_data[['item', 'quantity']])
                    
                    col_buttons = st.columns(3)
                    with col_buttons[0]:
                        if st.button("Dalam Proses", key=f"process_{order_id}"):
                            update_order_status(order_id, "Dalam Proses")
                    with col_buttons[1]:
                        if st.button("Siap Dihidangkan", key=f"ready_{order_id}"):
                            update_order_status(order_id, "Siap Dihidangkan")
                    st.markdown("---")
            else:
                st.success("Tiada pesanan baru buat masa ini!")
        
        # --- Sales Reporting Tab ---
        with tab2:
            st.header("📈 Dashboard Laporan Jualan")
            completed_orders = get_orders_from_db()
            completed_orders = completed_orders[completed_orders['payment_status'] == 'Selesai (Bayar)'].copy()
            if not completed_orders.empty:
                completed_orders['Date'] = pd.to_datetime(completed_orders['submitted_at']).dt.date
                st.subheader("Total Jualan dari Masa ke Masa")
                daily_sales = completed_orders.groupby('Date')['subtotal'].sum().reset_index()
                st.line_chart(daily_sales, x='Date', y='subtotal')
                st.subheader("Jualan Mengikut Item")
                item_sales = completed_orders.groupby('item')['subtotal'].sum().reset_index()
                st.bar_chart(item_sales, x='item', y='subtotal')
                st.subheader("Item Paling Laris")
                top_items = completed_orders.groupby('item')['quantity'].sum().sort_values(ascending=False).reset_index()
                top_items.columns = ['Item', 'Kuantiti Terjual']
                st.dataframe(top_items)
                with st.expander("Lihat Riwayat Pesanan"):
                    st.dataframe(completed_orders.sort_values(by='submitted_at', ascending=False))
            else:
                st.info("Tiada pesanan selesai untuk dilaporkan.")

        # --- Payment Tab ---
        with tab3:
            st.header("💳 Urus Pembayaran")
            unpaid_orders = get_orders_from_db()
            unpaid_orders = unpaid_orders[unpaid_orders['payment_status'] != 'Selesai (Bayar)']
            if not unpaid_orders.empty:
                st.info("Berikut adalah pesanan yang belum dibayar.")
                for order_id in unpaid_orders['order_id'].unique():
                    order_data = unpaid_orders[unpaid_orders['order_id'] == order_id]
                    st.subheader(f"Pesanan: {order_id}")
                    total_price = order_data['subtotal'].sum()
                    st.metric(label="Jumlah Perlu Dibayar", value=f"RM{total_price:.2f}")
                    payment_method = st.selectbox("Kaedah Pembayaran", PAYMENT_METHODS, key=f"pay_select_{order_id}")
                    if st.button(f"Tandai Pesanan Sebagai Selesai (Bayar)", key=f"mark_pay_{order_id}"):
                        update_payment_status(order_id, payment_method)
                    st.markdown("---")
            else:
                st.success("Semua pesanan telah dibayar!")