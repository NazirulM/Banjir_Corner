import streamlit as st
import pandas as pd
import datetime
import time
from logic_POS import add_to_order, submit_order, update_order_status, update_payment_status, setup_session_state, remove_from_order
from db_POS import get_orders_from_db, get_single_order_from_db
from streamlit import components

# --- Data & Menu (Updated for Configuration) ---
MENU = {
    "makanan": {
        "Mi Bandung": {
            "base_price": 8.00,
            "variants": {
                "label": "Jenis Mi Bandung",
                "type": "radio",
                "options": {"Biasa": 0.00, "Ayam": 2.00, "Daging": 2.00, "Kerang": 2.00, "Special": 5.00}, # Price is the cost ADDED to the base_price
                "required": True,
            },
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Extra Telur": 1.00, "Extra Mi": 1.00, "Extra Protein": 2.00},
                "required": False,
            }
        },
        "Sup": {
            "base_price": 7.00,
            "variants": {
                "label": "Jenis Sup",
                "type": "radio",
                "options": {"Ayam": 2.00, "Daging": 2.00, "tetel": 2.00, "kambing": 2.00, "gearbox": 10.00}, # Price is the cost ADDED to the base_price
                "required": True,
            },
            "addons": {
                "label": "Add-Ons",
                "type": "multiselect",
                "options": {"Bihun": 1.00, "Nasi Putih": 1.00, "Nasi Impit": 1.00, "Mi Kuning": 1.00,
                            "Ayam": 2.00, "Daging": 2.00, "tetel": 2.00, "kambing": 2.00, "gearbox": 10.00},
                "required": False
            }
        },
        "Bakso": {
            "base_price": 6.00,
            "variants": {
                "label": "Jenis Bakso",
                "type": "radio",
                "options": {"Biasa": 0.00, "Ayam": 2.00, "Daging": 2.00, "tetel": 2.00, "kambing": 2.00, "gearbox": 10.00}, # Price is the cost ADDED to the base_price
                "required": True
            },
            "addons": {
                "label": "Add-Ons (Optional)",
                "type": "multiselect",
                "options": {"Sayur": 0.50, "Kentang": 0.50},
                "required": False
            }
        },
        "Chicken Chop": {
            "base_price": 7.00,
            "addons": {
                "label": "Add-Ons",
                "type": "multiselect",
                "options": {"Nasi Putih": 1.00, "Cheese": 1.00},
                "required": False
            }
        },
        "Lamb Chop": {
            "base_price": 17.00,
            "addons": {
                "label": "Add-Ons",
                "type": "multiselect",
                "options": {"Nasi Putih": 1.00},
                "required": False
            }
        },
        "Grilled Chicken Chop": 13.00,
        "French Fries": 5.00,
        "Spaghetti Bolognese": 7.00,
        "Spaghetti Carbonara": 7.00,
    },
    "minuman": {
        "Teh O Ais": 3.00,
        "Sirap Limau": 3.50,
        "Kopi Panas": 2.50,
        "Jus Oren": 4.00,
    }
}



PAYMENT_METHODS = ["Tunai", "DuitNow QR Pay", "TnG Online Transfer"]


# --- General Helper Functions ---

def get_menu_item_details(category, item_name):
    """Safely retrieves the item's configuration dict or base price."""
    item_data = MENU.get(category, {}).get(item_name)
    
    if isinstance(item_data, dict):
        base_price = item_data.get("base_price", 0.00)
        is_configurable = True
    else:
        base_price = item_data
        is_configurable = False
        
    return base_price, is_configurable, item_data

def finalize_configuration(item_data, quantity, key_to_reset, remarks_text):
    """Handles submission, calculates final price, and adds the custom item to order."""
    
    base_item = item_data['name']
    base_price = item_data['base_price']
    
    final_price = base_price
    config_details = []
    
    # 1. Process Variants and Add-ons dynamically
    config_settings = get_menu_item_details(item_data['category'], base_item)[2]

    # Check Requirements and Calculate Price
    required_variant_selected = True
    
    for key, config in config_settings.items():
        if key in ['variants', 'addons']:
            session_key = f"{base_item}_{key}_selection" 
            selection = st.session_state.get(session_key)

            if config.get('required') and not selection:
                required_variant_selected = False
                st.error(f"Sila pilih satu dari {config['label']}.")
                break
            
            if selection:
                if config['type'] == 'radio':
                    # Variant (single selection)
                    final_price += config['options'][selection]
                    config_details.append(selection)
                elif config['type'] == 'multiselect':
                    # Add-ons (multiple selection)
                    for add_on in selection:
                        final_price += config['options'][add_on]
                        config_details.append(add_on)

    if not required_variant_selected:
        return

    # 2. Final Item Name
    customized_item_name = f"{base_item}"
    if config_details:
        customized_item_name += f" ({', '.join(config_details)})"
    
    # 3. Add to Order and Clear State
    # 🚀 CRITICAL: Pass remarks_text to add_to_order 🚀
    add_to_order(customized_item_name, final_price, quantity, remarks_text)
    
    # Clear all configuration-related state keys for the next item
    # Since we are using an open remarks field, we should also clear its state key
    remarks_key = f"{item_data['name']}_remarks"
    if remarks_key in st.session_state:
        del st.session_state[remarks_key]
        
    st.session_state[key_to_reset] = 0
    st.session_state.item_to_configure = None 
    st.rerun()

