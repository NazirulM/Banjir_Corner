

import streamlit as st
import pandas as pd
import datetime

# --- App Configuration ---
st.set_page_config(
    page_title="Food Stall POS",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session State Management ---
# Initialize session state for orders and history
if "orders" not in st.session_state:
    st.session_state.orders = []
if "order_history" not in st.session_state:
    st.session_state.order_history = pd.DataFrame(columns=['Item', 'Kuantiti', 'Harga', 'Subtotal', 'ID Pesanan', 'Cara Pembayaran', 'Masa', 'Status'])
if "next_order_id" not in st.session_state:
    st.session_state.next_order_id = 1

# --- Data & Menu ---
MENU = {
    "Lamb Chop": 17.00,
    "Chicken Chop": 6.00,
    "Chicken Grilled": 12.00,
    "Spaghetti Bolognese": 6.00,
    "Spaghetti Carbonara": 6.00, # Fix missing comma
    "Fries": 4.00,
    "Fish N Chip": 7.00
}

PAYMENT_METHODS = ["Tunai", "QR Pay", "TnG Online Transfer"]

# --- Functions ---
def add_to_order(item, price, quantity):
    """Adds an item with specified quantity to the current order."""
    if quantity <= 0:
        st.warning("Sila masukkan kuantiti yang sah.")
        return
    st.session_state.orders.append({'Item': item, 'Kuantiti': quantity, 'Harga': price, 'Subtotal': price * quantity})
    st.success(f"{quantity} x {item} ditambah ke dalam pesanan.")

def submit_order(order_id, payment_method):
    """Submits the current order, adds it to history, and clears the current order."""
    if not st.session_state.orders:
        st.error("Ralat: pesanan tidak boleh dibiarkan kosong.")
        return

    # Create a DataFrame for the current order
    current_order_df = pd.DataFrame(st.session_state.orders)
    current_order_df['ID Pesanan'] = order_id
    current_order_df['Cara Pembayaran'] = payment_method
    current_order_df['Masa'] = datetime.datetime.now()
    current_order_df['Status'] = 'Pending'

    # Append the current order to the history DataFrame
    st.session_state.order_history = pd.concat([st.session_state.order_history, current_order_df], ignore_index=True)
    st.session_state.orders = [] # Clear current order
    st.session_state.next_order_id += 1
    st.success(f"Pesanan {order_id} telah berjaya dimasukkan!")

def mark_order_as_finished(order_id):
    """Marks a pending order as finished."""
    idx = st.session_state.order_history[st.session_state.order_history['ID Pesanan'] == order_id].index
    if not idx.empty:
        st.session_state.order_history.loc[idx, 'Status'] = 'Selesai'
        st.success(f"Pesanan {order_id} ditanda sebagai selesai.")

# --- UI Layout ---
st.title("🍔 Food Stall Management App")
st.markdown("---")

# Main page with tabs for Order Management, Order Status, and Reporting
tab1, tab2, tab3 = st.tabs(["🛒 Pengurusan Pesanan", "🗒️ Status Pesanan", "📈 Laporan Jualan"])

with tab1:
    st.header("🛒 Pesanan Baru")
    
    # Order Details Section
    col_id, col_payment = st.columns(2)
    with col_id:
        # Use an auto-incrementing ID for convenience
        order_id_input = st.text_input("ID Pesanan", value=f"ORDER-{st.session_state.next_order_id}", disabled=False)
    with col_payment:
        payment_method = st.selectbox("Cara Pembayaran", PAYMENT_METHODS)

    st.markdown("---")

    col_menu, col_order = st.columns([1, 2])

    with col_menu:
        st.subheader("Item Menu")
        for item, price in MENU.items():
            col_item_name, col_item_qty, col_add_btn = st.columns([2, 1, 1])
            with col_item_name:
                st.write(f"**{item}** (RM{price:.2f})")
            with col_item_qty:
                quantity = st.number_input(
                    "Kuantiti",
                    min_value=1,
                    value=1,
                    key=f"qty_{item}",
                    label_visibility="collapsed"
                )
            with col_add_btn:
                if st.button("Tambah", key=f"btn_{item}"):
                    add_to_order(item, price, quantity)

    with col_order:
        st.subheader("Pesanan Semasa")
        if st.session_state.orders:
            order_df = pd.DataFrame(st.session_state.orders)
            st.dataframe(order_df[['Item', 'Kuantiti', 'Subtotal']])
            
            total_price = order_df['Subtotal'].sum()
            st.metric(label="Total", value=f"RM{total_price:.2f}")

            st.markdown("---")
            col_submit, col_clear = st.columns(2)
            with col_submit:
                if st.button("✅ Hantar Pesanan", use_container_width=True):
                    submit_order(order_id_input, payment_method)
            with col_clear:
                if st.button("🗑️ Kosongkan Pesanan", use_container_width=True):
                    st.session_state.orders = []
                    st.info("Pesanan telah dikosongkan.")
        else:
            st.info("Pesanan semasa kosong. Sila pilih item dari menu.")

with tab2:
    st.header("🗒️ Status Pesanan")
    pending_orders = st.session_state.order_history[st.session_state.order_history['Status'] == 'Pending']
    
    if not pending_orders.empty:
        st.info("Pesanan di bawah masih pending. Tandai sebagai selesai setelah dihidangkan.")
        
        # Group by Order ID to show each unique order
        for order_id in pending_orders['ID Pesanan'].unique():
            order_data = pending_orders[pending_orders['ID Pesanan'] == order_id]
            st.subheader(f"Pesanan: {order_id}")
            st.markdown(f"**Cara Pembayaran:** {order_data['Cara Pembayaran'].iloc[0]}")
            st.dataframe(order_data[['Item', 'Kuantiti', 'Subtotal']])
            total_subtotal = order_data['Subtotal'].sum()
            st.metric(label="Total Pesanan", value=f"RM{total_subtotal:.2f}")
            if st.button(f"Tandai {order_id} sebagai selesai", key=f"finish_btn_{order_id}"):
                mark_order_as_finished(order_id)
            st.markdown("---")
    else:
        st.success("Tidak ada pesanan pending saat ini.")


with tab3:
    st.header("📈 Dashboard Laporan Jualan")
    # We will only report on "Selesai" (Finished) orders
    df = st.session_state.order_history[st.session_state.order_history['Status'] == 'Selesai'].copy()
    
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Masa']).dt.date
        
        # Total Sales over time
        st.subheader("Total Jualan dari Masa ke Masa")
        daily_sales = df.groupby('Date')['Subtotal'].sum().reset_index()
        st.line_chart(daily_sales, x='Date', y='Subtotal')

        # Sales by Item
        st.subheader("Jualan Mengikut Item")
        item_sales = df.groupby('Item')['Subtotal'].sum().reset_index()
        st.bar_chart(item_sales, x='Item', y='Subtotal')

        # Top Selling Items (by quantity)
        st.subheader("Item Paling Laris")
        top_items = df.groupby('Item')['Kuantiti'].sum().sort_values(ascending=False).reset_index()
        top_items.columns = ['Item', 'Kuantiti Terjual']
        st.dataframe(top_items)
        
        # Display raw data for debugging/review
        with st.expander("Lihat Riwayat Pesanan Selesai"):
            st.dataframe(df)

    else:
        st.info("Tidak ada pesanan selesai untuk dilaporkan.")
