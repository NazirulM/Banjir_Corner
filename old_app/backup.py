import streamlit as st
import pandas as pd
import datetime
import psycopg2
import time

# --- App Configuration ---
st.set_page_config(
    page_title="Food Stall POS",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Base64 encoded WAV file for notification sound
# A short "ding" sound
DING_SOUND = "data:audio/wav;base64,UklGRl9QDQBXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQBQGwEBCjELBgwIBgIIGAsGDAoBBiYKGAgDAxELBgwL"

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

# --- Database Functions ---
# Note: For a real app, you would define your SQL table schema here.
# CREATE TABLE IF NOT EXISTS orders (
#     order_id VARCHAR(50) PRIMARY KEY,
#     dine_option VARCHAR(20),
#     submitted_at TIMESTAMP,
#     status VARCHAR(20),
#     payment_status VARCHAR(20),
#     payment_method VARCHAR(50)
# );
#
# CREATE TABLE IF NOT EXISTS order_items (
#     item_id SERIAL PRIMARY KEY,
#     order_id VARCHAR(50) REFERENCES orders(order_id),
#     item VARCHAR(50),
#     quantity INTEGER,
#     price DECIMAL,
#     subtotal DECIMAL
# );

@st.cache_resource
def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    return psycopg2.connect(**st.secrets["connections.postgresql"])

@st.cache_data(ttl=5)
def get_orders_from_db():
    """Fetches all orders and their items from the database and returns a DataFrame."""
    conn = get_db_connection()
    df = pd.DataFrame()
    with conn.cursor() as cur:
        cur.execute("SELECT o.order_id, o.dine_option, o.submitted_at, o.status, o.payment_status, o.payment_method, i.item, i.quantity, i.subtotal FROM orders o JOIN order_items i ON o.order_id = i.order_id ORDER BY o.submitted_at DESC;")
        data = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        df = pd.DataFrame(data, columns=cols)
    conn.close()
    return df

@st.cache_data(ttl=1) # Reduced TTL for single order status check
def get_single_order_from_db(order_id):
    """Fetches a single order's details and items from the database."""
    conn = get_db_connection()
    order_details = None
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM orders WHERE order_id = %s;", (order_id,))
        order_details = cur.fetchone()
    conn.close()
    return order_details

def insert_new_order(order_id, dine_option, items):
    """Inserts a new order and its items into the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM orders WHERE order_id = %s;", (order_id,))
            if cur.fetchone():
                st.error(f"Ralat: ID Pesanan {order_id} sudah wujud.")
                return False
            cur.execute("INSERT INTO orders (order_id, dine_option, submitted_at, status, payment_status, payment_method) VALUES (%s, %s, %s, %s, %s, %s);",
                        (order_id, dine_option, datetime.datetime.now(), 'Dalam Dapur', 'Belum Bayar', 'N/A'))
            for item in items:
                cur.execute("INSERT INTO order_items (order_id, item, quantity, price, subtotal) VALUES (%s, %s, %s, %s, %s);",
                            (order_id, item['Item'], item['Kuantiti'], item['Harga'], item['Subtotal']))
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Ralat pangkalan data: {e}")
        return False
    finally:
        conn.close()
    return True

def update_db_status(order_id, new_status):
    """Updates the status of an order in the database."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET status = %s WHERE order_id = %s;", (new_status, order_id))
    conn.commit()
    conn.close()

def update_db_payment(order_id, payment_method):
    """Updates payment status and method in the database."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET payment_status = %s, payment_method = %s WHERE order_id = %s;", ('Selesai (Bayar)', payment_method, order_id))
    conn.commit()
    conn.close()

# --- Functions for App Logic ---
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
        st.experimental_rerun()

def update_order_status(order_id, new_status):
    """Updates the status of an order in the database."""
    update_db_status(order_id, new_status)
    st.success(f"Status pesanan {order_id} dikemas kini kepada '{new_status}'.")
    st.cache_data.clear() # Clear cache to force a fresh data fetch on rerun
    st.experimental_rerun()

def update_payment_status(order_id, new_payment_method):
    """Updates the payment status and method of an order in the database."""
    update_db_payment(order_id, new_payment_method)
    st.success(f"Pembayaran untuk pesanan {order_id} dikemas kini.")
    st.cache_data.clear()
    st.experimental_rerun()

# --- UI Components ---
def customer_interface(table_number):
    """Renders the UI for the customer to place an order."""
    if not table_number:
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
    
    st.button("Kemaskini Status", key="refresh_status")
    
    if 'last_status_check' not in st.session_state:
        st.session_state.last_status_check = None

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

# --- Main app function ---
def run_app():
    """Main function to run the Streamlit app based on query parameters."""
    query_params = st.experimental_get_query_params()
    user_type = query_params.get("user", ["customer"])[0]
    table_number = query_params.get("table", [None])[0]

    if "current_order" not in st.session_state:
        st.session_state.current_order = []
        
    st.title("🍔 Aplikasi Pengurusan Gerai Makanan")
    st.markdown("---")

    if user_type == "employee":
        employee_interface()
    else:
        customer_interface(table_number)

# --- Initial Instructions ---
st.sidebar.markdown("---")
st.sidebar.subheader("Cara Penggunaan")
st.sidebar.info("Untuk memulakan, **jalankan aplikasi ini** dan: \n\n"
              "1. **Antaramuka Pelanggan:** Akses aplikasi dengan menambahkan `?table=X` di URL (contoh: `http://localhost:8501/?table=1`) atau biarkan ia untuk pesanan 'Bawa Pulang'. \n\n"
              "2. **Antaramuka Kakitangan:** Akses aplikasi dengan menambahkan `?user=employee` di URL (contoh: `http://localhost:8501/?user=employee`) dan masukkan kata laluan demo '1234'.")

run_app()