def calculate_current_cost(item_name, base_price, config_settings):
    """Calculates the current cost based on selections stored in st.session_state."""
    current_cost = base_price

    if config_settings:
        for key, config in config_settings.items():
            if key in ['variants', 'addons']:
                session_key = f"{item_name}_{key}_selection"
                selection = st.session_state.get(session_key)

                if selection:
                    if config['type'] == 'radio':
                        # Variant (single selection)
                        # Selection is the string name, use it to look up the price
                        current_cost += config['options'].get(selection, 0)
                    elif config['type'] == 'multiselect':
                        # Add-ons (multiple selection)
                        for add_on in selection:
                            # Selection is a list of string names
                            current_cost += config['options'].get(add_on, 0)
    return current_cost


def show_item_config(item_data):
    """Renders a reusable, dynamic configuration pop-up for any complex item."""
    
    item_name = item_data['name']
    base_price = item_data['base_price']
    quantity = item_data['quantity']
    key_to_reset = item_data['key_to_reset']
    category = item_data['category']
    
    config_settings = get_menu_item_details(category, item_name)[2]

    remarks_key = f"{item_name}_remarks" 
    
    # CRITICAL FIX: Removed st.form() and replaced it with st.container()
    with st.container(border=True):
        st.subheader(f"Customize your {item_name}")
        
        # --- Dynamically Render Variants and Add-ons ---
        
        if config_settings:
            for key, config in config_settings.items():
                if key in ['variants', 'addons']:
                    st.markdown("---")
                    st.markdown(f"##### **{config['label']}**")
                    
                    price_options = config['options']
                    price_str = ", ".join([f"{opt} (+RM{price:.2f})" for opt, price in price_options.items()])
                    st.caption(f"Pilihan Harga: {price_str}")
                    
                    session_key = f"{item_name}_{key}_selection" 
                    
                    # Ensure selection key is initialized for the first render
                    if session_key not in st.session_state:
                        st.session_state[session_key] = None if config['type'] == 'radio' else []

                    if config['type'] == 'radio' and config.get('required'):
                        # Variants (Required Radio Button)
                        st.radio(
                            config['label'],
                            list(price_options.keys()),
                            index=None,
                            key=session_key,
                            label_visibility="collapsed"
                        )
                        
                    elif config['type'] == 'multiselect':
                        # Add-ons (Optional Multiselect)
                        st.multiselect(
                            config['label'],
                            list(price_options.keys()),
                            key=session_key,
                            # Default is handled by the initial state setup above
                            label_visibility="collapsed"
                        )
        
        # 🚀 START: NEW REMARKS FIELD 🚀
        st.markdown("---")
        st.markdown("##### **Nota Khas/Permintaan (Pilihan)**")
        st.text_area(
            "Sila masukkan permintaan khas anda di sini (e.g., Kurang Pedas, Taknak Sayur)",
            key=remarks_key,
            height=70,
            label_visibility="collapsed"
        )
        # 🚀 END: NEW REMARKS FIELD 🚀
        
        # --- Dynamic Price Estimation (This now reruns with the app state) ---
        
        # Calculation is called here:
        current_cost = calculate_current_cost(item_name, base_price, config_settings)
        
        st.markdown("---")
        st.metric(label="Anggaran Harga per Unit", value=f"RM{current_cost:.2f}")

        # --- Submission Buttons (Now use regular st.button) ---
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            # Check requirements manually before finalizing
            is_valid = True
            for key, config in config_settings.items():
                if key == 'variants' and config.get('required'):
                    session_key = f"{item_name}_{key}_selection" 
                    if not st.session_state.get(session_key):
                        is_valid = False
                        st.error("Sila pilih satu varian yang wajib (Mandatory Variant).")
                        break # Stop checking if mandatory variant is missing
            
            if st.button("✅ Sahkan Pesanan", use_container_width=True, disabled=not is_valid):
                # The finalize function validates and adds the item
                finalize_configuration(item_data, quantity, key_to_reset, remarks_key)
        
        with col_cancel:
            if st.button("❌ Batal Pesanan", type="secondary", use_container_width=True):
                st.session_state[key_to_reset] = 0
                st.session_state.item_to_configure = None
                st.rerun() 

