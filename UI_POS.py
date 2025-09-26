import streamlit as st
import pandas as pd
import datetime
import time
from logic_POS import add_to_order, submit_order, update_order_status, update_payment_status
from db_POS import get_orders_from_db, get_single_order_from_db

# --- Data & Menu ---
MENU = {
    "Lamb Chop": 17.00,
    "Chicken Chop": 6.00,
    "Chicken Grilled": 12.00,
    "Spaghetti Bolognese": 6.00,
    "Spaghetti Carbonara": 6.00,
    "Fries": 4.00,
    "Fish N Chip": 7.00
}

PAYMENT_METHODS = ["Tunai", "DuitNow QR Pay", "TnG Online Transfer"]

def customer_interface(table_number, user_type):
    """Renders the UI for the customer to place an order."""
    is_takeaway_only = user_type == "customer" and not table_number
    
    if is_takeaway_only:
        st.warning("Anda kini membuat pesanan Bawa Pulang.")
        st.info("Sila teruskan dengan pesanan anda.")
    elif not table_number:
        st.warning("Sila imbas kod QR meja anda untuk membuat pesanan.")
        st.info("Anda boleh membuat pesanan bawa pulang dengan meninggalkan ruangan ini.")
    
    st.header("🛒 Pesanan Baru")
    
    col_id, col_option = st.columns(2)
    with col_id:
        if table_number:
            order_id_input = st.text_input("ID Pesanan", value=f"MEJA-{table_number}", disabled=True)
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            order_id_input = st.text_input("ID Pesanan (Bawa Pulang)", value=f"BAWA PULANG-{timestamp}", disabled=False)
    with col_option:
        if is_takeaway_only:
            dine_option = st.selectbox("Pilihan", ["Take-Away"], disabled=True)
        else:
            dine_option = st.selectbox("Pilihan", ["Dine-In", "Take-Away"])

    st.markdown("---")
    
    col_menu, col_order = st.columns([1, 2])
    with col_menu:
        st.subheader("Menu")
        for item, price in MENU.items():
            col_item_name, col_item_qty, col_add_btn = st.columns([2, 1, 1])
            with col_item_name:
                st.write(f"**{item}** (RM{price:.2f})")
            with col_item_qty:
                quantity = st.number_input("Kuantiti", min_value=1, value=1, key=f"qty_{item}_{table_number}", label_visibility="collapsed")
            with col_add_btn:
                if st.button("Tambah", key=f"btn_{item}_{table_number}"):
                    add_to_order(item, price, quantity)
                    
    with col_order:
        st.subheader("Pesanan Semasa")
        if st.session_state.current_order:
            order_df = pd.DataFrame(st.session_state.current_order)
            st.dataframe(order_df[['Item', 'Kuantiti', 'Subtotal']])
            total_price = order_df['Subtotal'].sum()
            st.metric(label="Total", value=f"RM{total_price:.2f}")
            st.markdown("---")
            if st.button("✅ Hantar Pesanan", use_container_width=True):
                submit_order(order_id_input, dine_option)
        else:
            st.info("Pesanan semasa kosong. Sila pilih item dari menu.")
    
    st.markdown("---")
    st.header("Status Pesanan Anda")
    st.info("Status pesanan anda akan dikemas kini di sini.")
    
    if st.button("Kemaskini Status", key="refresh_status"):
        st.session_state.last_status_check = datetime.datetime.now()
        
    if st.session_state.last_status_check is not None:
        with st.spinner("Memuatkan status..."):
            order_details = get_single_order_from_db(order_id_input)
            if order_details:
                status = order_details[3]
                submitted_at = order_details[2]
                st.subheader(f"Status untuk Pesanan: `{order_id_input}`")
                st.markdown(f"**Pilihan:** `{order_details[1]}`")
                st.markdown(f"**Status:** `{status}`")
                elapsed_time = datetime.datetime.now() - submitted_at
                minutes, seconds = divmod(elapsed_time.total_seconds(), 60)
                st.markdown(f"**Masa berlalu:** {int(minutes):02d} minit, {int(seconds):02d} saat")

def employee_interface():
    """Renders the UI for the employee dashboard."""
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
                        elapsed_time = datetime.datetime.now() - order_data['submitted_at'].iloc[0].to_pydatetime()
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