# --- Helper Functions (Remaining functions are unchanged) ---

def quantity_changed(item_name, category, unique_key):
    """
    Handles changes in the st.number_input for an item.
    Either triggers configuration or adds the item directly.
    """
    
    current_qty = st.session_state[unique_key]
    
    # Do nothing if quantity is zero (or reset to zero)
    if current_qty == 0:
        return
        
    base_price, is_configurable, _ = get_menu_item_details(category, item_name)

    if is_configurable:
        # Trigger configuration pop-up for complex items
        st.session_state.item_to_configure = {
            'name': item_name,
            'base_price': base_price,
            'quantity': current_qty,
            'key_to_reset': unique_key,
            'category': category
        }
        # Reset the quantity input so the item doesn't look like it's already added
        st.session_state[unique_key] = 0 
    else:
        # 🚀 CRITICAL FIX: Add simple item directly, passing an empty string for remarks
        if current_qty > 0:
            add_to_order(item_name, base_price, current_qty, "") # Pass "" for remarks
            st.session_state[unique_key] = 0 # Reset input after adding

def get_total_item_quantity(base_item):
    """Calculates the total quantity of a base item (ignoring variations) in the current order."""
    total_qty = 0
    if not st.session_state.current_order:
        return 0
        
    for item in st.session_state.current_order:
        # Check if the item name starts with the base item name (e.g., "Mi Bandung" is the start of "Mi Bandung (Ayam, Telur)")
        if item['Item'].startswith(base_item):
            total_qty += item['Kuantiti']
    return total_qty

def render_menu_category(category_name, menu_items, table_number):
    """Renders the menu for a specific category using the new quantity/config logic."""
    st.subheader(f"{category_name.capitalize()}")
    for item_name in menu_items.keys():
        
        base_price, is_configurable, item_data_config = get_menu_item_details(category_name, item_name)
        
        unique_key = f"qty_{item_name}_{table_number}_{category_name}" 
        
        # Ensure input key is initialized to 0
        if unique_key not in st.session_state:
             st.session_state[unique_key] = 0
             
        # Get the currently ordered quantity for this item
        current_ordered_qty = get_total_item_quantity(item_name)

        col_item_name, col_item_qty_input, col_ordered_qty = st.columns([3, 1, 1]) 
        
        with col_item_name:
            st.write(item_name)
                
        with col_item_qty_input:
            # Min value 0, maintained by session state, and uses the callback
            st.number_input(
                "Kuantiti", 
                min_value=0, 
                key=unique_key, 
                on_change=quantity_changed, 
                args=(item_name, category_name, unique_key), 
                label_visibility="collapsed"
            )
        
        with col_ordered_qty:
            # Display the confirmed, added quantity
            st.markdown(f"<div style='text-align: right; padding-top: 5px;'>**Added: {current_ordered_qty}**</div>", unsafe_allow_html=True)


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
    if 'item_to_configure' in st.session_state:
        del st.session_state.item_to_configure


def display_order_status(order_id_input):
    """Displays the status of the submitted order without elapsed time."""
    st.header("⏳ Status Pesanan Anda")
    
    with st.spinner(f"Memuatkan status pesanan `{order_id_input}`..."):
        time.sleep(1) 
        order_details = get_single_order_from_db(order_id_input) 
        
    if not order_details:
        st.error(f"Pesanan dengan ID `{order_id_input}` tidak ditemui.")
        st.markdown("---")
        if st.button("➡️ Buat Pesanan Baru", use_container_width=True):
            st.session_state.create_new_order = True
            st.rerun()
        return

    status = order_details[3]

    if status == 'Siap Dihidangkan':
         st.success(f"Status: **{status}**! Sila tunggu kakitangan menghidangkan pesanan anda.")
    elif status == 'Dalam Dapur':
         st.warning(f"Status: **{status}**. Pesanan anda baru sahaja dimasukkan.")
    else:
         st.info(f"Status: **{status}**. Pesanan anda sedang disiapkan.")

    st.markdown(f"**ID Pesanan:** `{order_id_input}`")
    st.markdown(f"**Pilihan:** `{order_details[1]}`")
    
    st.markdown("---")
    
    if st.button("➡️ Buat Pesanan Baru", use_container_width=True):
        st.session_state.create_new_order = True
        st.rerun()


# --- Main Interface ---

def customer_interface(table_number, user_type):
    """Renders the UI for the customer to place an order or view status."""
    setup_session_state()
    
    if st.session_state.get('create_new_order', False):
        reset_customer_view_state() 
    
    if st.session_state.get('item_to_configure'):
        show_item_config(st.session_state.item_to_configure)
        return

    # --- Initialization & Status Check (Unchanged) ---
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
    
    if 'view_state' not in st.session_state:
        st.session_state.view_state = 'menu'
    
    if 'menu_category' not in st.session_state:
        st.session_state.menu_category = 'makanan' 
    
    if st.session_state.get('submitted_order_id') and not st.session_state.get('create_new_order', False):
        display_order_status(st.session_state.submitted_order_id)
        return
        
    with st.sidebar:
        pass
            
    # --- MAIN CONTENT: Checkout State (Unchanged) ---
    if st.session_state.view_state == 'checkout' and st.session_state.current_order:
        st.header("🧾 Checkout Pesanan")
        
        st.info(f"ID Pesanan: **`{order_id_input}`**")
        if table_number:
            st.info(f"Nombor Meja: **`{table_number}`**")
            
        st.markdown("---")
        st.markdown("### **Ringkasan Pesanan**")
        
        for index, item_data in enumerate(st.session_state.current_order):
            
            with st.container(border=True): 
                col_item_name, col_item_qty = st.columns([4, 2])
                with col_item_name:
                    st.markdown(f"**{item_data['Item']}**")
                with col_item_qty:
                    st.write(f"Kuantiti: **{item_data['Kuantiti']}**")
                
                col_price, col_cancel = st.columns([4, 2])
                with col_price:
                    st.subheader(f"RM{item_data['Subtotal']:.2f}")
                with col_cancel:
                    if st.button("❌ Batal", key=f"cancel_{index}", use_container_width=True):
                        remove_from_order(index) 

        if st.session_state.current_order:
            order_df = pd.DataFrame(st.session_state.current_order)
            total_price = order_df['Subtotal'].sum()
        else:
            total_price = 0.00
            
        st.markdown("---")
        st.metric(label="Total Perlu Dibayar", value=f"RM{total_price:.2f}")
        st.markdown("---")
        
        with st.form("checkout_form"):
            if is_takeaway_only or dine_option_default == "Take-Away":
                dine_option = st.selectbox("Pilihan (Wajib)", ["Take-Away"], disabled=True)
            elif dine_option_default == "Dine-In":
                dine_option = st.selectbox("Pilihan (Wajib)", ["Dine-In", "Take-Away"], index=0)
            else:
                dine_option = st.selectbox("Pilihan (Wajib)", ["Dine-In", "Take-Away"])
            
            submitted = st.form_submit_button("✅ Hantar Pesanan ke Dapur", use_container_width=True)
            
            if submitted:
                if dine_option:
                    st.session_state.submitted_order_id = order_id_input
                    submit_order(order_id_input, dine_option) 
                else:
                    st.error("Sila pilih pilihan 'Dine-In' atau 'Take-Away'.")

        if st.button("⬅️ Kembali ke Menu", use_container_width=True):
            st.session_state.view_state = 'menu'
            st.rerun()

    elif st.session_state.view_state == 'checkout' and not st.session_state.current_order:
        st.session_state.view_state = 'menu'
        st.rerun()

    # --- MAIN CONTENT: Menu State ---
    else: 
        st.header("🛒 Buat Pesanan Baru")
        
        if is_takeaway_only:
            # st.warning("Anda kini membuat pesanan **Bawa Pulang**.")
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
        
        selected_category = st.session_state.menu_category
        
        render_menu_category(selected_category, MENU[selected_category], table_number)

        # 🚀 START: SIMPLIFIED FOOTER 🚀
        if st.session_state.current_order:
            st.markdown("---")
            
            # Recalculate total for the checkout button help
            order_df = pd.DataFrame(st.session_state.current_order)
            total_price = order_df['Subtotal'].sum()
            
            checkout_label = f"🧾 Checkout Pesanan (RM{total_price:.2f})"

            if st.button(checkout_label, key="main_checkout_btn", type="primary", use_container_width=True):
                st.session_state.view_state = 'checkout'
                st.rerun()

def employee_interface():
    # (employee_interface content remains unchanged)
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